import numpy as np

from scripts.datagen.fields import field_builders
from scripts.datagen.generator import quantize_dots, sample_dots


def test_sample_dots_follow_field() -> None:
    field = field_builders["center"](128, np.random.default_rng(0))
    dots = sample_dots(field, 300, np.random.default_rng(1))

    assert dots.shape == (300, 2)
    assert np.hypot(dots[:, 0], dots[:, 1]).mean() < 0.5


def test_quantize_snaps_and_dedupes() -> None:
    dots = np.array([[0.101, 0.101], [0.109, 0.108], [-0.5, 0.5]])
    snapped = quantize_dots(dots, die_grid=20)

    assert len(snapped) == 2
    cell = 2.0 / 20
    offsets = (snapped + 1) / cell - 0.5
    assert np.allclose(offsets, offsets.round())
