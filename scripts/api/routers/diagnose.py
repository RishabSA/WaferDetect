from pathlib import Path
import numpy as np
from fastapi import APIRouter, HTTPException
from PIL import Image

from scripts.analytics.diagnosis import diagnose, kb_path, load_knowledge_base
from scripts.baselines.classical import dot_coordinates
from scripts.perception.annotations import load_class_names, load_label_file

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


@router.get("/api/diagnose/{stem}")
def diagnose_wafer(stem: str, die_mm: float = 6.0, die_value: float = 25.0) -> dict:
    dots, detections = wafer_dots_and_detections(stem)
    return diagnose(dots, detections, load_knowledge_base(kb_path), die_mm, die_value)
