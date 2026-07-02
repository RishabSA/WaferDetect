from pathlib import Path

import torch

from scripts.baselines.resnet import WaferDataset, multi_hot


def make_pair(tmp_path: Path, stem: str, lines: str) -> None:
    from PIL import Image

    (tmp_path / "images").mkdir(exist_ok=True)
    (tmp_path / "labels").mkdir(exist_ok=True)
    Image.new("L", (640, 640), 255).save(tmp_path / "images" / f"{stem}.jpg")
    (tmp_path / "labels" / f"{stem}.txt").write_text(lines)


def test_multi_hot(tmp_path: Path) -> None:
    make_pair(
        tmp_path,
        "0001_combo_a+b",
        "4 0.1 0.2 0.3 0.4 0.5 0.6\n17 0.1 0.2 0.3 0.4 0.5 0.6\n",
    )
    target = multi_hot(tmp_path / "labels" / "0001_combo_a+b.txt", n_classes=21)

    assert target.shape == (21,)
    assert target[4] == 1.0 and target[17] == 1.0
    assert target.sum() == 2.0


def test_wafer_dataset_item(tmp_path: Path) -> None:
    make_pair(tmp_path, "0001_center", "0 0.1 0.2 0.3 0.4 0.5 0.6\n")
    dataset = WaferDataset(tmp_path / "images", tmp_path / "labels", n_classes=21)

    image, target = dataset[0]
    assert image.shape == (3, 224, 224)
    assert image.dtype == torch.float32
    assert float(image.max()) <= 1.0
    assert target[0] == 1.0
