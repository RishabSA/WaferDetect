from functools import partial
import numpy as np
from scipy.ndimage import gaussian_filter


def disk_coordinates(grid: int) -> tuple:
    axis = np.linspace(-1.0, 1.0, grid)
    xx, yy = np.meshgrid(axis, axis)
    rr = np.hypot(xx, yy)

    return xx, yy, rr, rr <= 1.0


def gaussian_blob(grid: int, cx: float, cy: float, sigma: float) -> np.ndarray:
    xx, yy, _, disk = disk_coordinates(grid)
    return np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma**2)) * disk


def annulus(grid: int, radius: float, width: float) -> np.ndarray:
    _, _, rr, disk = disk_coordinates(grid)
    return np.exp(-((rr - radius) ** 2) / (2 * width**2)) * disk


def angular_mask(grid: int, theta0: float, width: float) -> np.ndarray:
    xx, yy, _, _ = disk_coordinates(grid)
    theta = np.arctan2(yy, xx)

    # Wrapped angular difference keeps the window continuous across +/- pi.
    delta = np.angle(np.exp(1j * (theta - theta0)))
    return np.exp(-(delta**2) / (2 * width**2))


def curve_band(
    grid: int, points: np.ndarray, sigma: float, weights: np.ndarray | None = None
) -> np.ndarray:
    field = np.zeros((grid, grid))
    cols = np.clip(
        ((points[:, 0] + 1) / 2 * (grid - 1)).round().astype(int), 0, grid - 1
    )
    rows = np.clip(
        ((points[:, 1] + 1) / 2 * (grid - 1)).round().astype(int), 0, grid - 1
    )
    field[rows, cols] = 1.0 if weights is None else weights

    field = gaussian_filter(field, sigma * grid / 2)
    _, _, _, disk = disk_coordinates(grid)
    return field * disk


# There are 24 builder functions that take in a grid and draw their own randomized parameters


def center_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    return gaussian_blob(grid, 0.0, 0.0, rng.uniform(0.15, 0.35))


def donut_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    return annulus(grid, rng.uniform(0.35, 0.60), rng.uniform(0.08, 0.18))


def edge_ring_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    return annulus(grid, rng.uniform(0.90, 0.97), rng.uniform(0.03, 0.08))


def edge_loc_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    theta = rng.uniform(0, 2 * np.pi)
    radius = rng.uniform(0.85, 0.95)
    cx, cy = radius * np.cos(theta), radius * np.sin(theta)
    return gaussian_blob(grid, cx, cy, rng.uniform(0.08, 0.18))


def scratch_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    angle = rng.uniform(0, np.pi)
    cx, cy = rng.uniform(-0.5, 0.5, size=2)
    length = rng.uniform(0.5, 1.4)

    t = np.linspace(-length / 2, length / 2, 200)
    points = np.stack([cx + t * np.cos(angle), cy + t * np.sin(angle)], axis=1)
    return curve_band(grid, points, rng.uniform(0.015, 0.04))


def random_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    _, _, _, disk = disk_coordinates(grid)
    return disk.astype(float)


def loc_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    theta = rng.uniform(0, 2 * np.pi)
    radius = rng.uniform(0.2, 0.7)
    cx, cy = radius * np.cos(theta), radius * np.sin(theta)
    return gaussian_blob(grid, cx, cy, rng.uniform(0.08, 0.20))


def near_full_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    return random_field(grid, rng)


def swirl_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    turns = rng.uniform(1.5, 3.0)
    theta = np.linspace(0, turns * 2 * np.pi, 600)
    radius = theta / theta.max() * rng.uniform(0.7, 0.95)
    phase = rng.uniform(0, 2 * np.pi)

    points = np.stack(
        [radius * np.cos(theta + phase), radius * np.sin(theta + phase)], axis=1
    )
    return curve_band(grid, points, rng.uniform(0.02, 0.05))


def radial_spokes_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    _, _, rr, disk = disk_coordinates(grid)
    count = int(rng.integers(3, 9))
    phase = rng.uniform(0, 2 * np.pi)
    width = rng.uniform(0.06, 0.15)

    field = sum(
        angular_mask(grid, phase + index * 2 * np.pi / count, width)
        for index in range(count)
    )
    return field * (rr > 0.15) * disk


def shot_grid_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    xx, yy, _, disk = disk_coordinates(grid)
    cell = rng.uniform(0.15, 0.30)
    cols = np.floor((xx + 1) / cell).astype(int)
    rows = np.floor((yy + 1) / cell).astype(int)

    n_cols = cols.max() + 1
    n_rows = rows.max() + 1
    chosen = rng.random((n_rows, n_cols)) < rng.uniform(0.15, 0.35)
    return np.where(chosen[rows, cols] & disk, 1.0, 0.0)


def crescent_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    ring = annulus(grid, rng.uniform(0.4, 0.7), rng.uniform(0.08, 0.15))
    return ring * angular_mask(grid, rng.uniform(0, 2 * np.pi), rng.uniform(0.3, 0.7))


