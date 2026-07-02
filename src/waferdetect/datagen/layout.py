import argparse
import os
import random
import shutil
from pathlib import Path

from waferdetect.perception.annotations import load_class_names
from waferdetect.perception.dataset import stem_category, write_data_yaml

classes_file = Path("data/raw/classes.txt")
raw_test_images = Path("data/yolo/images/test")


def build_layout(
    generated_dir: Path, out_dir: Path, val_frac: float, seed: int, limit: int = 0
) -> Path:
    rng = random.Random(seed)
    stems = sorted(path.stem for path in (generated_dir / "labels").glob("*.txt"))

    if limit:
        rng.shuffle(stems)
        stems = sorted(stems[:limit])

    by_category = {}
    for stem in stems:
        by_category.setdefault(stem_category(stem), []).append(stem)

    split = {"train": [], "val": []}
    for category in sorted(by_category):
        members = sorted(by_category[category])
        rng.shuffle(members)
        n_val = round(len(members) * val_frac)
        split["val"].extend(members[:n_val])
        split["train"].extend(members[n_val:])

    for name, members in split.items():
        images_out = out_dir / "images" / name
        labels_out = out_dir / "labels" / name
        os.makedirs(images_out, exist_ok=True)
        os.makedirs(labels_out, exist_ok=True)

        for stem in members:
            shutil.copy2(generated_dir / "images" / f"{stem}.jpg", images_out)
            shutil.copy2(generated_dir / "labels" / f"{stem}.txt", labels_out)

    # Test points at the frozen raw split for direct Stage 1/2 comparisons.
    return write_data_yaml(
        out_dir,
        load_class_names(classes_file),
        {
            "train": "images/train",
            "val": "images/val",
            "test": str(raw_test_images.resolve()),
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--generated-dir",
        type=str,
        required=True,
        help="Generated dataset directory containing images/ and labels/ (required).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        required=True,
        help="Output YOLO layout directory (required).",
    )
    parser.add_argument(
        "--val-frac",
        type=float,
        default=0.1,
        help="Fraction of the generated set used for validation (default: 0.1).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed to use for reproducibility (default: 42).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Seeded subsample size for scaling runs; 0 means all (default: 0).",
    )

    args = parser.parse_args()

    yaml_path = build_layout(
        Path(args.generated_dir),
        Path(args.out_dir),
        args.val_frac,
        args.seed,
        args.limit,
    )
    print(f"Wrote {yaml_path}")
