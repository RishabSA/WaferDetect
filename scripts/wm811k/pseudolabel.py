import argparse
import os
import random
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull
from sklearn.cluster import DBSCAN
from tqdm import tqdm

from scripts.datagen.generator import render, wafer_frac
from scripts.datagen.labels import wafer_to_image, yolo_line
from scripts.perception.annotations import load_class_names
from scripts.perception.dataset import write_data_yaml
from scripts.wm811k.convert import load_map
from scripts.wm811k.manifests import read_manifest
from scripts.wm811k.render import die_dots

classes_file = Path("data/raw/classes.txt")
parquet_path = Path("data/wm811k/labeled.parquet")
pool_path = Path("data/wm811k/manifests/fewshot_pool.txt")

edge_classes = ("edge_ring", "edge_loc")
whole_wafer_classes = ("near_full", "random")
eps_pitches = 2.5
min_cluster_dots = 4


def pseudo_polygon(wafer_map: np.ndarray, class_name: str) -> list[tuple[float, float]]:
    dots = die_dots(wafer_map)
    pitch = 2.0 / max(wafer_map.shape)

    if class_name in whole_wafer_classes or len(dots) < min_cluster_dots:
        chosen = dots
    else:
        cluster_ids = DBSCAN(eps=eps_pitches * pitch, min_samples=3).fit_predict(dots)
        clusters = [
            dots[cluster_ids == index] for index in set(cluster_ids) if index != -1
        ]

        if not clusters:
            chosen = dots
        elif class_name in edge_classes:
            chosen = max(
                clusters,
                key=lambda cluster: float(
                    np.hypot(cluster[:, 0], cluster[:, 1]).mean()
                ),
            )
        else:
            chosen = max(clusters, key=len)

    # Hull over die corners is non-degenerate for perfectly collinear scratch dies.
    half = pitch / 2
    corners = np.concatenate(
        [chosen + [dx, dy] for dx in (-half, half) for dy in (-half, half)]
    )
    hull = ConvexHull(corners)
    return [tuple(point) for point in corners[hull.vertices]]


def pseudo_label_line(
    wafer_map: np.ndarray, class_name: str, class_names: list[str]
) -> str:
    polygon = wafer_to_image(pseudo_polygon(wafer_map, class_name), wafer_frac)
    return yolo_line(class_names.index(class_name), polygon)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--budget",
        type=int,
        required=True,
        help="Wafers per class to fine-tune on (required).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed to use for reproducibility (default: 42).",
    )
    parser.add_argument(
        "--parquet",
        type=str,
        default=str(parquet_path),
        help="Labeled parquet path (default: data/wm811k/labeled.parquet).",
    )
    parser.add_argument(
        "--pool",
        type=str,
        default=str(pool_path),
        help="Few-shot pool manifest (default: data/wm811k/manifests/fewshot_pool.txt).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="",
        help="Output layout dir (default: data/wm811k/fewshot_<budget>_<seed>).",
    )
    parser.add_argument(
        "--val-frac",
        type=float,
        default=0.1,
        help="Fraction of the budget used for validation (default: 0.1).",
    )

    args = parser.parse_args()
    out_dir = Path(args.out_dir or f"data/wm811k/fewshot_{args.budget}_{args.seed}")

    frame = pd.read_parquet(args.parquet)
    pool = read_manifest(Path(args.pool))
    class_names = load_class_names(classes_file)
    rng = random.Random(args.seed)

    split = {"train": [], "val": []}
    for name, group in frame.loc[pool].groupby("failure_type"):
        indices = sorted(group.index.tolist())
        rng.shuffle(indices)
        taken = indices[: args.budget]
        if len(taken) < args.budget:
            print(f"{name}: pool has only {len(taken)} wafers (budget {args.budget})")

        n_val = max(1, round(len(taken) * args.val_frac))
        split["val"].extend(taken[:n_val])
        split["train"].extend(taken[n_val:])

    for split_name, members in split.items():
        images_out = out_dir / "images" / split_name
        labels_out = out_dir / "labels" / split_name
        os.makedirs(images_out, exist_ok=True)
        os.makedirs(labels_out, exist_ok=True)

        for index in tqdm(members, desc=f"building {split_name}"):
            row = frame.loc[index]
            wafer_map = load_map(row)
            stem = f"{index:06d}_{row['failure_type']}"

            image = render(
                die_dots(wafer_map), np.random.default_rng(args.seed + index)
            )
            image.save(images_out / f"{stem}.jpg")
            line = pseudo_label_line(wafer_map, row["failure_type"], class_names)
            (labels_out / f"{stem}.txt").write_text(line + "\n")

    yaml_path = write_data_yaml(
        out_dir, class_names, {"train": "images/train", "val": "images/val"}
    )
    counts = {name: len(members) for name, members in split.items()}
    print(f"Layout counts: {counts}")
    print(f"Wrote {yaml_path}")
