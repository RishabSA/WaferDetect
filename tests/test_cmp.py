import numpy as np

from scripts.datagen.fields import disk_coordinates
from scripts.datagen.physics.cmp import cmp_field, removal_profile

grid = 96


def test_uniform_pressure_matched_rotation_is_flat() -> None:
    _, _, _, disk = disk_coordinates(grid)
    removal = removal_profile(
        grid,
        mode="center",
        amplitude=0.0,
        velocity_mismatch=0.0,
        rng=np.random.default_rng(0),
    )

    values = removal[disk]
    assert values.max() - values.min() < 1e-9


def test_edge_ring_mode_mass_at_rim() -> None:
    field = cmp_field(grid, np.random.default_rng(1), mode="edge_ring")
    _, _, rr, _ = disk_coordinates(grid)
    assert field[rr > 0.75].sum() > 0.8 * field.sum()


def test_donut_mode_concentrates_in_ring() -> None:
    field = cmp_field(grid, np.random.default_rng(2), mode="donut")
    _, _, rr, disk = disk_coordinates(grid)

    peak_radius = rr[np.unravel_index(field.argmax(), field.shape)]
    band = disk & (np.abs(rr - peak_radius) < 0.15)
    assert field[band].sum() > 0.7 * field.sum()


def test_field_contract_all_modes() -> None:
    _, _, rr, _ = disk_coordinates(grid)
    for seed, mode in enumerate(("center", "edge_ring", "donut")):
        field = cmp_field(grid, np.random.default_rng(seed), mode=mode)

        assert field.shape == (grid, grid)
        assert field.min() >= 0.0
        assert field.max() > 0.0
        assert float(field[rr > 1.0].max(initial=0.0)) == 0.0
