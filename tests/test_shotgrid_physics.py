import numpy as np

from scripts.datagen.fields import disk_coordinates
from scripts.datagen.physics.shotgrid import intra_field_mask, shot_grid_physics_field

grid = 128


def test_intra_field_mask_repeats_with_cell_period() -> None:
    period_grid = 129
    cell = 0.25
    mask = intra_field_mask(
        period_grid,
        cell,
        offset=np.array([0.1, 0.05]),
        spot=np.array([0.5, 0.5]),
        spot_radius=0.15,
    )

    shift = 16
    inner = slice(shift, period_grid - shift)
    shifted = np.roll(np.roll(mask, shift, axis=0), shift, axis=1)
    agreement = (mask[inner, inner] == shifted[inner, inner]).mean()
    assert agreement > 0.95


def test_physics_field_contract() -> None:
    _, _, rr, _ = disk_coordinates(grid)
    for seed in range(4):
        field = shot_grid_physics_field(grid, np.random.default_rng(seed))

        assert field.shape == (grid, grid)
        assert field.min() >= 0.0
        assert field.max() > 0.0
        assert float(field[rr > 1.0].max(initial=0.0)) == 0.0


def test_field_values_are_cellwise() -> None:
    field = shot_grid_physics_field(grid, np.random.default_rng(1))
    assert len(np.unique(field)) <= 3
