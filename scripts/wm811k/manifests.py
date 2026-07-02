import argparse
import json
import os
import random
from pathlib import Path
import pandas as pd

parquet_path = Path("data/wm811k/labeled.parquet")
manifests_dir = Path("data/wm811k/manifests")

calibration_frac = 0.10
fewshot_frac = 0.40


def build_manifests(
    frame: pd.DataFrame,
    seed: int,
    eval_cap: int = 2000,
    calibration_per_class: int = 50,
    fewshot_reserve: int = 600,
    none_calibration: int = 200,
    none_eval: int = 2000,
) -> dict[str, list[int]]:
    rng = random.Random(seed)
    manifests = {"calibration": [], "eval": [], "fewshot_pool": []}

    for name, group in frame.groupby("failure_type"):
        indices = sorted(group.index.tolist())
        rng.shuffle(indices)

        if name == "none":
            # The threshold sweep needs defect-free wafers to feel false-positive pressure.
            manifests["calibration"].extend(indices[:none_calibration])
            manifests["eval"].extend(
                indices[none_calibration : none_calibration + none_eval]
            )
            continue

        n_calibration = min(calibration_per_class, int(len(indices) * calibration_frac))
        n_pool = min(fewshot_reserve, int(len(indices) * fewshot_frac))

        manifests["calibration"].extend(indices[:n_calibration])
        manifests["fewshot_pool"].extend(
            indices[n_calibration : n_calibration + n_pool]
        )
        manifests["eval"].extend(indices[n_calibration + n_pool :][:eval_cap])

    return {name: sorted(members) for name, members in manifests.items()}


def write_manifests(
    manifests: dict[str, list[int]],
    frame: pd.DataFrame,
    out_dir: Path,
    seed: int | None = None,
) -> None:
    os.makedirs(out_dir, exist_ok=True)
    summary = {"seed": seed, "manifests": {}}

    for name, members in manifests.items():
        (out_dir / f"{name}.txt").write_text("\n".join(str(i) for i in members) + "\n")
        counts = frame.loc[members, "failure_type"].value_counts().to_dict()
        summary["manifests"][name] = {"total": len(members), "per_class": counts}

    (out_dir / "manifest_summary.json").write_text(json.dumps(summary, indent=2) + "\n")


def read_manifest(path: Path) -> list[int]:
    return [int(line) for line in path.read_text().splitlines() if line.strip()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--parquet",
        type=str,
        default=str(parquet_path),
        help="Labeled parquet path (default: data/wm811k/labeled.parquet).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=str(manifests_dir),
        help="Manifest output directory (default: data/wm811k/manifests).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed to use for reproducibility (default: 42).",
    )
    parser.add_argument(
        "--eval-cap",
        type=int,
        default=2000,
        help="Max eval wafers per class (default: 2000).",
    )

    args = parser.parse_args()
    frame = pd.read_parquet(args.parquet)
    manifests = build_manifests(frame, args.seed, eval_cap=args.eval_cap)
    write_manifests(manifests, frame, Path(args.out_dir), args.seed)

    for name, members in manifests.items():
        print(f"{name}: {len(members)} wafers")
