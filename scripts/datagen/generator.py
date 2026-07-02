import argparse
import json
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from tqdm import tqdm

from scripts.datagen.fields import category_class, field_builders
from scripts.datagen.labels import (
    field_mask,
    field_to_polygon,
    mask_iou,
    wafer_to_image,
    yolo_line,
)
from scripts.perception.annotations import load_class_names

classes_file = Path("data/raw/classes.txt")

image_size = 640
grid_size = 256
wafer_frac = 0.97

combo_size_weights = (0.75, 0.20, 0.05)
combo_iou_limit = 0.7
max_overlap_retries = 10

pattern_dot_counts = {
    "near_full": (900, 1600),
    "random": (250, 500),
    "gradient": (350, 700),
    "half_wafer": (250, 500),
}
default_dot_count = (120, 280)
background_dot_count = (30, 90)


def sample_dots(field: np.ndarray, count: int, rng: np.random.Generator) -> np.ndarray:
    grid = field.shape[0]
    flat = field.ravel()
    cells = rng.choice(flat.size, size=count, p=flat / flat.sum())

    rows, cols = np.divmod(cells, grid)
    jitter = rng.uniform(-0.5, 0.5, size=(count, 2))
    u = (cols + jitter[:, 0]) / (grid - 1) * 2 - 1
    v = (rows + jitter[:, 1]) / (grid - 1) * 2 - 1
    dots = np.stack([u, v], axis=1)

    radius = np.hypot(dots[:, 0], dots[:, 1])
    outside = radius > 0.99
    dots[outside] = dots[outside] / radius[outside, None] * 0.99
    return dots


def background_dots(count: int, rng: np.random.Generator) -> np.ndarray:
    # sqrt makes radial density uniform in area, not clustered at the center
    radius = np.sqrt(rng.uniform(0, 1, count)) * 0.98
    theta = rng.uniform(0, 2 * np.pi, count)
    return np.stack([radius * np.cos(theta), radius * np.sin(theta)], axis=1)


def quantize_dots(dots: np.ndarray, die_grid: int) -> np.ndarray:
    cell = 2.0 / die_grid
    snapped = (np.floor((dots + 1) / cell) + 0.5) * cell - 1
    return np.unique(snapped.round(6), axis=0)


def render(dots: np.ndarray, rng: np.random.Generator) -> Image.Image:
    image = Image.new("L", (image_size, image_size), 255)
    draw = ImageDraw.Draw(image)

    margin = image_size * (1 - wafer_frac) / 2
    draw.ellipse(
        [margin, margin, image_size - margin, image_size - margin], outline=0, width=2
    )

    for u, v in dots:
        x = (0.5 + u * wafer_frac / 2) * image_size
        y = (0.5 + v * wafer_frac / 2) * image_size
        radius = rng.uniform(1.2, 2.4)
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=0)

    return image


def choose_categories(rng: np.random.Generator, combo_frac: float) -> list[str]:
    categories = sorted(field_builders)
    if rng.random() >= combo_frac:
        return [str(rng.choice(categories))]

    size = int(rng.choice((2, 3, 4), p=combo_size_weights))
    return [str(category) for category in rng.choice(categories, size=size)]


def sample_name(index: int, categories: list[str]) -> str:
    if len(categories) == 1:
        return f"{index:04d}_{categories[0]}"

    return f"{index:04d}_combo_" + "+".join(
        category_class(category) for category in categories
    )


def generate_sample(
    categories: list[str],
    class_names: list[str],
    rng: np.random.Generator,
    die_grid: int = 0,
) -> tuple[Image.Image, list[str]]:
    dots = []
    lines = []
    masks = []

    for category in categories:
        for _ in range(max_overlap_retries):
            field = field_builders[category](grid_size, rng)
            mask = field_mask(field)
            if all(mask_iou(mask, other) <= combo_iou_limit for other in masks):
                break
        masks.append(mask)

        low, high = pattern_dot_counts.get(category, default_dot_count)
        dots.append(sample_dots(field, int(rng.integers(low, high)), rng))

        polygon = wafer_to_image(field_to_polygon(field), wafer_frac)
        class_id = class_names.index(category_class(category))
        lines.append(yolo_line(class_id, polygon))

    dots.append(background_dots(int(rng.integers(*background_dot_count)), rng))
    all_dots = np.concatenate(dots)
    if die_grid:
        all_dots = quantize_dots(all_dots, die_grid)

    return render(all_dots, rng), lines


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--out-dir",
        type=str,
        required=True,
        help="Output dataset directory, e.g. data/generated/v1 (required).",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10000,
        help="Number of wafer maps to generate (default: 10000).",
    )
    parser.add_argument(
        "--combo-frac",
        type=float,
        default=0.17,
        help="Fraction of samples with multiple patterns, like the raw set (default: 0.17).",
    )
    parser.add_argument(
        "--die-grid-frac",
        type=float,
        default=0.0,
        help="Fraction of samples rendered with die-grid quantization (default: 0.0).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed to use for reproducibility (default: 42).",
    )

    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    images_dir = out_dir / "images"
    labels_dir = out_dir / "labels"
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)

    class_names = load_class_names(classes_file)
    rng = np.random.default_rng(args.seed)
    category_counts = {}

    for index in tqdm(range(1, args.count + 1), desc="generating wafers"):
        categories = choose_categories(rng, args.combo_frac)
        die_grid = int(rng.integers(26, 61)) if rng.random() < args.die_grid_frac else 0

        image, lines = generate_sample(categories, class_names, rng, die_grid)
        name = sample_name(index, categories)
        image.save(images_dir / f"{name}.jpg")
        (labels_dir / f"{name}.txt").write_text("\n".join(lines) + "\n")

        key = "combo" if len(categories) > 1 else categories[0]
        category_counts[key] = category_counts.get(key, 0) + 1

    manifest = {
        "count": args.count,
        "combo_frac": args.combo_frac,
        "die_grid_frac": args.die_grid_frac,
        "seed": args.seed,
        "image_size": image_size,
        "grid_size": grid_size,
        "wafer_frac": wafer_frac,
        "category_counts": dict(sorted(category_counts.items())),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"Wrote {args.count} samples to {out_dir}")
