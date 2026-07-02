import argparse
import os
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm

from scripts.datagen.generator import render
from scripts.wm811k.convert import load_map
from scripts.wm811k.manifests import read_manifest

parquet_path = Path("data/wm811k/labeled.parquet")


def die_dots(wafer_map: np.ndarray) -> np.ndarray:
    rows, cols = np.nonzero(wafer_map == 2)
    height, width = wafer_map.shape

    u = (cols + 0.5) / width * 2 - 1
    v = (rows + 0.5) / height * 2 - 1
    return np.stack([u, v], axis=1)


def render_manifest(
    frame: pd.DataFrame, indices: list[int], out_dir: Path, seed: int
) -> None:
    os.makedirs(out_dir, exist_ok=True)

    for index in tqdm(indices, desc="rendering wafers"):
        row = frame.loc[index]
        dots = die_dots(load_map(row))

        # Per-wafer seed keeps dot-radius jitter reproducible across re-renders.
        image = render(dots, np.random.default_rng(seed + index))
        image.save(out_dir / f"{index:06d}_{row['failure_type']}.jpg")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--manifest",
        type=str,
        required=True,
        help="Manifest txt of parquet row indices to render (required).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        required=True,
        help="Output image directory (required).",
    )
    parser.add_argument(
        "--parquet",
        type=str,
        default=str(parquet_path),
        help="Labeled parquet path (default: data/wm811k/labeled.parquet).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed to use for reproducibility (default: 42).",
    )

    args = parser.parse_args()
    frame = pd.read_parquet(args.parquet)
    indices = read_manifest(Path(args.manifest))
    render_manifest(frame, indices, Path(args.out_dir), args.seed)
    print(f"Rendered {len(indices)} wafers to {args.out_dir}")
