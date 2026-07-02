import numpy as np

from scripts.analytics.diegrid import (
    die_centers,
    failed_dies,
    radial_yield,
    wafer_summary,
    zone_yields,
)


def test_gross_count_band_and_monotonic() -> None:
    six = die_centers(6.0)
    three = die_centers(3.0)

    assert 1500 < len(six) < 1886
    assert len(three) > len(six)


def test_single_dot_marks_single_die() -> None:
    failed = failed_dies(np.array([[0.01, 0.01]]))
    assert failed.sum() == 1


def test_no_dots_full_yield() -> None:
    summary = wafer_summary(np.zeros((0, 2)))
    assert summary["failed_dies"] == 0
    assert summary["yield"] == 1.0
    assert summary["gross_dies"] > 1000


def test_radial_and_zone_structure() -> None:
    theta = np.linspace(0, 2 * np.pi, 400, endpoint=False)
    dots = np.stack([0.9 * np.cos(theta), 0.9 * np.sin(theta)], axis=1)

    rates = radial_yield(dots)
    assert len(rates) == 10
    assert rates[-1] + rates[-2] > rates[0] + rates[1]

    zones = zone_yields(dots)
    assert set(zones) == {"center", "mid", "edge"}
    assert zones["center"] > zones["edge"]
