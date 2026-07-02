from pathlib import Path

import pytest

from scripts.perception.annotations import (
    DefectInstance,
    load_class_names,
    load_dataset,
    load_label_file,
    parse_label_line,
)

classes_file = Path("data/raw/classes.txt")
raw_images_dir = Path("data/raw/images")
raw_labels_dir = Path("data/raw/labels")

valid_line = "4 0.1 0.2 0.3 0.4 0.5 0.6"
expected_pair_count = 580


def test_parse_valid_line() -> None:
    instance = parse_label_line(valid_line)
    assert instance == DefectInstance(
        class_id=4, polygon=[(0.1, 0.2), (0.3, 0.4), (0.5, 0.6)]
    )


def test_non_integer_class_raises() -> None:
    with pytest.raises(ValueError):
        parse_label_line("x 0.1 0.2 0.3 0.4 0.5 0.6")


def test_odd_coordinate_count_raises() -> None:
    with pytest.raises(ValueError):
        parse_label_line("4 0.1 0.2 0.3 0.4 0.5 0.6 0.7")


def test_load_class_names_real_file() -> None:
    names = load_class_names(classes_file)
    assert len(names) == 21
    assert names[0] == "center"
    assert names[20] == "double_ring"


def test_empty_label_file_returns_no_instances(tmp_path: Path) -> None:
    empty = tmp_path / "empty.txt"
    empty.write_text("\n")
    assert load_label_file(empty) == []


def test_load_dataset_missing_label_raises(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"
    images_dir.mkdir()
    labels_dir.mkdir()
    (images_dir / "0001_center.jpg").write_bytes(b"fake")
    with pytest.raises(FileNotFoundError):
        load_dataset(images_dir, labels_dir)


def test_load_dataset_real_files() -> None:
    dataset = load_dataset(raw_images_dir, raw_labels_dir)
    assert len(dataset) == expected_pair_count
