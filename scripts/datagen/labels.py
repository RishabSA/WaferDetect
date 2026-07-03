import numpy as np
from scipy import ndimage
from scipy.spatial import ConvexHull
from skimage.measure import approximate_polygon, find_contours

max_vertices = 30


def field_mask(field: np.ndarray, threshold_frac: float = 0.35) -> np.ndarray:
    return field >= field.max() * threshold_frac


def field_to_polygon(
    field: np.ndarray, threshold_frac: float = 0.35, tolerance_frac: float = 0.01
) -> list[tuple[float, float]]:
    grid = field.shape[0]
    mask = field_mask(field, threshold_frac)
    _, components = ndimage.label(mask)

    if components > 1:
        rows, cols = np.nonzero(mask)
        points = np.stack([cols, rows], axis=1).astype(float)

        # Disjoint clusters
        contour_xy = points[ConvexHull(points).vertices]
    else:
        # Padding closes contours for rim-touching fields like gradient and half-wafer.
        padded = np.pad(mask, 1)
        contour = max(find_contours(padded.astype(float), 0.5), key=len)

        # Single blob
        contour_xy = contour[:, ::-1] - 1.0

    # Douglas–Peucker simplification that deletes vertices that deviate from the shape by less than 2.5 pixels
    # Simplifies the polygon to only the meaningful vertices
    simplified = approximate_polygon(contour_xy, tolerance_frac * grid)
    if np.allclose(simplified[0], simplified[-1]):
        simplified = simplified[:-1]

    if len(simplified) > max_vertices:
        step = int(np.ceil(len(simplified) / max_vertices))
        simplified = simplified[::step]

    # Convert grid indices back to wafer coordinates in [-1, 1]
    return [(x / (grid - 1) * 2 - 1, y / (grid - 1) * 2 - 1) for x, y in simplified]


def wafer_to_image(
    points: list[tuple[float, float]], wafer_frac: float
) -> list[tuple[float, float]]:
    # Maps wafer coordinates to normalized image coordinates
    return [
        (round(0.5 + x * wafer_frac / 2, 6), round(0.5 + y * wafer_frac / 2, 6))
        for x, y in points
    ]


def image_to_wafer(
    points: list[tuple[float, float]], wafer_frac: float
) -> list[tuple[float, float]]:
    return [((x - 0.5) * 2 / wafer_frac, (y - 0.5) * 2 / wafer_frac) for x, y in points]


def yolo_line(class_id: int, polygon: list[tuple[float, float]]) -> str:
    coordinates = " ".join(f"{x:.6f} {y:.6f}" for x, y in polygon)
    return f"{class_id} {coordinates}"


def mask_iou(a: np.ndarray, b: np.ndarray) -> float:
    union = np.logical_or(a, b).sum()

    if union == 0:
        return 0.0

    return float(np.logical_and(a, b).sum() / union)
