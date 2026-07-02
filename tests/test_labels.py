import numpy as np

from waferdetect.datagen.fields import gaussian_blob, lift_pin_field
from waferdetect.datagen.labels import (
    field_mask,
    field_to_polygon,
    mask_iou,
    wafer_to_image,
    yolo_line,
)
from waferdetect.perception.annotations import parse_label_line

grid = 128


def shoelace_area(polygon: list[tuple[float, float]]) -> float:
    xs = np.array([point[0] for point in polygon])
    ys = np.array([point[1] for point in polygon])
    return 0.5 * abs(np.dot(xs, np.roll(ys, 1)) - np.dot(ys, np.roll(xs, 1)))


def test_circle_field_polygon() -> None:
    field = gaussian_blob(grid, 0.0, 0.0, 0.3)
    polygon = field_to_polygon(field)

    assert 3 <= len(polygon) <= 30
    assert all(-1 <= x <= 1 and -1 <= y <= 1 for x, y in polygon)

    expected = np.pi * 0.43**2
    assert abs(shoelace_area(polygon) - expected) / expected < 0.25


def test_multi_component_uses_hull() -> None:
    field = lift_pin_field(grid, np.random.default_rng(0))
    polygon = field_to_polygon(field)

    assert shoelace_area(polygon) > 0.3


def test_rim_touching_field_closes() -> None:
    from waferdetect.datagen.fields import half_wafer_field

    polygon = field_to_polygon(half_wafer_field(grid, np.random.default_rng(1)))
    assert len(polygon) >= 3


def test_wafer_to_image_range() -> None:
    points = wafer_to_image([(-1.0, -1.0), (1.0, 1.0)], wafer_frac=0.97)
    assert points[0] == (0.015, 0.015)
    assert points[1] == (0.985, 0.985)


def test_yolo_line_round_trips_through_parser() -> None:
    line = yolo_line(4, [(0.1, 0.2), (0.3, 0.4), (0.5, 0.6)])
    instance = parse_label_line(line)

    assert instance.class_id == 4
    assert len(instance.polygon) == 3


def test_mask_iou() -> None:
    a = np.zeros((10, 10), dtype=bool)
    b = np.zeros((10, 10), dtype=bool)
    a[:5] = True
    b[3:8] = True

    assert mask_iou(a, a) == 1.0
    assert abs(mask_iou(a, b) - 2 / 8) < 1e-9
    assert mask_iou(a, np.zeros((10, 10), dtype=bool)) == 0.0


def test_field_mask_threshold() -> None:
    field = gaussian_blob(grid, 0.0, 0.0, 0.3)
    mask = field_mask(field)
    assert mask.sum() > 0
    assert mask.dtype == bool
