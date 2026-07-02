import argparse
import json
import os
from pathlib import Path
import yaml
from ultralytics import YOLO

from waferdetect.perception.annotations import load_class_names

classes_file = Path("data/raw/classes.txt")
yolo_dir = Path("data/yolo")
runs_dir = Path("runs")

combo_token = "_combo_"
tiny_token = "_edge_scratch_tiny"


def subset_image_list(images_dir: Path, token: str) -> list[Path]:
    return sorted(path for path in images_dir.glob("*.jpg") if token in path.name)


def write_subset_yaml(
    base_yaml: Path, subset_name: str, image_paths: list[Path], out_dir: Path
) -> Path:
    with open(base_yaml, "r") as file:
        base = yaml.safe_load(file)

    os.makedirs(out_dir, exist_ok=True)
    list_file = out_dir / f"{subset_name}.txt"
    list_file.write_text("\n".join(str(path.resolve()) for path in image_paths) + "\n")

    subset = {
        "path": base["path"],
        "train": str(list_file.resolve()),
        "val": str(list_file.resolve()),
        "names": base["names"],
    }
    yaml_path = out_dir / f"{subset_name}.yaml"

    with open(yaml_path, "w") as file:
        yaml.safe_dump(subset, file, sort_keys=False)

    return yaml_path


def metrics_to_dict(metrics: object, class_names: list[str]) -> dict[str, object]:
    per_class = {}

    for position, class_index in enumerate(metrics.box.ap_class_index):
        name = class_names[int(class_index)]
        per_class[name] = {
            "box_ap50": float(metrics.box.ap50[position]),
            "box_ap": float(metrics.box.ap[position]),
            "mask_ap50": float(metrics.seg.ap50[position]),
            "mask_ap": float(metrics.seg.ap[position]),
        }

    return {
        "box_map50": float(metrics.box.map50),
        "box_map50_95": float(metrics.box.map),
        "mask_map50": float(metrics.seg.map50),
        "mask_map50_95": float(metrics.seg.map),
        "per_class": per_class,
    }


def render_report(results: dict[str, dict[str, object]]) -> str:
    lines = ["# WaferDetect evaluation report", ""]

    for section, metrics in results.items():
        lines.append(f"## {section}")
        lines.append("")
        lines.append(
            f"- box mAP50: {metrics['box_map50']:.4f} | box mAP50-95: {metrics['box_map50_95']:.4f}"
        )
        lines.append(
            f"- mask mAP50: {metrics['mask_map50']:.4f} | mask mAP50-95: {metrics['mask_map50_95']:.4f}"
        )

        per_class = metrics["per_class"]
        if per_class:
            lines.append("")
            lines.append(
                "| class | box AP50 | mask AP50 | box AP50-95 | mask AP50-95 |"
            )
            lines.append("|---|---|---|---|---|")
            for name, row in per_class.items():
                lines.append(
                    f"| {name} | {row['box_ap50']:.3f} | {row['mask_ap50']:.3f}"
                    f" | {row['box_ap']:.3f} | {row['mask_ap']:.3f} |"
                )

        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model-path",
        type=str,
        default="runs/train/stage1_baseline/weights/best.pt",
        help="Fine-tuned YOLO segmentation model path *.pt to load (default: runs/train/stage1_baseline/weights/best.pt).",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="stage1_baseline",
        help="Name to use for YOLO training (default: stage1_baseline).",
    )
    parser.add_argument(
        "--data",
        type=str,
        default=str(yolo_dir / "data.yaml"),
        help="(default: data/yolo/data.yaml).",
    )

    args = parser.parse_args()

    class_names = load_class_names(classes_file)
    out_dir = runs_dir / "eval" / args.name
    os.makedirs(out_dir, exist_ok=True)
    model = YOLO(args.model_path)

    results = {}

    full_test = model.val(
        data=args.data,
        split="test",
        plots=True,
        project=str(out_dir),
        name="full_test",
    )

    results["full_test"] = metrics_to_dict(full_test, class_names)
    test_images_dir = yolo_dir / "images" / "test"

    for subset_name, token in (
        ("combo", combo_token),
        ("edge_scratch_tiny", tiny_token),
    ):
        subset_yaml = write_subset_yaml(
            Path(args.data),
            subset_name,
            subset_image_list(test_images_dir, token),
            out_dir / "subsets",
        )
        metrics = model.val(
            data=str(subset_yaml),
            split="val",
            plots=False,
            project=str(out_dir),
            name=subset_name,
        )
        results[subset_name] = metrics_to_dict(metrics, class_names)

    (out_dir / "metrics.json").write_text(json.dumps(results, indent=2) + "\n")
    (out_dir / "report.md").write_text(render_report(results))

    print(f"Wrote {out_dir / 'metrics.json'}")
    print(f"Wrote {out_dir / 'report.md'}")
