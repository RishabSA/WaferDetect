from pathlib import Path

import yaml

from scripts.datagen.layout import build_layout


def make_generated(tmp_path: Path, count: int = 20) -> Path:
    generated = tmp_path / "generated"
    (generated / "images").mkdir(parents=True)
    (generated / "labels").mkdir(parents=True)

    for index in range(1, count + 1):
        category = "donut" if index % 2 else "scratch"
        stem = f"{index:04d}_{category}"
        (generated / "images" / f"{stem}.jpg").write_bytes(b"fake-jpeg")
        (generated / "labels" / f"{stem}.txt").write_text("0 0.1 0.2 0.3 0.4 0.5 0.6\n")

    return generated


def test_build_layout_splits_and_yaml(tmp_path: Path) -> None:
    generated = make_generated(tmp_path)
    out_dir = tmp_path / "yolo"

    yaml_path = build_layout(generated, out_dir, val_frac=0.2, seed=42)
    data = yaml.safe_load(yaml_path.read_text())

    train = list((out_dir / "images" / "train").glob("*.jpg"))
    val = list((out_dir / "images" / "val").glob("*.jpg"))
    assert len(train) + len(val) == 20
    assert len(val) == 4
    assert data["test"].endswith("data/yolo/images/test")
    assert len(list((out_dir / "labels" / "train").glob("*.txt"))) == len(train)


def test_build_layout_limit_is_deterministic(tmp_path: Path) -> None:
    generated = make_generated(tmp_path)

    first = build_layout(generated, tmp_path / "a", val_frac=0.2, seed=7, limit=10)
    second = build_layout(generated, tmp_path / "b", val_frac=0.2, seed=7, limit=10)

    stems_a = sorted(
        path.stem for path in (tmp_path / "a" / "images" / "train").glob("*.jpg")
    )
    stems_b = sorted(
        path.stem for path in (tmp_path / "b" / "images" / "train").glob("*.jpg")
    )
    assert stems_a == stems_b
    assert first.name == second.name == "data.yaml"
