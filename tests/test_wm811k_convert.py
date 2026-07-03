from pathlib import Path
import importlib
import sys

import numpy as np
import pandas as pd

from scripts.wm811k.convert import (
    convert,
    flatten_label,
    install_legacy_pandas_pickle_aliases,
    load_map,
    read_pickle_compat,
    wm811k_class_map,
)


def make_fake_pickle(tmp_path: Path) -> Path:
    raw = pd.DataFrame(
        {
            "waferMap": [
                np.array([[0, 1, 2], [1, 2, 1], [0, 1, 0]]),
                np.array([[1, 1], [1, 1]]),
                np.array([[2, 1], [1, 2]]),
            ],
            "failureType": [np.array([["Center"]]), np.array([]), np.array([["none"]])],
            "lotName": ["lot1", "lot2", "lot3"],
        }
    )
    path = tmp_path / "fake.pkl"
    raw.to_pickle(path)
    return path


def test_flatten_label_handles_nesting() -> None:
    assert flatten_label(np.array([["Edge-Ring"]])) == "Edge-Ring"
    assert flatten_label(np.array([])) is None


def test_class_map_is_complete() -> None:
    assert set(wm811k_class_map) == {
        "Center",
        "Donut",
        "Edge-Ring",
        "Edge-Loc",
        "Scratch",
        "Random",
        "Loc",
        "Near-full",
        "none",
    }
    assert wm811k_class_map["Edge-Ring"] == "edge_ring"


def test_legacy_pandas_pickle_aliases() -> None:
    for name in tuple(sys.modules):
        if name.startswith("pandas.indexes"):
            sys.modules.pop(name)

    install_legacy_pandas_pickle_aliases()
    legacy = importlib.import_module("pandas.indexes")
    numeric = importlib.import_module("pandas.indexes.numeric")

    assert legacy.Index is pd.Index
    assert numeric.Int64Index is pd.Index


def test_read_pickle_compat_handles_python2_string_encoding(tmp_path: Path) -> None:
    path = tmp_path / "py2.pkl"
    path.write_bytes(b"S'\\x9a'\np0\n.")

    assert read_pickle_compat(path) == "\x9a"


def test_convert_filters_and_round_trips(tmp_path: Path) -> None:
    frame = convert(make_fake_pickle(tmp_path), tmp_path / "labeled.parquet")

    assert list(frame["failure_type"]) == ["center", "none"]
    assert list(frame.index) == [0, 1]

    reloaded = pd.read_parquet(tmp_path / "labeled.parquet")
    wafer_map = load_map(reloaded.iloc[0])
    assert wafer_map.shape == (3, 3)
    assert wafer_map[0, 2] == 2
    assert wafer_map.dtype == np.uint8
