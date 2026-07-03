import io
from pathlib import Path
import numpy as np
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from PIL import Image
from skimage.transform import radon

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


@router.post("/api/analyze")
async def analyze(
    request: Request,
    stem: str = "",
    die_mm: float = 6.0,
    die_value: float = 25.0,
    file: UploadFile | None = File(default=None),
) -> dict:
    if bool(stem) == (file is not None):
        raise HTTPException(422, "provide exactly one of stem or file")

    model = request.app.state.model
    if model is None:
        raise HTTPException(503, "server started without --model-path")

    if stem:
        image_path = raw_images_dir / f"{stem}.jpg"
        if not image_path.is_file():
            raise HTTPException(404, f"unknown wafer stem: {stem}")
        image = Image.open(image_path).convert("RGB")
    else:
        image = Image.open(io.BytesIO(await file.read())).convert("RGB")

    dots = dot_coordinates(np.asarray(image.convert("L")))

    result = model.predict(np.asarray(image), verbose=False)[0]
    names = load_class_names(classes_file)
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

    report = diagnose(dots, detections, load_knowledge_base(kb_path), die_mm, die_value)
    for entry, (_, _, polygon) in zip(report["detections"], detections, strict=True):
        entry["polygon"] = polygon

    # Subsample for SVG rendering; convert wafer coordinates to normalized image coordinates
    display = dots[:: max(1, len(dots) // max_display_dots)]
    display_image = (display * wafer_frac + 1) / 2  # shape: (n, 2)

    ground_truth = None
    if stem:
        instances = load_label_file(raw_labels_dir / f"{stem}.txt")
        ground_truth = [names[instance.class_id] for instance in instances]

    return {
        "stem": stem or None,
        "image": image_png(image),
        "dots": np.round(display_image, 4).tolist(),
        "sinogram": sinogram_png(dot_sinogram(dots)),
        "detections": report["detections"],
        "wafer_summary": report["wafer_summary"],
        "radial": radial_yield(dots, die_mm),
        "zones": zone_yields(dots, die_mm),
        "ground_truth": ground_truth,
    }
