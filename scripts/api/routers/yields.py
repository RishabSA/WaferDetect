from pathlib import Path
from PIL import Image
import numpy as np
from fastapi import APIRouter, HTTPException

from scripts.analytics.diagnosis import kb_path, load_knowledge_base
from scripts.analytics.diegrid import radial_yield, wafer_summary, zone_yields
from scripts.analytics.economics import decompose, pareto
from scripts.analytics.yieldmodels import (
    estimate_alpha,
    estimate_defect_density,
    quadrat_counts,
)
from scripts.baselines.classical import dot_coordinates
from scripts.perception.annotations import load_class_names, load_label_file
from scripts.perception.dataset import read_manifests

router = APIRouter()

classes_file = Path("data/raw/classes.txt")
raw_images_dir = Path("data/raw/images")
raw_labels_dir = Path("data/raw/labels")


def wafer_dots_and_detections(stem: str) -> tuple:
    image_path = raw_images_dir / f"{stem}.jpg"
    if not image_path.is_file():
        raise HTTPException(404, f"unknown wafer stem: {stem}")

    image = np.asarray(Image.open(image_path).convert("L"))
    names = load_class_names(classes_file)
    instances = load_label_file(raw_labels_dir / f"{stem}.txt")
    detections = [
        (names[instance.class_id], 1.0, instance.polygon) for instance in instances
    ]

    return dot_coordinates(image), detections


@router.get("/api/yield/wafer/{stem}")
def yield_wafer(
    stem: str,
    die_mm: float = 6.0,
    die_value: float = 25.0,
    wafer_radius_mm: float = 150.0,
) -> dict:
    dots, detections = wafer_dots_and_detections(stem)
    polygons = [polygon for _, _, polygon in detections]
    economics = decompose(dots, polygons, die_mm, die_value, wafer_radius_mm)

    summary = wafer_summary(dots, die_mm, wafer_radius_mm)
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

    return {
        "summary": summary,
        "radial": radial_yield(dots, die_mm, wafer_radius_mm=wafer_radius_mm),
        "zones": zone_yields(dots, die_mm, wafer_radius_mm),
        "regions": economics["regions"],
    }


@router.get("/api/yield/pareto")
def yield_pareto(split: str = "test", limit: int = 0, die_value: float = 25.0) -> dict:
    kb = load_knowledge_base(kb_path)
    stems = sorted(read_manifests()[split])

    if limit:
        stems = stems[:limit]

    losses = []
    for stem in stems:
        dots, detections = wafer_dots_and_detections(stem)
        regions = decompose(
            dots, [polygon for _, _, polygon in detections], die_value=die_value
        )["regions"]

        for (name, _, _), region in zip(detections, regions, strict=True):
            losses.append((kb[name]["process_steps"][0], region["dollars"]))

    return {"wafers": len(stems), "pareto": pareto(losses)}
