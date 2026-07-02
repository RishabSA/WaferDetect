# Simplifications, deliberate: Preston removal with parametric pressure profiles and a linear relative-velocity mismatch; removal deviation stands in for over/under-polish
import numpy as np

from scripts.datagen.fields import disk_coordinates
from scripts.datagen.physics.spincoat import deviation_to_probability


def removal_profile(
    grid: int,
    mode: str,
    amplitude: float,
    velocity_mismatch: float,
    rng: np.random.Generator,
) -> np.ndarray:
    _, _, rr, disk = disk_coordinates(grid)

    if mode == "center":
        pressure = 1.0 + amplitude * np.exp(
            -(rr**2) / (2 * rng.uniform(0.15, 0.3) ** 2)
        )
    elif mode == "edge_ring":
        pressure = 1.0 + amplitude * np.exp(
            -((rr - 1.0) ** 2) / (2 * rng.uniform(0.04, 0.08) ** 2)
        )
    elif mode == "donut":
        radius = rng.uniform(0.35, 0.6)
        pressure = 1.0 + amplitude * np.exp(
            -((rr - radius) ** 2) / (2 * rng.uniform(0.06, 0.12) ** 2)
        )
    else:
        raise ValueError(f"Unknown CMP pressure mode: {mode!r}")

    velocity = 1.0 + velocity_mismatch * rr
    return pressure * velocity * disk


def cmp_field(grid: int, rng: np.random.Generator, mode: str) -> np.ndarray:
    amplitude = rng.uniform(0.5, 1.0)
    removal = removal_profile(grid, mode, amplitude, rng.uniform(0.0, 0.2), rng)

    _, _, _, disk = disk_coordinates(grid)
    deviation = np.where(disk, removal - removal[disk].mean(), 0.0)
    return deviation_to_probability(deviation, amplitude) * disk
