import numpy as np

from scripts.datagen.fields import disk_coordinates
from scripts.datagen.physics.spincoat import (
    density,
    film_thickness,
    initial_height,
    spincoat_field,
    viscosity,
)

grid = 96


def test_film_thickness_matches_closed_form() -> None:
    spin_speed = 300.0
    duration = 30.0
    k = 2 * density * spin_speed**2 / (3 * viscosity)

    expected = initial_height / np.sqrt(1 + 2 * k * initial_height**2 * duration)
    assert abs(film_thickness(spin_speed, 0.0, duration) - expected) / expected < 1e-4


def test_center_mode_peaks_at_center() -> None:
    field = spincoat_field(grid, np.random.default_rng(0), mode="center")
    row, col = np.unravel_index(field.argmax(), field.shape)
    assert np.hypot(row - grid / 2, col - grid / 2) < grid * 0.2


def test_edge_bead_mass_at_rim() -> None:
    field = spincoat_field(grid, np.random.default_rng(1), mode="edge_bead")
    _, _, rr, _ = disk_coordinates(grid)
    assert field[rr > 0.75].sum() > 0.8 * field.sum()


def test_tilt_mode_mass_off_center() -> None:
    field = spincoat_field(grid, np.random.default_rng(2), mode="tilt")
    xx, yy, _, _ = disk_coordinates(grid)

    total = field.sum()
    centroid_x = (field * xx).sum() / total
    centroid_y = (field * yy).sum() / total
    assert np.hypot(centroid_x, centroid_y) > 0.2


def test_annular_mode_concentrates_in_ring() -> None:
    field = spincoat_field(grid, np.random.default_rng(3), mode="annular")
    _, _, rr, disk = disk_coordinates(grid)

    peak_radius = rr[np.unravel_index(field.argmax(), field.shape)]
    band = disk & (np.abs(rr - peak_radius) < 0.15)
    assert field[band].sum() > 0.7 * field.sum()


def test_field_contract_all_modes() -> None:
    _, _, rr, _ = disk_coordinates(grid)
    for seed, mode in enumerate(("center", "annular", "tilt", "edge_bead")):
        field = spincoat_field(grid, np.random.default_rng(seed), mode=mode)

        assert field.shape == (grid, grid)
        assert field.min() >= 0.0
        assert field.max() > 0.0
        assert float(field[rr > 1.0].max(initial=0.0)) == 0.0
