from functools import partial
import numpy as np

from scripts.datagen.physics.cmp import cmp_field
from scripts.datagen.physics.shotgrid import shot_grid_physics_field
from scripts.datagen.physics.spincoat import spincoat_field
from scripts.datagen.physics.thermal import slip_lines_field


def dual_mechanism(
    grid: int, rng: np.random.Generator, spincoat_mode: str, cmp_mode: str
) -> np.ndarray:
    # Spin-coat and CMP non-uniformity can produce the same observable pattern
    if rng.random() < 0.5:
        return spincoat_field(grid, rng, mode=spincoat_mode)

    return cmp_field(grid, rng, mode=cmp_mode)


physics_field_builders = {
    "slip_lines": slip_lines_field,
    "center": partial(dual_mechanism, spincoat_mode="center", cmp_mode="center"),
    "donut": partial(dual_mechanism, spincoat_mode="annular", cmp_mode="donut"),
    "edge_ring": partial(
        dual_mechanism, spincoat_mode="edge_bead", cmp_mode="edge_ring"
    ),
    "gradient": partial(spincoat_field, mode="tilt"),
    "shot_grid": shot_grid_physics_field,
}
