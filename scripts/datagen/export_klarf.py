import argparse
import os
import shutil
from pathlib import Path
import numpy as np
from PIL import Image
from tqdm import tqdm

from scripts.api.klarf import klarf_text
from scripts.baselines.classical import dot_coordinates
from scripts.perception.annotations import load_class_names, load_label_file

classes_file = Path("data/raw/classes.txt")
raw_images_dir = Path("data/raw/images")
raw_labels_dir = Path("data/raw/labels")
klarf_dir = Path("data/klarf")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--force",
        action="store_true",
        help="Whether to delete and rebuild data/klarf if it exists (default: False).",
    )
    parser.add_argument(
        "--die-mm",
        type=float,
        default=6.0,
        help="Die pitch in mm written to every KLARF (default: 6.0).",
    )
    parser.add_argument(
        "--wafer-radius-mm",
        type=float,
        default=150.0,
        help="Wafer radius in mm written to every KLARF (default: 150.0).",
    )

    args = parser.parse_args()

    if klarf_dir.exists():
        if not args.force:
            raise FileExistsError(f"{klarf_dir} already exists, so rerun with --force")

        shutil.rmtree(klarf_dir)

    os.makedirs(klarf_dir, exist_ok=True)

    names = load_class_names(classes_file)
    image_paths = sorted(raw_images_dir.glob("*.jpg"))

    for image_path in tqdm(image_paths, desc="Exporting KLARF"):
        stem = image_path.stem
        dots = dot_coordinates(np.asarray(Image.open(image_path).convert("L")))

        # Ground-truth labels stand in for detections, so each KLARF carries the known classes and re-ingesting one shows them as ground truth
        instances = load_label_file(raw_labels_dir / f"{stem}.txt")
        detections = [
            (names[instance.class_id], 1.0, instance.polygon) for instance in instances
        ]

        text = klarf_text(
            dots, detections, names, stem, args.die_mm, args.wafer_radius_mm
        )
        (klarf_dir / f"{stem}.klarf").write_text(text)

    print(f"Wrote {len(image_paths)} KLARF files to {klarf_dir}")
