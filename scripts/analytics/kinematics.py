import numpy as np
from skimage.transform import radon

raster_size = 256
n_angles = 180
straightness_tolerance = 0.05
concentric_center_tolerance = 0.3
arc_chord_ratio_limit = 2.0


def radon_orientation(points: np.ndarray) -> float:
    # Rasterize the points and Radon-transforms at 1 degree steps
    grid = np.zeros((raster_size, raster_size))

    cols = np.clip(
        ((points[:, 0] + 1) / 2 * (raster_size - 1)).astype(int), 0, raster_size - 1
    )
    rows = np.clip(
        ((points[:, 1] + 1) / 2 * (raster_size - 1)).astype(int), 0, raster_size - 1
    )
    grid[rows, cols] = 1.0

    angles = np.linspace(0.0, 180.0, n_angles, endpoint=False)
    sinogram = radon(grid, theta=angles)

    # For the transform, a line of points is projected along its own direction and collapses into one enormous bin
    # Skimage peaks when the projection angle is perpendicular to the line
    peak = angles[int(sinogram.std(axis=0).argmax())]
    return float((peak - 90.0) % 180.0)


def line_deviation(points: np.ndarray) -> float:
    centered = points - points.mean(axis=0)

    # SVD of the centered cloud because the first singular direction is the best-fit line, and the second singular value is exactly the sum of squared perpendicular distances from it
    _, singular, _ = np.linalg.svd(centered, full_matrices=False)
    return float(singular[1] / np.sqrt(len(points)))


def circle_fit(points: np.ndarray) -> tuple[float, float, float]:
    # The Kasa method is an observation that x² + y² = ax + by + c is linear in (a, b, c), so one least-squares solve yields center (a/2, b/2) and radius
    design = np.column_stack([points[:, 0], points[:, 1], np.ones(len(points))])
    target = (points**2).sum(axis=1)
    (a, b, c), *_ = np.linalg.lstsq(design, target, rcond=None)

    cx = a / 2
    cy = b / 2
    radius = float(np.sqrt(max(c + cx**2 + cy**2, 0.0)))
    return float(cx), float(cy), radius


def scratch_verdict(points: np.ndarray) -> dict:
    orientation = radon_orientation(points)
    deviation = line_deviation(points)
    cx, cy, radius = circle_fit(points)
    chord = np.linalg.norm(points[-1] - points[0])
    arc_like = radius > 0 and chord / radius <= arc_chord_ratio_limit

    if deviation < straightness_tolerance and not arc_like:
        rim_most = points[np.hypot(points[:, 0], points[:, 1]).argmax()]
        return {
            "verdict": "handling_linear",
            "orientation_deg": orientation,
            "radius_of_curvature": None,
            "arc_center": None,
            "entry_bearing_deg": float(
                np.degrees(np.arctan2(rim_most[1], rim_most[0])) % 360
            ),
        }

    concentric = np.hypot(cx, cy) < concentric_center_tolerance
    return {
        "verdict": "cmp_rotational" if concentric else "off_axis_arc",
        "orientation_deg": orientation,
        "radius_of_curvature": radius,
        "arc_center": (cx, cy),
        "entry_bearing_deg": None,
    }
