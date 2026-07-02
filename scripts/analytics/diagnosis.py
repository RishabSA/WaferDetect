import argparse
import json
import os
from pathlib import Path
import numpy as np
import yaml
from PIL import Image
from ultralytics import YOLO

from scripts.analytics.diegrid import default_die_mm, wafer_summary
from scripts.analytics.economics import decompose, points_in_polygon
from scripts.analytics.kinematics import scratch_verdict
from scripts.analytics.yieldmodels import (
    estimate_alpha,
    estimate_defect_density,
    quadrat_counts,
)
from scripts.baselines.classical import dot_coordinates
from scripts.datagen.generator import wafer_frac
from scripts.datagen.labels import image_to_wafer
from scripts.perception.annotations import load_class_names, load_label_file

classes_file = Path("data/raw/classes.txt")
kb_path = Path("scripts/analytics/knowledge_base.yaml")
out_root = Path("runs/analytics")

scratch_classes = ("scratch", "edge_scratch")
min_kinematics_dots = 5


def load_knowledge_base(path: Path) -> dict:
    with open(path) as file:
        return yaml.safe_load(file)


def polygon_area(polygon: list) -> float:
    xs = np.array([point[0] for point in polygon])
    ys = np.array([point[1] for point in polygon])
    return float(0.5 * abs(np.dot(xs, np.roll(ys, 1)) - np.dot(ys, np.roll(xs, 1))))


def polygon_centroid_radius(polygon: list) -> float:
    wafer = image_to_wafer(polygon, wafer_frac)
    xs = [point[0] for point in wafer]
    ys = [point[1] for point in wafer]
    return float(np.hypot(sum(xs) / len(xs), sum(ys) / len(ys)))


def diagnose(
    dots: np.ndarray,
    detections: list[tuple[str, float, list]],
    kb: dict,
    die_mm: float = default_die_mm,
    die_value: float = 25.0,
) -> dict:
    economics = decompose(
        dots, [polygon for _, _, polygon in detections], die_mm, die_value
    )

    entries = []
    for (name, confidence, polygon), region in zip(
        detections, economics["regions"], strict=True
    ):
        entry = {
            "class": name,
            "confidence": confidence,
            "geometry": {
                "area_frac": polygon_area(polygon),
                "centroid_r": polygon_centroid_radius(polygon),
            },
            "yield_loss": region,
            "diagnosis": kb[name],
        }

        if name in scratch_classes:
            # Dots trace the physical scratch; polygon vertices carry no curvature.
            inside = dots[points_in_polygon(dots, polygon)]
            if len(inside) >= min_kinematics_dots:
                entry["kinematics"] = scratch_verdict(inside)

        entries.append(entry)

    summary = wafer_summary(dots, die_mm)
    failed_fraction = 1 - summary["yield"]
    summary["d0_per_mm2"] = (
        estimate_defect_density(failed_fraction, die_mm**2)
        if failed_fraction < 1
        else None
    )
    summary["alpha"] = estimate_alpha(quadrat_counts(dots)) if len(dots) else None
    summary["yield_random"] = economics["yield_random"]
    summary["total_loss_dollars"] = sum(
        region["dollars"] for region in economics["regions"]
    )

    return {"detections": entries, "wafer_summary": summary}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--image", type=str, required=True, help="Wafer image path (required)."
    )
    parser.add_argument(
        "--labels",
        type=str,
        default="",
        help="Ground-truth label txt to diagnose (default: unset).",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default="",
        help="Trained weights to detect with (default: unset).",
    )
    parser.add_argument(
        "--die-mm",
        type=float,
        default=default_die_mm,
        help="Die edge length in mm (default: 6.0).",
    )
    parser.add_argument(
        "--die-value",
        type=float,
        default=25.0,
        help="Dollar value per die (default: 25.0).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=str(out_root),
        help="Report output directory (default: runs/analytics).",
    )

    args = parser.parse_args()
    if bool(args.labels) == bool(args.model_path):
        parser.error("Provide exactly one of --labels or --model-path")

    names = load_class_names(classes_file)
    image_path = Path(args.image)
    image = np.asarray(Image.open(image_path).convert("L"))
    dots = dot_coordinates(image)

    if args.labels:
        instances = load_label_file(Path(args.labels))
        detections = [
            (names[instance.class_id], 1.0, instance.polygon) for instance in instances
        ]
    else:
        result = YOLO(args.model_path).predict(str(image_path), verbose=False)[0]
        detections = [
            (
                names[int(class_id)],
                float(confidence),
                [tuple(point) for point in segment],
            )
            for class_id, confidence, segment in zip(
                result.boxes.cls, result.boxes.conf, result.masks.xyn, strict=True
            )
        ]

    report = diagnose(
        dots, detections, load_knowledge_base(kb_path), args.die_mm, args.die_value
    )

    os.makedirs(args.out_dir, exist_ok=True)
    out_path = Path(args.out_dir) / f"{image_path.stem}.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"Total attributed loss: ${report['wafer_summary']['total_loss_dollars']:.0f}"
    )
    print(f"Wrote {out_path}")
