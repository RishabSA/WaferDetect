import numpy as np
import pytest

from scripts.analytics.yieldmodels import (
    estimate_alpha,
    estimate_defect_density,
    negative_binomial_yield,
    poisson_yield,
    quadrat_counts,
)


def test_poisson_round_trip() -> None:
    die_area = 36.0
    density = 0.002
    failed_fraction = 1 - poisson_yield(density, die_area)
    assert estimate_defect_density(failed_fraction, die_area) == pytest.approx(density)


def test_negative_binomial_limits_to_poisson() -> None:
    poisson = poisson_yield(0.002, 36.0)
    assert negative_binomial_yield(0.002, 36.0, alpha=1e6) == pytest.approx(
        poisson, rel=1e-3
    )
    assert negative_binomial_yield(0.002, 36.0, alpha=0.5) > poisson


def test_alpha_estimates() -> None:
    assert estimate_alpha(np.array([5.0, 5.0, 5.0, 5.0])) is None

    clustered = np.array([20.0, 0.0, 0.0, 0.0])
    assert estimate_alpha(clustered) == pytest.approx(25.0 / 70.0)


def test_quadrat_counts_cover_dots() -> None:
    rng = np.random.default_rng(0)
    theta = rng.uniform(0, 2 * np.pi, 300)
    radius = np.sqrt(rng.uniform(0, 1, 300)) * 0.7
    dots = np.stack([radius * np.cos(theta), radius * np.sin(theta)], axis=1)

    counts = quadrat_counts(dots)
    assert counts.sum() == 300
