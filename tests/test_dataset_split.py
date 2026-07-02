from pathlib import Path

import pytest

import waferdetect.perception.dataset as dataset
from waferdetect.perception.dataset import (
    split_names,
    compute_split,
    read_manifests,
    stem_category,
    write_manifests,
)

RAW_IMAGES_DIR = Path("data/raw/images")
SEED = 42
TRAIN_FRAC = 0.70
VAL_FRAC = 0.15
EXPECTED_COUNTS = {"train": 406, "val": 87, "test": 87}
EXPECTED_TOTAL = 580


def real_stems() -> list[str]:
    return sorted(path.stem for path in RAW_IMAGES_DIR.glob("*.jpg"))


def test_stem_category_variants() -> None:
    assert stem_category("0001_center") == "center"
    assert stem_category("0461_edge_scratch_tiny") == "edge_scratch_tiny"
    assert stem_category("0481_combo_half_wafer+donut") == "combo"


def test_stem_category_rejects_bad_format() -> None:
    with pytest.raises(ValueError, match="stem format"):
        stem_category("no_leading_number")


def test_split_is_deterministic() -> None:
    stems = real_stems()
    first = compute_split(stems, train_frac=TRAIN_FRAC, val_frac=VAL_FRAC, seed=SEED)
    second = compute_split(stems, train_frac=TRAIN_FRAC, val_frac=VAL_FRAC, seed=SEED)
    assert first == second


def test_split_counts_and_disjointness() -> None:
    split = compute_split(real_stems(), train_frac=TRAIN_FRAC, val_frac=VAL_FRAC, seed=SEED)
    for name in split_names:
        assert len(split[name]) == EXPECTED_COUNTS[name]
    combined = split["train"] + split["val"] + split["test"]
    assert len(set(combined)) == EXPECTED_TOTAL


def test_every_category_in_every_split() -> None:
    stems = real_stems()
    expected_categories = {stem_category(stem) for stem in stems}
    split = compute_split(stems, train_frac=TRAIN_FRAC, val_frac=VAL_FRAC, seed=SEED)
    for name in split_names:
        assert {stem_category(stem) for stem in split[name]} == expected_categories


def test_tiny_category_does_not_raise() -> None:
    split = compute_split(
        ["0001_center", "0002_center"], train_frac=TRAIN_FRAC, val_frac=VAL_FRAC, seed=SEED
    )
    combined = split["train"] + split["val"] + split["test"]
    assert sorted(combined) == ["0001_center", "0002_center"]


def test_manifests_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dataset, "splits_dir", tmp_path)
    split = {"train": ["a_center"], "val": ["b_center"], "test": ["c_center"]}
    write_manifests(split)
    assert read_manifests() == split


def test_read_manifests_missing_file_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(dataset, "splits_dir", tmp_path)
    with pytest.raises(FileNotFoundError):
        read_manifests()
