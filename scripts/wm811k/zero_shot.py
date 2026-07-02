import argparse
import json
import os
from pathlib import Path
import numpy as np
from sklearn.metrics import classification_report, f1_score

from scripts.perception.annotations import load_class_names
from scripts.wm811k.convert import wm811k_class_map

classes_file = Path("data/raw/classes.txt")
out_root = Path("runs/wm811k")

defect_classes = tuple(sorted(set(wm811k_class_map.values()) - {"none"}))
sweep_thresholds = np.arange(0.05, 0.65, 0.05)
predict_floor = 0.01


def reduce_detections(
    class_ids: list[int],
    confidences: list[float],
    class_names: list[str],
    threshold: float,
) -> str:
    label = "none"
    best = threshold

    for class_id, confidence in zip(class_ids, confidences, strict=True):
        if confidence >= best:
            best = confidence
            name = class_names[int(class_id)]
            label = name if name in defect_classes else "other"

    return label


def predict_directory(model, images_dir: Path, batch_size: int = 64) -> dict:
    from tqdm import tqdm

    paths = sorted(images_dir.glob("*.jpg"))
    predictions = {}

    for start in tqdm(range(0, len(paths), batch_size), desc="predicting"):
        batch = paths[start : start + batch_size]
        results = model.predict(
            [str(path) for path in batch], conf=predict_floor, verbose=False
        )

        for path, result in zip(batch, results, strict=True):
            pairs = [
                (int(class_id), float(confidence))
                for class_id, confidence in zip(
                    result.boxes.cls, result.boxes.conf, strict=True
                )
            ]
            predictions[path.stem] = pairs

    return predictions


def load_or_predict(model, images_dir: Path, cache_path: Path) -> dict:
    if cache_path.exists():
        return {
            stem: [(int(class_id), float(confidence)) for class_id, confidence in pairs]
            for stem, pairs in json.loads(cache_path.read_text()).items()
        }

    predictions = predict_directory(model, images_dir)
    cache_path.write_text(json.dumps(predictions))
    return predictions


def labels_at_threshold(
    predictions: dict, class_names: list[str], threshold: float
) -> dict:
    return {
        stem: reduce_detections(
            [class_id for class_id, _ in pairs],
            [confidence for _, confidence in pairs],
            class_names,
            threshold,
        )
        for stem, pairs in predictions.items()
    }


def choose_threshold(
    predictions: dict, truths: dict[str, str], class_names: list[str]
) -> tuple[float, float]:
    best_threshold = 0.0
    best_f1 = -1.0

    for threshold in sweep_thresholds:
        predicted = labels_at_threshold(predictions, class_names, float(threshold))
        stems = sorted(truths)
        f1 = f1_score(
            [truths[stem] for stem in stems],
            [predicted[stem] for stem in stems],
            labels=list(defect_classes),
            average="macro",
            zero_division=0,
        )
        if f1 > best_f1:
            best_threshold = float(threshold)
            best_f1 = float(f1)

    return best_threshold, best_f1


def score(
    predictions: dict, truths: dict[str, str], class_names: list[str], threshold: float
) -> dict:
    predicted = labels_at_threshold(predictions, class_names, threshold)
    stems = sorted(truths)
    true_list = [truths[stem] for stem in stems]
    predicted_list = [predicted[stem] for stem in stems]

    none_stems = [stem for stem in stems if truths[stem] == "none"]
    none_fpr = (
        sum(1 for stem in none_stems if predicted[stem] != "none") / len(none_stems)
        if none_stems
        else 0.0
    )

    confusion = {}
    for truth, prediction in zip(true_list, predicted_list, strict=True):
        confusion.setdefault(truth, {})
        confusion[truth][prediction] = confusion[truth].get(prediction, 0) + 1

    return {
        "threshold": threshold,
        "macro_f1_defects": float(
            f1_score(
                true_list,
                predicted_list,
                labels=list(defect_classes),
                average="macro",
                zero_division=0,
            )
        ),
        "none_fpr": none_fpr,
        "per_class": classification_report(
            true_list, predicted_list, output_dict=True, zero_division=0
        ),
        "confusion": confusion,
    }


def truths_from_directory(images_dir: Path) -> dict:
    return {
        path.stem: path.stem.split("_", 1)[1]
        for path in sorted(images_dir.glob("*.jpg"))
    }


def render_report(metrics: dict, calibration_f1: float) -> str:
    lines = [
        "# WM-811K zero-shot report",
        "",
        f"- threshold: {metrics['threshold']:.2f}",
        f"- calibration defect macro-F1: {calibration_f1:.4f}",
        f"- eval defect macro-F1: {metrics['macro_f1_defects']:.4f}",
        f"- none false-positive rate: {metrics['none_fpr']:.4f}",
        "",
        "## Confusion",
        "",
    ]

    for truth, row in sorted(metrics["confusion"].items()):
        entries = ", ".join(
            f"{prediction}: {count}" for prediction, count in sorted(row.items())
        )
        lines.append(f"- {truth}: {entries}")

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    from ultralytics import YOLO

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Trained *.pt weights (required).",
    )
    parser.add_argument(
        "--calibration-dir",
        type=str,
        default="data/wm811k/images/calibration",
        help="Rendered calibration images (default: data/wm811k/images/calibration).",
    )
    parser.add_argument(
        "--eval-dir",
        type=str,
        default="data/wm811k/images/eval",
        help="Rendered eval images (default: data/wm811k/images/eval).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=str(out_root / "zero_shot"),
        help="Output directory (default: runs/wm811k/zero_shot).",
    )

    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    class_names = load_class_names(classes_file)
    model = YOLO(args.model_path)

    calibration_dir = Path(args.calibration_dir)
    calibration_predictions = load_or_predict(
        model, calibration_dir, out_dir / "predictions_calibration.json"
    )
    threshold, calibration_f1 = choose_threshold(
        calibration_predictions, truths_from_directory(calibration_dir), class_names
    )
    print(
        f"Calibrated threshold: {threshold:.2f} "
        f"(calibration macro-F1 {calibration_f1:.4f})"
    )

    eval_dir = Path(args.eval_dir)
    eval_predictions = load_or_predict(
        model, eval_dir, out_dir / "predictions_eval.json"
    )
    metrics = score(
        eval_predictions, truths_from_directory(eval_dir), class_names, threshold
    )

    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (out_dir / "report.md").write_text(render_report(metrics, calibration_f1))
    print(f"Zero-shot defect macro-F1: {metrics['macro_f1_defects']:.4f}")
    print(f"None false-positive rate: {metrics['none_fpr']:.4f}")
    print(f"Wrote {out_dir / 'metrics.json'}")
    print(f"Wrote {out_dir / 'report.md'}")
