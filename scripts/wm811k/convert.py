import argparse
import os
import pickle
from pathlib import Path
import sys
import types
import numpy as np
import pandas as pd

pickle_path = Path("data/wm811k/LSWMD.pkl")
parquet_path = Path("data/wm811k/labeled.parquet")

wm811k_class_map = {
    "Center": "center",
    "Donut": "donut",
    "Edge-Ring": "edge_ring",
    "Edge-Loc": "edge_loc",
    "Scratch": "scratch",
    "Random": "random",
    "Loc": "loc",
    "Near-full": "near_full",
    "none": "none",
}


def install_legacy_pandas_pickle_aliases() -> None:
    import pandas.core.indexes.base as base
    import pandas.core.indexes.category as category
    import pandas.core.indexes.datetimes as datetimes
    import pandas.core.indexes.multi as multi
    import pandas.core.indexes.period as period
    import pandas.core.indexes.range as range_index
    import pandas.core.indexes.timedeltas as timedeltas

    package = types.ModuleType("pandas.indexes")
    package.__path__ = []
    package.Index = pd.Index
    package.MultiIndex = pd.MultiIndex
    package.RangeIndex = pd.RangeIndex

    numeric = types.ModuleType("pandas.indexes.numeric")
    numeric.Int64Index = pd.Index
    numeric.Float64Index = pd.Index
    numeric.UInt64Index = pd.Index

    aliases = {
        "pandas.indexes": package,
        "pandas.indexes.base": base,
        "pandas.indexes.category": category,
        "pandas.indexes.datetimes": datetimes,
        "pandas.indexes.multi": multi,
        "pandas.indexes.numeric": numeric,
        "pandas.indexes.period": period,
        "pandas.indexes.range": range_index,
        "pandas.indexes.timedeltas": timedeltas,
    }
    for old_name, module in aliases.items():
        sys.modules.setdefault(old_name, module)


def flatten_label(value) -> str | None:
    flat = np.ravel(value)
    return str(flat[0]) if flat.size else None


def read_pickle_compat(path: Path):
    install_legacy_pandas_pickle_aliases()
    try:
        return pd.read_pickle(path)
    except UnicodeDecodeError:
        with open(path, "rb") as file:
            return pickle.load(file, encoding="latin1")


def convert(pickle_path: Path, parquet_path: Path) -> pd.DataFrame:
    raw = read_pickle_compat(pickle_path)

    labels = raw["failureType"].map(flatten_label)
    keep = labels.isin(wm811k_class_map)
    maps = raw.loc[keep, "waferMap"]

    frame = pd.DataFrame(
        {
            "failure_type": labels[keep].map(wm811k_class_map).to_numpy(),
            "lot": raw.loc[keep, "lotName"].astype(str).to_numpy(),
            "rows": maps.map(lambda wafer_map: wafer_map.shape[0]).to_numpy(),
            "cols": maps.map(lambda wafer_map: wafer_map.shape[1]).to_numpy(),
            "map": maps.map(
                lambda wafer_map: wafer_map.astype(np.uint8).tobytes()
            ).to_numpy(),
        }
    )

    os.makedirs(parquet_path.parent, exist_ok=True)
    frame.to_parquet(parquet_path)
    return frame


def load_map(row) -> np.ndarray:
    return np.frombuffer(row["map"], dtype=np.uint8).reshape(row["rows"], row["cols"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--pickle",
        type=str,
        default=str(pickle_path),
        help="Path to the downloaded LSWMD.pkl (default: data/wm811k/LSWMD.pkl).",
    )
    parser.add_argument(
        "--parquet",
        type=str,
        default=str(parquet_path),
        help="Output parquet path (default: data/wm811k/labeled.parquet).",
    )

    args = parser.parse_args()
    frame = convert(Path(args.pickle), Path(args.parquet))

    print(frame["failure_type"].value_counts().to_string())
    print(f"Wrote {len(frame)} labeled wafers to {args.parquet}")
