from pathlib import Path

import numpy as np

from waferdetect.datagen.generator import generate_sample, sample_name
from waferdetect.datagen.review import write_review_sheets
from waferdetect.perception.annotations import load_class_names

classes_file = Path("data/raw/classes.txt")


def test_write_review_sheets(tmp_path: Path) -> None:
    class_names = load_class_names(classes_file)
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"
    images_dir.mkdir()
    labels_dir.mkdir()

    rng = np.random.default_rng(0)
    for index, category in enumerate(["donut", "donut", "scratch"], start=1):
        image, lines = generate_sample([category], class_names, rng)
        name = sample_name(index, [category])
        image.save(images_dir / f"{name}.jpg")
        (labels_dir / f"{name}.txt").write_text("\n".join(lines) + "\n")

    review_dir = write_review_sheets(tmp_path, per_category=2)

    assert (review_dir / "donut.png").is_file()
    assert (review_dir / "scratch.png").is_file()
