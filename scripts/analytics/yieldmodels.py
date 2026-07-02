import numpy as np


def poisson_yield(defect_density: float, die_area: float) -> float:
    return float(np.exp(-die_area * defect_density))


def negative_binomial_yield(
    defect_density: float, die_area: float, alpha: float
) -> float:
    return float((1 + die_area * defect_density / alpha) ** -alpha)


def estimate_defect_density(failed_fraction: float, die_area: float) -> float:
    return float(-np.log(1 - failed_fraction) / die_area)


def quadrat_counts(dots: np.ndarray, quadrats: int = 8) -> np.ndarray:
    edges = np.linspace(-1.0, 1.0, quadrats + 1)
    counts, _, _ = np.histogram2d(dots[:, 0], dots[:, 1], bins=[edges, edges])

    # Keep only quadrats whose center is on-wafer; edge cells bias the variance
    centers = (edges[:-1] + edges[1:]) / 2
    xx, yy = np.meshgrid(centers, centers, indexing="ij")
    return counts[np.hypot(xx, yy) <= 1.0]


def estimate_alpha(counts: np.ndarray) -> float | None:
    mean = counts.mean()
    variance = counts.var()

    if variance <= mean:
        return None

    return float(mean**2 / (variance - mean))
