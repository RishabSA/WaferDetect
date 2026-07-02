import io
from pathlib import Path
import numpy as np
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from PIL import Image

from scripts.analytics.diagnosis import polygon_area, polygon_centroid_radius
from scripts.perception.annotations import load_class_names

router = APIRouter()

classes_file = Path("data/raw/classes.txt")
raw_images_dir = Path("data/raw/images")


def detections_to_response(
    class_ids: list, confidences: list, segments: list, class_names: list[str]
) -> list[dict]:
    detections = []
    for class_id, confidence, segment in zip(
        class_ids, confidences, segments, strict=True
    ):
        polygon = [(float(x), float(y)) for x, y in segment]
        detections.append(
            {
                "class": class_names[int(class_id)],
                "confidence": float(confidence),
                "polygon": polygon,
                "area_frac": polygon_area(polygon),
                "centroid_r": polygon_centroid_radius(polygon),
            }
        )

    return detections


@router.post("/api/detect")
async def detect(
    request: Request, stem: str = "", file: UploadFile | None = File(default=None)
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
        source = np.asarray(Image.open(image_path).convert("RGB"))
    else:
        source = np.asarray(Image.open(io.BytesIO(await file.read())).convert("RGB"))

    result = model.predict(source, verbose=False)[0]
    if result.masks is None:
        return {"detections": []}

    names = load_class_names(classes_file)
    return {
        "detections": detections_to_response(
            result.boxes.cls, result.boxes.conf, result.masks.xyn, names
        )
    }
