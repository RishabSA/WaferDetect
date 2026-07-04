import numpy as np
from matplotlib.path import Path as PolygonPath

from scripts.analytics.diegrid import die_centers, failed_dies
from scripts.datagen.generator import wafer_frac
from scripts.datagen.labels import image_to_wafer

default_die_mm = 6.0


def points_in_polygon(points: np.ndarray, polygon_image: list) -> np.ndarray:
    polygon_wafer = image_to_wafer(polygon_image, wafer_frac)

    # Vectorized point-in-polygon is used to convert the polygon to wafer coordinates first
    return PolygonPath(polygon_wafer).contains_points(points)


def decompose(
    dots: np.ndarray,
    polygons_image: list,
    die_mm: float = default_die_mm,
    die_value: float = 25.0,
) -> dict:
    centers = die_centers(die_mm)
    failed = failed_dies(dots, die_mm)

    region_masks = [points_in_polygon(centers, polygon) for polygon in polygons_image]
    inside_any = np.zeros(len(centers), dtype=bool)
    for mask in region_masks:
        inside_any |= mask

    # Find every die that's outside all detected regions and measures the failure rate there, which is the wafer's random background (failures that would have happened anyway)
    outside = ~inside_any
    background_rate = float(failed[outside].mean()) if outside.any() else 0.0

    regions = []
    for mask in region_masks:
        dies_in = int(mask.sum())
        failed_in = int((failed & mask).sum())

        # Attribute only failures above the wafer's random-background rate
        # Each detection is billed only for its excess
        excess = max(failed_in - background_rate * dies_in, 0.0)
        regions.append(
            {
                "dies": dies_in,
                "failed": failed_in,
                "excess_failed": excess,
                "yield_loss_frac": excess / len(centers),
                "dollars": excess * die_value,
            }
        )

    return {
        "gross_dies": len(centers),
        "failed_dies": int(failed.sum()),
        "background_rate": background_rate,
        "yield_random": 1 - background_rate,
        "regions": regions,
    }


def pareto(items: list[tuple[str, float]]) -> list[tuple[str, float]]:
    totals = {}
    for key, dollars in items:
        totals[key] = totals.get(key, 0.0) + dollars

    return sorted(totals.items(), key=lambda pair: -pair[1])
