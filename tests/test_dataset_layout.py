import os
from pathlib import Path

import pytest
import yaml

import scripts.perception.dataset as dataset
from scripts.perception.dataset import (
    build_yolo_layout,
    compute_split,
    split_names,
    write_data_yaml,
)

FIXTURE_CLASS_NAMES = [f"class_{i}" for i in range(21)]
FIXTURE_LABEL_LINE = "0 0.1 0.2 0.3 0.4 0.5 0.6\n"


def make_fixture_raw(tmp_path: Path, count: int = 7) -> tuple[Path, Path, list[str]]:
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)
    stems = [f"{i:04d}_center" for i in range(1, count + 1)]
    for stem in stems:
        (images_dir / f"{stem}.jpg").write_bytes(b"fake-jpeg")
        (labels_dir / f"{stem}.txt").write_text(FIXTURE_LABEL_LINE)
    return images_dir, labels_dir, stems


def test_write_data_yaml(tmp_path: Path) -> None:
    yaml_path = write_data_yaml(
        tmp_path, FIXTURE_CLASS_NAMES, {"train": "images/train", "val": "images/val"}
    )
    data = yaml.safe_load(yaml_path.read_text())
    assert data["path"] == str(tmp_path.resolve())
    assert data["train"] == "images/train"
    assert data["names"][0] == "class_0"
    assert len(data["names"]) == 21


def test_build_yolo_layout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    images_dir, labels_dir, stems = make_fixture_raw(tmp_path)
    yolo_dir = tmp_path / "yolo"
    monkeypatch.setattr(dataset, "raw_images_dir", images_dir)
    monkeypatch.setattr(dataset, "raw_labels_dir", labels_dir)
    monkeypatch.setattr(dataset, "yolo_dir", yolo_dir)
    split = compute_split(stems, train_frac=0.70, val_frac=0.15, seed=42)
    yaml_path = build_yolo_layout(split, FIXTURE_CLASS_NAMES)
    assert yaml_path.is_file()
    for name in split_names:
        image_count = len(list((yolo_dir / "images" / name).glob("*.jpg")))
        label_count = len(list((yolo_dir / "labels" / name).glob("*.txt")))
        assert image_count == len(split[name])
        assert label_count == len(split[name])


def test_build_yolo_layout_missing_label_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    images_dir, labels_dir, stems = make_fixture_raw(tmp_path)
    (labels_dir / f"{stems[0]}.txt").unlink()
    monkeypatch.setattr(dataset, "raw_images_dir", images_dir)
    monkeypatch.setattr(dataset, "raw_labels_dir", labels_dir)
    monkeypatch.setattr(dataset, "yolo_dir", tmp_path / "yolo")
    split = compute_split(stems, train_frac=0.70, val_frac=0.15, seed=42)
    with pytest.raises(FileNotFoundError):
        build_yolo_layout(split, FIXTURE_CLASS_NAMES)