def half_wafer_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    xx, yy, _, disk = disk_coordinates(grid)
    phi = rng.uniform(0, 2 * np.pi)
    signed = xx * np.cos(phi) + yy * np.sin(phi)
    softness = rng.uniform(0.02, 0.08)
    return (1 / (1 + np.exp(-signed / softness))) * disk


def wedge_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    _, _, _, disk = disk_coordinates(grid)
    window = angular_mask(grid, rng.uniform(0, 2 * np.pi), rng.uniform(0.25, 0.8))
    return window * disk


def comet_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    theta = rng.uniform(0, 2 * np.pi)
    head = np.array([np.cos(theta), np.sin(theta)]) * rng.uniform(0.1, 0.5)
    tail_dir = rng.uniform(0, 2 * np.pi)
    length = rng.uniform(0.3, 0.7)

    t = np.linspace(0, length, 200)
    points = head + t[:, None] * np.array([np.cos(tail_dir), np.sin(tail_dir)])
    weights = np.exp(-t / (0.35 * length))

    tail = curve_band(grid, points, rng.uniform(0.02, 0.04), weights)
    return tail + gaussian_blob(grid, head[0], head[1], rng.uniform(0.05, 0.10))


def edge_scratch_field(
    grid: int, rng: np.random.Generator, min_len: float, max_len: float
) -> np.ndarray:
    theta = rng.uniform(0, 2 * np.pi)
    start = np.array([np.cos(theta), np.sin(theta)]) * 0.93
    direction = theta + np.pi / 2 + rng.uniform(-0.4, 0.4)
    length = rng.uniform(min_len, max_len)

    t = np.linspace(0, length, 200)
    points = start + t[:, None] * np.array([np.cos(direction), np.sin(direction)])
    return curve_band(grid, points, rng.uniform(0.012, 0.03))


def lift_pin_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    phase = rng.uniform(0, 2 * np.pi)
    pin_radius = rng.uniform(0.50, 0.60)
    sigma = rng.uniform(0.04, 0.08)

    return sum(
        gaussian_blob(
            grid,
            pin_radius * np.cos(phase + index * 2 * np.pi / 3),
            pin_radius * np.sin(phase + index * 2 * np.pi / 3),
            sigma,
        )
        for index in range(3)
    )


def bullseye_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    blob = gaussian_blob(grid, 0.0, 0.0, rng.uniform(0.10, 0.20))
    return blob + annulus(grid, rng.uniform(0.45, 0.70), rng.uniform(0.06, 0.12))


def gradient_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    xx, yy, _, disk = disk_coordinates(grid)
    phi = rng.uniform(0, 2 * np.pi)
    ramp = np.clip((xx * np.cos(phi) + yy * np.sin(phi) + 1) / 2, 0.0, 1.0)
    return ramp ** rng.uniform(1.5, 3.0) * disk


def slip_lines_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    base = rng.uniform(0, np.pi / 2)
    field = np.zeros((grid, grid))

    for _ in range(int(rng.integers(3, 7))):
        angle = base + int(rng.integers(0, 2)) * np.pi / 2
        anchor_theta = rng.uniform(0, 2 * np.pi)
        anchor = np.array([np.cos(anchor_theta), np.sin(anchor_theta)]) * rng.uniform(
            0.6, 0.9
        )
        length = rng.uniform(0.15, 0.4)

        t = np.linspace(-length / 2, length / 2, 120)
        points = anchor + t[:, None] * np.array([np.cos(angle), np.sin(angle)])
        field += curve_band(grid, points, 0.015)

    return field


def double_ring_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    r_inner = rng.uniform(0.30, 0.50)
    r_outer = min(r_inner + rng.uniform(0.18, 0.32), 0.95)
    width = rng.uniform(0.04, 0.08)
    return annulus(grid, r_inner, width) + annulus(grid, r_outer, width)


field_builders = {
    "center": center_field,
    "donut": donut_field,
    "edge_ring": edge_ring_field,
    "edge_loc": edge_loc_field,
    "scratch": scratch_field,
    "random": random_field,
    "loc": loc_field,
    "near_full": near_full_field,
    "swirl": swirl_field,
    "radial_spokes": radial_spokes_field,
    "shot_grid": shot_grid_field,
    "crescent": crescent_field,
    "half_wafer": half_wafer_field,
    "wedge": wedge_field,
    "comet": comet_field,
    "edge_scratch_tiny": partial(edge_scratch_field, min_len=0.08, max_len=0.16),
    "edge_scratch_small": partial(edge_scratch_field, min_len=0.16, max_len=0.28),
    "edge_scratch_medium": partial(edge_scratch_field, min_len=0.28, max_len=0.45),
    "edge_scratch_large": partial(edge_scratch_field, min_len=0.45, max_len=0.70),
    "lift_pin": lift_pin_field,
    "bullseye": bullseye_field,
    "gradient": gradient_field,
    "slip_lines": slip_lines_field,
    "double_ring": double_ring_field,
}


def category_class(category: str) -> str:
    return "edge_scratch" if category.startswith("edge_scratch") else category
