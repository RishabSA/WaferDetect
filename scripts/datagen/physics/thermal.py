# Simplifications, deliberate: plane-stress biaxial thermoelasticity from the wafer-mean temperature; constant thermal diffusivity; an effective Schmid factor instead of full tensor projection; CRSS constants are order-of-magnitude, not metrology
import numpy as np
from scipy.ndimage import zoom

from scripts.datagen.fields import curve_band, disk_coordinates

ambient_kelvin = 300.0
youngs_modulus = 1.5e11
poisson_ratio = 0.28
expansion_coeff = 2.6e-6
schmid_factor = 0.5
crss_prefactor = 5.0e6
crss_activation = 1.0e3

solver_grid = 96
alpha = 0.2
rim_radius = 0.94
pin_sigma = 0.05


def masked_laplacian(temperature: np.ndarray, disk: np.ndarray) -> np.ndarray:
    laplacian = np.zeros_like(temperature)

    # Each in-disk neighbor pair contributes equal-and-opposite heat exchange.
    vertical = disk[1:, :] & disk[:-1, :]
    difference = temperature[1:, :] - temperature[:-1, :]
    laplacian[:-1, :] += np.where(vertical, difference, 0.0)
    laplacian[1:, :] -= np.where(vertical, difference, 0.0)

    horizontal = disk[:, 1:] & disk[:, :-1]
    difference = temperature[:, 1:] - temperature[:, :-1]
    laplacian[:, :-1] += np.where(horizontal, difference, 0.0)
    laplacian[:, 1:] -= np.where(horizontal, difference, 0.0)

    return laplacian


def solve_heat(
    grid: int,
    steps: int,
    ramp_per_step: float,
    edge_loss: float,
    pin_positions: np.ndarray | None,
    pin_strength: float,
    spot_center: tuple[float, float] | None = None,
    spot_strength: float = 0.0,
    spot_sigma: float = 0.10,
) -> np.ndarray:
    xx, yy, rr, disk = disk_coordinates(grid)
    temperature = np.full((grid, grid), ambient_kelvin)
    rim = disk & (rr > rim_radius)

    sinks = np.zeros((grid, grid))
    if pin_positions is not None:
        for px, py in pin_positions:
            sinks += pin_strength * np.exp(
                -((xx - px) ** 2 + (yy - py) ** 2) / (2 * pin_sigma**2)
            )

    if spot_center is not None:
        sx, sy = spot_center
        sinks += spot_strength * np.exp(
            -((xx - sx) ** 2 + (yy - sy) ** 2) / (2 * spot_sigma**2)
        )

    for _ in range(steps):
        temperature = temperature + alpha * masked_laplacian(temperature, disk)
        temperature = np.where(disk, temperature + ramp_per_step, temperature)
        temperature = np.where(
            rim, temperature - edge_loss * (temperature - ambient_kelvin), temperature
        )
        temperature = np.where(
            disk, temperature - sinks * (temperature - ambient_kelvin), temperature
        )

    return np.where(disk, temperature, ambient_kelvin)


def thermal_stress(temperature: np.ndarray, disk: np.ndarray) -> np.ndarray:
    mean_temperature = temperature[disk].mean()
    stress = youngs_modulus * expansion_coeff * (mean_temperature - temperature)
    stress = stress / (1 - poisson_ratio)

    return np.where(disk, stress, 0.0)


def slip_probability(
    temperature: np.ndarray, disk: np.ndarray, sharpness: float = 2.0
) -> np.ndarray:
    # Cold regions are tensile in this approximation; compressive hot regions do not seed slip.
    shear = schmid_factor * np.clip(thermal_stress(temperature, disk), 0.0, None)
    critical = crss_prefactor * np.exp(crss_activation / np.maximum(temperature, 1.0))

    margin = (shear - critical) / critical
    return np.where(disk, 1 / (1 + np.exp(-sharpness * margin)), 0.0)


def slip_lines_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    phase = rng.uniform(0, 2 * np.pi)
    angles = phase + np.arange(3) * 2 * np.pi / 3
    pin_radius = rng.uniform(0.50, 0.60)
    pins = np.stack([pin_radius * np.cos(angles), pin_radius * np.sin(angles)], axis=1)

    temperature = solve_heat(
        solver_grid,
        steps=int(rng.integers(150, 400)),
        ramp_per_step=rng.uniform(1.0, 3.0),
        edge_loss=rng.uniform(0.03, 0.15),
        pin_positions=pins,
        pin_strength=rng.uniform(0.02, 0.08),
    )
    _, _, _, solver_disk = disk_coordinates(solver_grid)
    probability = slip_probability(temperature, solver_disk)

    probability = np.clip(zoom(probability, grid / solver_grid, order=1), 0.0, None)
    _, _, _, disk = disk_coordinates(grid)
    probability = np.where(disk, probability, 0.0)

    flat = probability.ravel()
    anchors = rng.choice(flat.size, size=int(rng.integers(3, 7)), p=flat / flat.sum())
    base_angle = rng.uniform(0, np.pi / 2)
    field = np.zeros((grid, grid))

    for anchor in anchors:
        row, col = np.divmod(anchor, grid)
        cx = col / (grid - 1) * 2 - 1
        cy = row / (grid - 1) * 2 - 1
        angle = base_angle + int(rng.integers(0, 2)) * np.pi / 2
        length = rng.uniform(0.15, 0.4)

        t = np.linspace(-length / 2, length / 2, 120)
        points = np.stack([cx + t * np.cos(angle), cy + t * np.sin(angle)], axis=1)
        field += curve_band(grid, points, 0.015)

    return field
