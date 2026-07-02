# Simplifications, deliberate: square exposure fields; failure is binary per shot or per repeated within-field spot
import numpy as np

from scripts.datagen.fields import disk_coordinates


def intra_field_mask(
    grid: int, cell: float, offset: np.ndarray, spot: np.ndarray, spot_radius: float
) -> np.ndarray:
    xx, yy, _, disk = disk_coordinates(grid)

    # Same within-reticle coordinate repeats in every exposure field.
    frac_x = ((xx + 1 - offset[0]) / cell) % 1.0
    frac_y = ((yy + 1 - offset[1]) / cell) % 1.0

    hot = np.hypot(frac_x - spot[0], frac_y - spot[1]) < spot_radius
    return hot & disk


def shot_grid_physics_field(grid: int, rng: np.random.Generator) -> np.ndarray:
    xx, yy, _, disk = disk_coordinates(grid)
    cell = rng.uniform(0.15, 0.30)
    offset = rng.uniform(0, cell, size=2)

    if rng.random() < 0.5:
        spot = rng.uniform(0.2, 0.8, size=2)
        hot = intra_field_mask(grid, cell, offset, spot, rng.uniform(0.1, 0.2))
    else:
        cols = np.floor((xx + 1 - offset[0]) / cell).astype(int)
        rows = np.floor((yy + 1 - offset[1]) / cell).astype(int)
        n_cols = cols.max() - cols.min() + 1
        n_rows = rows.max() - rows.min() + 1
        chosen = rng.random((n_rows, n_cols)) < rng.uniform(0.15, 0.35)
        hot = chosen[rows - rows.min(), cols - cols.min()] & disk

    return np.where(hot, 1.0, 0.0)
