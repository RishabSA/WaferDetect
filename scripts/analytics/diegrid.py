import numpy as np

default_wafer_radius_mm = 150.0
edge_exclusion_mm = 3.0
default_die_mm = 6.0
radial_bins = 10


def die_centers(
    die_mm: float = default_die_mm,
    wafer_radius_mm: float = default_wafer_radius_mm,
) -> np.ndarray:
    die = die_mm / wafer_radius_mm
    usable = (wafer_radius_mm - edge_exclusion_mm) / wafer_radius_mm

    count = int(np.floor(2.0 / die))
    span = count * die
    axis = -span / 2 + die * (np.arange(count) + 0.5)
    xx, yy = np.meshgrid(axis, axis)

    # Worst-corner check: the whole die square must fit inside the usable radius
    corner = np.hypot(np.abs(xx) + die / 2, np.abs(yy) + die / 2)
    keep = corner <= usable

    return np.stack([xx[keep], yy[keep]], axis=1)


def failed_dies(
    dots: np.ndarray,
    die_mm: float = default_die_mm,
    wafer_radius_mm: float = default_wafer_radius_mm,
) -> np.ndarray:
    centers = die_centers(die_mm, wafer_radius_mm)
    if len(dots) == 0:
        return np.zeros(len(centers), dtype=bool)

    die = die_mm / wafer_radius_mm

    # |dot − center| <= die / 2 is computed along both axes, and a die is counted as failed if any dot lands in it
    inside_x = np.abs(dots[None, :, 0] - centers[:, None, 0]) <= die / 2
    inside_y = np.abs(dots[None, :, 1] - centers[:, None, 1]) <= die / 2

    return (inside_x & inside_y).any(axis=1)


def wafer_summary(
    dots: np.ndarray,
    die_mm: float = default_die_mm,
    wafer_radius_mm: float = default_wafer_radius_mm,
) -> dict:
    failed = failed_dies(dots, die_mm, wafer_radius_mm)
    gross = len(failed)
    return {
        "gross_dies": gross,
        "failed_dies": int(failed.sum()),
        "yield": float(1 - failed.sum() / gross),
    }


def radial_yield(
    dots: np.ndarray,
    die_mm: float = default_die_mm,
    bins: int = radial_bins,
    wafer_radius_mm: float = default_wafer_radius_mm,
) -> list[float]:
    centers = die_centers(die_mm, wafer_radius_mm)
    failed = failed_dies(dots, die_mm, wafer_radius_mm)
    radius = np.hypot(centers[:, 0], centers[:, 1])

    edges = np.linspace(0.0, radius.max() + 1e-9, bins + 1)
    rates = []
    for low, high in zip(edges[:-1], edges[1:], strict=True):
        band = (radius >= low) & (radius < high)
        rates.append(float(failed[band].mean()) if band.any() else 0.0)

    return rates


def zone_yields(
    dots: np.ndarray,
    die_mm: float = default_die_mm,
    wafer_radius_mm: float = default_wafer_radius_mm,
) -> dict:
    centers = die_centers(die_mm, wafer_radius_mm)
    failed = failed_dies(dots, die_mm, wafer_radius_mm)
    radius = np.hypot(centers[:, 0], centers[:, 1])
    limit = radius.max()

    zones = {
        "center": radius < limit / 3,
        "mid": (radius >= limit / 3) & (radius < 2 * limit / 3),
        "edge": radius >= 2 * limit / 3,
    }
    return {name: float(1 - failed[mask].mean()) for name, mask in zones.items()}
