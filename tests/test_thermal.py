import numpy as np

from scripts.datagen.fields import disk_coordinates
from scripts.datagen.physics.thermal import (
    ambient_kelvin,
    masked_laplacian,
    slip_lines_field,
    slip_probability,
    solve_heat,
    thermal_stress,
)

grid = 64


def pin_ring(phase: float = 0.0, radius: float = 0.55) -> np.ndarray:
    angles = phase + np.arange(3) * 2 * np.pi / 3
    return np.stack([radius * np.cos(angles), radius * np.sin(angles)], axis=1)


def test_masked_laplacian_conserves_heat() -> None:
    _, _, _, disk = disk_coordinates(grid)
    rng = np.random.default_rng(0)
    temperature = np.where(
        disk, ambient_kelvin + rng.uniform(0, 50, (grid, grid)), ambient_kelvin
    )

    stepped = temperature + 0.2 * masked_laplacian(temperature, disk)
    assert abs(stepped[disk].sum() - temperature[disk].sum()) < 1e-6


def test_uniform_ramp_no_loss_stays_uniform() -> None:
    _, _, _, disk = disk_coordinates(grid)
    temperature = solve_heat(
        grid,
        steps=50,
        ramp_per_step=2.0,
        edge_loss=0.0,
        pin_positions=None,
        pin_strength=0.0,
    )

    values = temperature[disk]
    assert values.max() - values.min() < 1e-6
    assert values.mean() > ambient_kelvin


def test_center_cold_spot_is_point_symmetric() -> None:
    temperature = solve_heat(
        grid,
        steps=100,
        ramp_per_step=2.0,
        edge_loss=0.0,
        pin_positions=None,
        pin_strength=0.0,
        spot_center=(0.0, 0.0),
        spot_strength=0.05,
    )
    assert np.allclose(temperature, np.rot90(temperature, 2), atol=1e-6)


def test_uniform_temperature_gives_zero_stress() -> None:
    _, _, _, disk = disk_coordinates(grid)
    temperature = np.where(disk, 600.0, ambient_kelvin)
    stress = thermal_stress(temperature, disk)
    assert abs(stress[disk]).max() < 1e-9


def test_slip_probability_peaks_at_pins() -> None:
    xx, yy, _, disk = disk_coordinates(grid)
    pins = pin_ring()
    temperature = solve_heat(
        grid,
        steps=200,
        ramp_per_step=2.0,
        edge_loss=0.05,
        pin_positions=pins,
        pin_strength=0.05,
    )
    probability = slip_probability(temperature, disk)

    near_pin = np.hypot(xx - pins[0, 0], yy - pins[0, 1]) < 0.12
    far = disk & (np.hypot(xx, yy) < 0.25)
    assert probability[near_pin & disk].mean() > probability[far].mean()


def test_slip_lines_field_contract() -> None:
    field = slip_lines_field(128, np.random.default_rng(0))
    _, _, rr, _ = disk_coordinates(128)

    assert field.shape == (128, 128)
    assert field.min() >= 0.0
    assert field.max() > 0.0
    assert float(field[rr > 1.0].max(initial=0.0)) == 0.0
