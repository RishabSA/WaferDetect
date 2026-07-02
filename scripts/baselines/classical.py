import argparse
import json
import os
from pathlib import Path
import numpy as np
from PIL import Image
from skimage.transform import radon
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from tqdm import tqdm

from scripts.datagen.fields import category_class
from scripts.perception.dataset import read_manifests, stem_category

raw_images_dir = Path("data/raw/images")
out_dir = Path("runs/baselines/classical")

dark_threshold = 128
outline_radius = 0.94
wafer_frac = 0.97


def dot_coordinates(image: np.ndarray) -> np.ndarray:
    height, width = image.shape
    rows, cols = np.nonzero(image < dark_threshold)

    u = (cols / (width - 1) * 2 - 1) / wafer_frac
    v = (rows / (height - 1) * 2 - 1) / wafer_frac
    keep = np.hypot(u, v) <= outline_radius
    return np.stack([u[keep], v[keep]], axis=1)


def density_features(
    dots: np.ndarray, radial_bins: int = 4, angular_bins: int = 8
) -> np.ndarray:
    radius = np.clip(np.hypot(dots[:, 0], dots[:, 1]), 0, 0.999)
    theta = np.arctan2(dots[:, 1], dots[:, 0]) % (2 * np.pi)

    r_index = (radius * radial_bins).astype(int)
    t_index = (theta / (2 * np.pi) * angular_bins).astype(int)

    counts = np.zeros((radial_bins, angular_bins))
    np.add.at(counts, (r_index, t_index), 1)
    return (counts / max(len(dots), 1)).ravel()


def radon_features(dots: np.ndarray, size: int = 64, n_angles: int = 20) -> np.ndarray:
    grid = np.zeros((size, size))
    cols = np.clip(((dots[:, 0] + 1) / 2 * (size - 1)).astype(int), 0, size - 1)
    rows = np.clip(((dots[:, 1] + 1) / 2 * (size - 1)).astype(int), 0, size - 1)
    grid[rows, cols] = 1.0

    angles = np.linspace(0.0, 180.0, n_angles, endpoint=False)
    sinogram = radon(grid, theta=angles)
    return np.concatenate([sinogram.mean(axis=0), sinogram.std(axis=0)])


def feature_vector(image: np.ndarray) -> np.ndarray:
    dots = dot_coordinates(image)
    return np.concatenate([density_features(dots), radon_features(dots)])


def load_split(stems: list[str]) -> tuple[np.ndarray, list[str]]:
    singles = [stem for stem in stems if stem_category(stem) != "combo"]
    features = [
        feature_vector(
            np.asarray(Image.open(raw_images_dir / f"{stem}.jpg").convert("L"))
        )
        for stem in tqdm(singles, desc="extracting features")
    ]
    labels = [category_class(stem_category(stem)) for stem in singles]

    return np.stack(features), labels


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--c",
        type=float,
        default=10.0,
        help="SVM regularization parameter C (default: 10.0).",
    )

    args = parser.parse_args()

    manifests = read_manifests()
    train_x, train_y = load_split(manifests["train"])
    test_x, test_y = load_split(manifests["test"])
    combo_test_count = sum(
        1 for stem in manifests["test"] if stem_category(stem) == "combo"
    )

    model = make_pipeline(StandardScaler(), SVC(kernel="rbf", C=args.c))
    model.fit(train_x, train_y)
    predictions = model.predict(test_x)

    metrics = {
        "test_accuracy_singles": float(accuracy_score(test_y, predictions)),
        "test_macro_f1_singles": float(f1_score(test_y, predictions, average="macro")),
        "combo_test_wafers": combo_test_count,
        "combo_exact_match": 0.0,
        "report": classification_report(test_y, predictions, output_dict=True),
    }

    os.makedirs(out_dir, exist_ok=True)
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")

    print(f"Singles accuracy: {metrics['test_accuracy_singles']:.4f}")
    print(f"Singles macro-F1: {metrics['test_macro_f1_singles']:.4f}")
    print(f"Wrote {out_dir / 'metrics.json'}")
