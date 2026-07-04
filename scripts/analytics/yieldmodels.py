import numpy as np


def poisson_yield(defect_density: float, die_area: float) -> float:
    # Y = e^(-A * D_0) - The Poisson yield model assumes defects that land randomly and independently, so the chance a die of area A survives is the Poisson zero-count probability

    # Yield percentage (probability of a die being defect-free)
    return float(np.exp(-die_area * defect_density))


def negative_binomial_yield(
    defect_density: float, die_area: float, alpha: float
) -> float:
    # Y = (1 + A * D_0/α)^(−α) - The Stapper model assumes that in real defect clusters, a contamination event could cluster many particles together
    # Clustering is good for yield, as ten defects in one die kill one die
    # α is the cluster parameter, and a large α recovers Poisson exactly, while a small α means heavy clustering and higher yield at the same density

    # Yield percentage (probability of a die being defect-free)
    return float((1 + die_area * defect_density / alpha) ** -alpha)


def estimate_defect_density(failed_fraction: float, die_area: float) -> float:
    # D_0 = −ln(1 - f)/A - Converts from an observed failed fraction back to defects per mm²
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
