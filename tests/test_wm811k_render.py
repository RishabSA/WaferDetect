from pathlib import Path

import numpy as np
import pandas as pd

from scripts.wm811k.render import die_dots, render_manifest


def make_frame() -> pd.DataFrame:
    wafer_map = np.zeros((10, 10), dtype=np.uint8)
    wafer_map[1:9, 1:9] = 1
    wafer_map[4, 4] = 2
    wafer_map[4, 5] = 2
    return pd.DataFrame(
        {
            "failure_type": ["center"],
            "rows": [10],
            "cols": [10],
            "map": [wafer_map.tobytes()],
        }
    )


def test_die_dots_positions() -> None:
    wafer_map = np.zeros((4, 4), dtype=np.uint8)
    wafer_map[0, 0] = 2
    wafer_map[3, 3] = 2

    dots = die_dots(wafer_map)
    assert dots.shape == (2, 2)
    assert np.allclose(sorted(dots[:, 0]), [-0.75, 0.75])
    assert np.allclose(sorted(dots[:, 1]), [-0.75, 0.75])


def test_render_manifest_writes_named_images(tmp_path: Path) -> None:
    render_manifest(make_frame(), [0], tmp_path, seed=42)

    path = tmp_path / "000000_center.jpg"
    assert path.is_file()

    from PIL import Image

    image = np.asarray(Image.open(path).convert("L"))
    assert image.shape == (640, 640)
    assert image.min() < 128


def test_render_is_deterministic(tmp_path: Path) -> None:
    render_manifest(make_frame(), [0], tmp_path / "a", seed=7)
    render_manifest(make_frame(), [0], tmp_path / "b", seed=7)

    first = (tmp_path / "a" / "000000_center.jpg").read_bytes()
    second = (tmp_path / "b" / "000000_center.jpg").read_bytes()
    assert first == second
