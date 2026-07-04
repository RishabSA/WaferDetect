import hashlib
import io
from collections import OrderedDict
from pathlib import Path
from PIL import Image
import numpy as np
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from skimage.transform import radon
from ultralytics import YOLO

from scripts.analytics.diagnosis import diagnose, kb_path, load_knowledge_base
from scripts.analytics.diegrid import radial_yield, zone_yields
from scripts.api.plots import image_png, sinogram_png
from scripts.baselines.classical import dot_coordinates
from scripts.datagen.generator import wafer_frac
from scripts.perception.annotations import load_class_names, load_label_file

router = APIRouter()

classes_file = Path("data/raw/classes.txt")
raw_images_dir = Path("data/raw/images")
raw_labels_dir = Path("data/raw/labels")

sinogram_grid = 128
sinogram_angles = 180
max_display_dots = 4000

cache_size = 16
analysis_cache: OrderedDict = OrderedDict()


def dot_sinogram(dots: np.ndarray) -> np.ndarray:
    grid = np.zeros((sinogram_grid, sinogram_grid))
    if len(dots):
        cols = np.clip(
            ((dots[:, 0] + 1) / 2 * (sinogram_grid - 1)).astype(int),
            0,
            sinogram_grid - 1,
        )
        rows = np.clip(
            ((dots[:, 1] + 1) / 2 * (sinogram_grid - 1)).astype(int),
            0,
            sinogram_grid - 1,
        )
        grid[rows, cols] = 1.0

    angles = np.linspace(0.0, 180.0, sinogram_angles, endpoint=False)
    return radon(grid, theta=angles)


def image_artifacts(image: Image.Image, model: YOLO) -> dict:
    # Everything derived from the image alone — independent of the what-if parameters
    dots = dot_coordinates(np.asarray(image.convert("L")))
    names = load_class_names(classes_file)

    result = model.predict(np.asarray(image), verbose=False)[0]
    detections = (
        []
        if result.masks is None
        else [
            (
                names[int(class_id)],
                float(confidence),
                [(float(x), float(y)) for x, y in segment],
            )
            for class_id, confidence, segment in zip(
                result.boxes.cls, result.boxes.conf, result.masks.xyn, strict=True
            )
        ]
    )

    return {
        "dots": dots,
        "detections": detections,
        "image": image_png(image),
        "sinogram": sinogram_png(dot_sinogram(dots)),
    }


@router.post("/api/analyze")
async def analyze(
    request: Request,
    stem: str = "",
    die_mm: float = 6.0,
    die_value: float = 25.0,
    wafer_radius_mm: float = 150.0,
    file: UploadFile | None = File(default=None),
) -> dict:
    if bool(stem) == (file is not None):
        raise HTTPException(422, "Provide exactly one of stem or file")

    model = request.app.state.model
    if model is None:
        raise HTTPException(503, "The model is not loaded")

    # Resolve the cache key: stem for dataset wafers, content hash for uploads
    if stem:
        image_path = raw_images_dir / f"{stem}.jpg"

        if not image_path.is_file():
            raise HTTPException(404, f"Unknown wafer stem: {stem}")

        key = stem
    else:
        payload = await file.read()
        key = hashlib.sha256(payload).hexdigest()

    # A hit skips image loading, dot extraction, YOLO, and both PNG renders —
    # only the what-if analytics below are recomputed
    if key in analysis_cache:
        analysis_cache.move_to_end(key)
        artifacts = analysis_cache[key]
    else:
        source = image_path if stem else io.BytesIO(payload)
        artifacts = image_artifacts(Image.open(source).convert("RGB"), model)

        analysis_cache[key] = artifacts
        if len(analysis_cache) > cache_size:
            analysis_cache.popitem(last=False)

    dots = artifacts["dots"]
    detections = artifacts["detections"]

    # Use extracted dots and detections to produce per-detection yield loss in dollars, an action form the knowledge-base, scratch kinematics, and a wafer summary
    report = diagnose(
        dots,
        detections,
        load_knowledge_base(kb_path),
        die_mm,
        die_value,
        wafer_radius_mm,
    )
    for entry, (_, _, polygon) in zip(report["detections"], detections, strict=True):
        entry["polygon"] = polygon

    # Subsample for SVG rendering; convert wafer coordinates to normalized image coordinates
    display = dots[:: max(1, len(dots) // max_display_dots)]
    display_image = (display * wafer_frac + 1) / 2  # shape: (n, 2)

    ground_truth = None
    if stem:
        names = load_class_names(classes_file)
        instances = load_label_file(raw_labels_dir / f"{stem}.txt")
        ground_truth = [names[instance.class_id] for instance in instances]

    return {
        "stem": stem or None,
        "image": artifacts["image"],
        "dots": np.round(display_image, 4).tolist(),
        "sinogram": artifacts["sinogram"],
        "detections": report["detections"],
        "wafer_summary": report["wafer_summary"],
        "radial": radial_yield(dots, die_mm, wafer_radius_mm=wafer_radius_mm),
        "zones": zone_yields(dots, die_mm, wafer_radius_mm),
        "ground_truth": ground_truth,
    }
