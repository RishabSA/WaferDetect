from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import yaml

from scripts.perception.evaluate import (
    combo_token,
    metrics_to_dict,
    render_report,
    subset_image_list,
    tiny_token,
    write_subset_yaml,
)

class_names = [f"class_{i}" for i in range(21)]


def make_images(tmp_path: Path) -> Path:
    for name in ("0001_center.jpg", "0481_combo_a+b.jpg", "0461_edge_scratch_tiny.jpg"):
        (tmp_path / name).write_bytes(b"fake-jpeg")
    return tmp_path


def test_subset_image_list_combo(tmp_path: Path) -> None:
    images_dir = make_images(tmp_path)
    assert [p.name for p in subset_image_list(images_dir, combo_token)] == [
        "0481_combo_a+b.jpg"
    ]


def test_subset_image_list_tiny(tmp_path: Path) -> None:
    images_dir = make_images(tmp_path)
    matches = subset_image_list(images_dir, tiny_token)
    assert [p.name for p in matches] == ["0461_edge_scratch_tiny.jpg"]


def test_subset_image_list_empty_returns_empty(tmp_path: Path) -> None:
    (tmp_path / "0001_center.jpg").write_bytes(b"fake-jpeg")
    assert subset_image_list(tmp_path, combo_token) == []


def test_write_subset_yaml(tmp_path: Path) -> None:
    images_dir = make_images(tmp_path)
    base_yaml = tmp_path / "data.yaml"
    base_yaml.write_text(
        yaml.safe_dump(
            {"path": str(tmp_path), "val": "images/val", "names": {0: "center"}}
        )
    )
    subset_yaml = write_subset_yaml(
        base_yaml,
        "combo",
        subset_image_list(images_dir, combo_token),
        tmp_path / "subsets",
    )
    data = yaml.safe_load(subset_yaml.read_text())
    list_file = Path(data["val"])
    assert list_file.is_file()
    assert "0481_combo_a+b.jpg" in list_file.read_text()
    assert data["names"] == {0: "center"}


def fake_metrics() -> SimpleNamespace:
    return SimpleNamespace(
        box=SimpleNamespace(
            map50=0.8,
            map=0.6,
            ap50=np.array([0.9]),
            ap=np.array([0.7]),
            ap_class_index=np.array([4]),
        ),
        seg=SimpleNamespace(
            map50=0.75, map=0.55, ap50=np.array([0.85]), ap=np.array([0.65])
        ),
    )


def test_metrics_to_dict() -> None:
    result = metrics_to_dict(fake_metrics(), class_names)
    assert result["box_map50"] == pytest.approx(0.8)
    assert result["mask_map50"] == pytest.approx(0.75)
    assert result["per_class"]["class_4"]["mask_ap50"] == pytest.approx(0.85)


def test_render_report_contains_sections() -> None:
    report = render_report({"full_test": metrics_to_dict(fake_metrics(), class_names)})
    assert "## full_test" in report
    assert "mask mAP50" in report
    assert "| class_4 |" in report
