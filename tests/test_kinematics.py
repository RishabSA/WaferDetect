import numpy as np

from scripts.analytics.kinematics import (
    circle_fit,
    line_deviation,
    radon_orientation,
    scratch_verdict,
)


def arc_points(cx: float, cy: float, radius: float, start: float, stop: float) -> np.ndarray:
    theta = np.linspace(start, stop, 80)
    return np.stack([cx + radius * np.cos(theta), cy + radius * np.sin(theta)], axis=1)


def test_orientation_horizontal_and_vertical() -> None:
    t = np.linspace(-0.7, 0.7, 100)
    horizontal = np.stack([t, np.zeros_like(t)], axis=1)
    vertical = np.stack([np.zeros_like(t), t], axis=1)

    assert abs(radon_orientation(horizontal) - 0.0) < 5.0
    assert abs(radon_orientation(vertical) - 90.0) < 5.0


def test_straight_chord_is_handling() -> None:
    t = np.linspace(-0.6, 0.6, 100)
    points = np.stack([t, 0.3 + 0.001 * np.sin(t * 40)], axis=1)

    assert line_deviation(points) < 0.02
    result = scratch_verdict(points)
    assert result["verdict"] == "handling_linear"
    assert result["entry_bearing_deg"] is not None


def test_concentric_arc_is_cmp() -> None:
    points = arc_points(0.0, 0.0, 0.55, 0.2, 1.8)
    cx, cy, radius = circle_fit(points)

    assert abs(radius - 0.55) < 0.02
    assert np.hypot(cx, cy) < 0.05
    assert scratch_verdict(points)["verdict"] == "cmp_rotational"


def test_off_axis_arc() -> None:
    points = arc_points(0.6, 0.1, 0.25, 0.5, 2.5)
    assert scratch_verdict(points)["verdict"] == "off_axis_arc"
