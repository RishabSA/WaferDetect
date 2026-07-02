from pathlib import Path

import numpy as np
import pytest

from waferdetect.datagen.fields import category_class, disk_coordinates, field_builders
from waferdetect.perception.annotations import load_class_names

classes_file = Path("data/raw/classes.txt")
grid = 128


def test_registry_covers_all_classes() -> None:
    assert len(field_builders) == 24
    assert {category_class(category) for category in field_builders} == set(
        load_class_names(classes_file)
    )


@pytest.mark.parametrize("category", sorted(field_builders))
def test_field_properties(category: str) -> None:
    field = field_builders[category](grid, np.random.default_rng(0))
    _, _, rr, _ = disk_coordinates(grid)

    assert field.shape == (grid, grid)
    assert field.min() >= 0.0
    assert field.max() > 0.0
    assert float(field[rr > 1.0].max(initial=0.0)) == 0.0


def test_center_field_peaks_at_center() -> None:
    field = field_builders["center"](grid, np.random.default_rng(1))
    row, col = np.unravel_index(field.argmax(), field.shape)
    assert abs(row - grid / 2) < grid * 0.1
    assert abs(col - grid / 2) < grid * 0.1


def test_edge_ring_mass_near_rim() -> None:
    field = field_builders["edge_ring"](grid, np.random.default_rng(2))
    _, _, rr, _ = disk_coordinates(grid)
    assert field[rr > 0.8].sum() > 0.9 * field.sum()


def test_half_wafer_covers_about_half() -> None:
    field = field_builders["half_wafer"](grid, np.random.default_rng(3))
    _, _, _, disk = disk_coordinates(grid)
    covered = (field > 0.5).sum() / disk.sum()
    assert 0.3 < covered < 0.7


def test_edge_scratch_sizes_ordered() -> None:
    tiny = field_builders["edge_scratch_tiny"](grid, np.random.default_rng(4))
    large = field_builders["edge_scratch_large"](grid, np.random.default_rng(4))
    assert (tiny > 0.35 * tiny.max()).sum() < (large > 0.35 * large.max()).sum()
