import numpy as np
from skimage.transform import radon

raster_size = 64
n_angles = 180
straightness_tolerance = 0.02
concentric_center_tolerance = 0.3


def radon_orientation(points: np.ndarray) -> float:
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

    # Skimage peaks when the projection angle is perpendicular to the line.
    peak = angles[int(sinogram.std(axis=0).argmax())]
    return float((peak - 90.0) % 180.0)


def line_deviation(points: np.ndarray) -> float:
    centered = points - points.mean(axis=0)
    _, singular, _ = np.linalg.svd(centered, full_matrices=False)
    return float(singular[1] / np.sqrt(len(points)))


def circle_fit(points: np.ndarray) -> tuple[float, float, float]:
    design = np.column_stack([points[:, 0], points[:, 1], np.ones(len(points))])
    target = (points**2).sum(axis=1)
    (a, b, c), *_ = np.linalg.lstsq(design, target, rcond=None)

    cx = a / 2
    cy = b / 2
    radius = float(np.sqrt(max(c + cx**2 + cy**2, 0.0)))
    return float(cx), float(cy), radius


def scratch_verdict(points: np.ndarray) -> dict:
    orientation = radon_orientation(points)

    if line_deviation(points) < straightness_tolerance:
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

    cx, cy, radius = circle_fit(points)
    concentric = np.hypot(cx, cy) < concentric_center_tolerance
    return {
        "verdict": "cmp_rotational" if concentric else "off_axis_arc",
        "orientation_deg": orientation,
        "radius_of_curvature": radius,
        "arc_center": (cx, cy),
        "entry_bearing_deg": None,
    }
