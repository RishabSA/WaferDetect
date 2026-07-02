from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from scripts.perception.annotations import load_class_names, load_label_file
from scripts.perception.dataset import read_manifests, stem_category

router = APIRouter()

classes_file = Path("data/raw/classes.txt")
raw_images_dir = Path("data/raw/images")
raw_labels_dir = Path("data/raw/labels")


def stem_splits() -> dict:
    return {stem: name for name, stems in read_manifests().items() for stem in stems}


@router.get("/api/wafers")
def list_wafers(
    split: str = "", category: str = "", offset: int = 0, limit: int = 50
) -> dict:
    splits = stem_splits()
    stems = sorted(splits)

    if split:
        stems = [stem for stem in stems if splits[stem] == split]

    if category:
        stems = [stem for stem in stems if stem_category(stem) == category]

    items = [
        {"stem": stem, "category": stem_category(stem), "split": splits[stem]}
        for stem in stems[offset : offset + limit]
    ]

    return {"total": len(stems), "items": items}


@router.get("/api/wafers/{stem}")
def wafer_detail(stem: str) -> dict:
    label_path = raw_labels_dir / f"{stem}.txt"
    if not label_path.is_file():
        raise HTTPException(404, f"unknown wafer stem: {stem}")

    names = load_class_names(classes_file)
    instances = [
        {"class": names[instance.class_id], "vertices": len(instance.polygon)}
        for instance in load_label_file(label_path)
    ]

    return {
        "stem": stem,
        "category": stem_category(stem),
        "split": stem_splits().get(stem, ""),
        "instances": instances,
    }


@router.get("/api/wafers/{stem}/image")
def wafer_image(stem: str) -> FileResponse:
    image_path = raw_images_dir / f"{stem}.jpg"
    if not image_path.is_file():
        raise HTTPException(404, f"unknown wafer stem: {stem}")

    return FileResponse(image_path, media_type="image/jpeg")
