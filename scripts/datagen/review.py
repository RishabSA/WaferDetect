import argparse
import os
from pathlib import Path
from PIL import Image
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scripts.perception.annotations import load_label_file
from scripts.perception.dataset import stem_category


def write_review_sheets(generated_dir: Path, per_category: int = 5) -> Path:
    images_dir = generated_dir / "images"
    labels_dir = generated_dir / "labels"
    review_dir = generated_dir / "review"
    os.makedirs(review_dir, exist_ok=True)

    by_category = {}
    for path in sorted(images_dir.glob("*.jpg")):
        by_category.setdefault(stem_category(path.stem), []).append(path)

    for category, paths in by_category.items():
        chosen = paths[:per_category]
        figure, axes = plt.subplots(1, len(chosen), figsize=(4 * len(chosen), 4))
        if len(chosen) == 1:
            axes = [axes]

        for axis, path in zip(axes, chosen, strict=True):
            image = Image.open(path)
            width, height = image.size
            axis.imshow(image, cmap="gray")

            for instance in load_label_file(labels_dir / f"{path.stem}.txt"):
                xs = [x * width for x, _ in instance.polygon] + [
                    instance.polygon[0][0] * width
                ]
                ys = [y * height for _, y in instance.polygon] + [
                    instance.polygon[0][1] * height
                ]

                axis.plot(xs, ys, linewidth=1.5)

            axis.set_title(path.stem, fontsize=8)
            axis.axis(False)

        figure.suptitle(category)
        figure.savefig(review_dir / f"{category}.png", dpi=100, bbox_inches="tight")
        plt.close(figure)

    return review_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--generated-dir",
        type=str,
        required=True,
        help="Generated dataset directory containing images/ and labels/ (required).",
    )
    parser.add_argument(
        "--per-category",
        type=int,
        default=5,
        help="Samples to render per category (default: 5).",
    )

    args = parser.parse_args()

    review_dir = write_review_sheets(Path(args.generated_dir), args.per_category)
    print(f"Wrote review sheets to {review_dir}")
