import numpy as np
import pytest

from scripts.analytics.diegrid import die_centers
from scripts.analytics.economics import decompose, pareto, points_in_polygon
from scripts.datagen.labels import image_to_wafer, wafer_to_image

left_half_polygon = [(0.015, 0.015), (0.5, 0.015), (0.5, 0.985), (0.015, 0.985)]


def test_image_to_wafer_round_trips() -> None:
    points = [(-0.8, 0.2), (0.3, -0.5)]
    recovered = image_to_wafer(wafer_to_image(points, 0.97), 0.97)
    assert np.allclose(recovered, points)


def test_points_in_polygon_splits_halves() -> None:
    points = np.array([[-0.5, 0.0], [0.5, 0.0]])
    inside = points_in_polygon(points, left_half_polygon)
    assert inside.tolist() == [True, False]


def test_decompose_attributes_excess() -> None:
    centers = die_centers(6.0)
    left = centers[centers[:, 0] < -0.01]
    right = centers[centers[:, 0] > 0.01]

    dots = np.concatenate([left[:30], right[:10]])
    report = decompose(dots, [left_half_polygon], die_mm=6.0, die_value=25.0)

    region = report["regions"][0]
    assert region["failed"] == 30
    background = report["background_rate"]
    assert background == pytest.approx(10 / len(right), rel=0.2)
    assert region["excess_failed"] == pytest.approx(
        30 - background * region["dies"], rel=1e-6
    )
    assert region["dollars"] == pytest.approx(region["excess_failed"] * 25.0)


def test_pareto_sorts_totals() -> None:
    ranked = pareto([("cmp", 100.0), ("litho", 300.0), ("cmp", 250.0)])
    assert ranked == [("cmp", 350.0), ("litho", 300.0)]
