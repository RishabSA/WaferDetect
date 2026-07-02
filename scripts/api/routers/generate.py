from pathlib import Path
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from scripts.api.plots import image_png
from scripts.datagen.fields import field_builders
from scripts.datagen.generator import choose_categories, generate_sample
from scripts.perception.annotations import load_class_names

router = APIRouter()

classes_file = Path("data/raw/classes.txt")


class GenerateRequest(BaseModel):
    categories: list[str] | None = None
    combo_frac: float = 0.0
    physics_frac: float = 0.0
    die_grid: int = 0
    seed: int = 42


@router.post("/api/generate")
def generate(request: GenerateRequest) -> dict:
    rng = np.random.default_rng(request.seed)
    categories = request.categories or choose_categories(rng, request.combo_frac)

    unknown = [category for category in categories if category not in field_builders]
    if unknown:
        raise HTTPException(
            422, f"unknown categories {unknown}; valid: {sorted(field_builders)}"
        )

    image, lines = generate_sample(
        categories,
        load_class_names(classes_file),
        rng,
        request.die_grid,
        request.physics_frac,
    )

    return {"categories": categories, "labels": lines, "image": image_png(image)}
