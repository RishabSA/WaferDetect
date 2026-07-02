from pathlib import Path

import numpy as np

from scripts.perception.annotations import load_class_names, parse_label_line
from scripts.wm811k.pseudolabel import pseudo_label_line, pseudo_polygon

classes_file = Path("data/raw/classes.txt")


def grid_with_cluster(rows: slice, cols: slice, size: int = 26) -> np.ndarray:
    wafer_map = np.ones((size, size), dtype=np.uint8)
    wafer_map[rows, cols] = 2
    return wafer_map


def polygon_centroid_radius(polygon: list[tuple[float, float]]) -> float:
    xs = [point[0] for point in polygon]
    ys = [point[1] for point in polygon]
    return float(np.hypot(sum(xs) / len(xs), sum(ys) / len(ys)))


def test_edge_class_picks_rim_cluster() -> None:
    wafer_map = grid_with_cluster(slice(10, 16), slice(10, 16))
    wafer_map[1:4, 12:15] = 2

    polygon = pseudo_polygon(wafer_map, "edge_loc")
    assert polygon_centroid_radius(polygon) > 0.5


def test_default_picks_largest_cluster() -> None:
    wafer_map = grid_with_cluster(slice(10, 16), slice(10, 16))
    wafer_map[1:3, 12:14] = 2

    polygon = pseudo_polygon(wafer_map, "center")
    assert polygon_centroid_radius(polygon) < 0.3


def test_collinear_scratch_still_hulls() -> None:
    wafer_map = np.ones((26, 26), dtype=np.uint8)
    wafer_map[13, 4:22] = 2

    polygon = pseudo_polygon(wafer_map, "scratch")
    assert len(polygon) >= 3


def test_near_full_uses_all_and_line_parses() -> None:
    wafer_map = np.full((26, 26), 2, dtype=np.uint8)
    names = load_class_names(classes_file)

    line = pseudo_label_line(wafer_map, "near_full", names)
    instance = parse_label_line(line)
    assert names[instance.class_id] == "near_full"
    assert all(0 <= value <= 1 for point in instance.polygon for value in point)
