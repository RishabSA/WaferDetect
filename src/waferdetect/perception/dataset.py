import argparse
import os
import random
import shutil
from pathlib import Path
import yaml

from waferdetect.perception.annotations import load_class_names, load_dataset

classes_file = Path("data/raw/classes.txt")
raw_images_dir = Path("data/raw/images")
raw_labels_dir = Path("data/raw/labels")
splits_dir = Path("data/splits")
yolo_dir = Path("data/yolo")

split_names = ("train", "val", "test")


def stem_category(stem: str) -> str:
    prefix, _, category = stem.partition("_")
    if not prefix.isdigit() or not category:
        raise ValueError(f"Unexpected wafer stem format: {stem}")

    # Combos pool into one group: first-class groups are too small (1-2 images)
    # to guarantee presence in all three splits
    if category.startswith("combo_"):
        return "combo"

    return category


def compute_split(
    stems: list[str], train_frac: float, val_frac: float, seed: int
) -> dict:
    by_category = {}

    # Maps a filename stem to its stratification bucket
    for stem in sorted(stems):
        by_category.setdefault(stem_category(stem), []).append(stem)

    rng = random.Random(seed)
    split = {name: [] for name in split_names}

    for category in sorted(by_category):
        members = sorted(by_category[category])
        rng.shuffle(members)
        count = len(members)

        n_train = round(count * train_frac)
        n_val = round(count * val_frac)

        split["train"].extend(members[:n_train])
        split["val"].extend(members[n_train : n_train + n_val])
        split["test"].extend(members[n_train + n_val :])

    for name in split_names:
        split[name].sort()

    return split


def write_manifests(split: dict) -> None:
    os.makedirs(splits_dir, exist_ok=True)
    for name in split_names:
        (splits_dir / f"{name}.txt").write_text("\n".join(split[name]) + "\n")


def read_manifests() -> dict:
    return {
        name: [
            line.strip()
            for line in (splits_dir / f"{name}.txt").read_text().splitlines()
            if line.strip()
        ]
        for name in split_names
    }


def write_data_yaml(
    dataset_dir: Path, class_names: list[str], split_paths: dict[str, str]
) -> Path:
    content = {
        "path": str(dataset_dir.resolve()),
        **split_paths,
        "names": {index: name for index, name in enumerate(class_names)},
    }

    yaml_path = dataset_dir / "data.yaml"

    with open(yaml_path, "w") as file:
        yaml.safe_dump(content, file, sort_keys=False)

    return yaml_path


def build_yolo_layout(
    split: dict[str, list[str]],
    class_names: list[str],
) -> Path:
    for name in split_names:
        images_out = yolo_dir / "images" / name
        labels_out = yolo_dir / "labels" / name

        os.makedirs(images_out, exist_ok=True)
        os.makedirs(labels_out, exist_ok=True)

        for stem in split[name]:
            shutil.copy2(raw_images_dir / f"{stem}.jpg", images_out / f"{stem}.jpg")
            shutil.copy2(raw_labels_dir / f"{stem}.txt", labels_out / f"{stem}.txt")

    return write_data_yaml(
        yolo_dir,
        class_names,
        {"train": "images/train", "val": "images/val", "test": "images/test"},
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--force",
        action="store_true",
        help="Whether to delete and rebuild data/yolo if it exists (default: False).",
    )
    parser.add_argument(
        "--train-frac",
        type=float,
        default=0.70,
        help="Fraction of the dataset split to use for training (default: 0.70).",
    )
    parser.add_argument(
        "--val-frac",
        type=float,
        default=0.15,
        help="Fraction of the dataset split to use for validation (default: 0.15).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed to use for reproducibility (defualt: 42).",
    )

    args = parser.parse_args()

    class_names = load_class_names(classes_file)
    dataset = load_dataset(raw_images_dir, raw_labels_dir)
    print(f"loaded {len(dataset)} image/label pairs")
    split = compute_split(sorted(dataset), args.train_frac, args.val_frac, args.seed)
    write_manifests(split)

    if yolo_dir.exists():
        if not args.force:
            raise FileExistsError(f"{yolo_dir} already exists, so rerun with --force")

        shutil.rmtree(yolo_dir)

    yaml_path = build_yolo_layout(split, class_names)

    counts = {name: len(split[name]) for name in split_names}
    print(f"Split counts: {counts}")
    print(f"Wrote {yaml_path}")
