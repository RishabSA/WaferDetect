# Simplifications: Newtonian EBP thinning with a constant evaporation term; non-uniformity enters as parametric deviation modes, not a full radial PDE

import numpy as np
from scipy.integrate import solve_ivp

from scripts.datagen.fields import disk_coordinates

density = 1000.0
viscosity = 0.02
initial_height = 2e-6
window_frac = 0.5
window_softness = 0.1


def film_thickness(spin_speed: float, evaporation: float, duration: float) -> float:
    # Emslie–Bonner–Peck equation: when you spin a wafer coated with viscous resist, centrifugal force thins the film at rate dh/dt = −(2ρω²/3η)·h³
    # h³ means thick films thin fast and the process self-levels, while the ω² says spin speed is the dominant control
    k = 2 * density * spin_speed**2 / (3 * viscosity)
    result = solve_ivp(
        lambda _, height: -k * height**3 - evaporation,
        (0.0, duration),
        [initial_height],
        rtol=1e-10,
        atol=1e-15,
    )

    return float(result.y[0, -1])


def thickness_deviation(
    grid: int, mode: str, amplitude: float, rng: np.random.Generator
) -> np.ndarray:
    xx, yy, rr, disk = disk_coordinates(grid)

    # The ideal EBP film is uniform, so defects are departures from uniformity, modeled as four parametric modes with randomized shapes
    if mode == "center":
        # A dispense hump that didn't spin out
        profile = np.exp(-(rr**2) / (2 * rng.uniform(0.15, 0.3) ** 2))
    elif mode == "annular":
        # A ring-shaped deviation at random radius
        radius = rng.uniform(0.35, 0.6)
        profile = np.exp(-((rr - radius) ** 2) / (2 * rng.uniform(0.06, 0.12) ** 2))
    elif mode == "tilt":
        # A tilted chuck making one side thicker keeps it one-sided so the failure pattern is a gradient lobe, not two opposite lobes
        # Only the thick side leaves the window, producing a one-sided gradient lobe
        phi = rng.uniform(0, 2 * np.pi)
        profile = np.clip(xx * np.cos(phi) + yy * np.sin(phi), 0.0, None)
    elif mode == "edge_bead":
        # The rim excess every real coater fights
        profile = np.exp(-((rr - 1.0) ** 2) / (2 * rng.uniform(0.04, 0.08) ** 2))
    else:
        raise ValueError(f"Unknown spin-coat deviation mode: {mode!r}")

    return amplitude * profile * disk


def deviation_to_probability(deviation: np.ndarray, amplitude: float) -> np.ndarray:
    # Downstream lithography only works if the resist thickness is within tolerance, as dies fail where |deviation| exceeds the window
    scale = abs(amplitude)
    excess = np.abs(deviation) - window_frac * scale

    # The sigmoid's threshold and softness scale relative to the deviation amplitude
    return 1 / (1 + np.exp(-excess / (window_softness * scale)))


def spincoat_field(grid: int, rng: np.random.Generator, mode: str) -> np.ndarray:
    amplitude = rng.uniform(0.5, 1.0)
    deviation = thickness_deviation(grid, mode, amplitude, rng)

    _, _, _, disk = disk_coordinates(grid)
    return deviation_to_probability(deviation, amplitude) * disk
