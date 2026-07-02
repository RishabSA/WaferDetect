import numpy as np

from waferdetect.baselines.classical import (
    density_features,
    dot_coordinates,
    feature_vector,
    radon_features,
)


def make_wafer_image(dot_positions: list[tuple[float, float]]) -> np.ndarray:
    image = np.full((640, 640), 255, dtype=np.uint8)
    for u, v in dot_positions:
        x = int((0.5 + u * 0.485) * 640)
        y = int((0.5 + v * 0.485) * 640)
        image[y - 2 : y + 2, x - 2 : x + 2] = 0
    return image


def test_dot_coordinates_finds_dots_and_ignores_outline() -> None:
    image = make_wafer_image([(0.0, 0.0), (0.5, 0.5)])

    yy, xx = np.mgrid[0:640, 0:640]
    rr = np.hypot(xx - 320, yy - 320)
    image[(rr > 308) & (rr < 312)] = 0

    dots = dot_coordinates(image)
    assert 1 <= len(dots) <= 200
    assert np.hypot(dots[:, 0], dots[:, 1]).max() <= 0.94


def test_density_features_localize() -> None:
    dots = np.array([[0.05, 0.05]] * 50)
    features = density_features(dots)

    assert features.shape == (32,)
    assert abs(features.sum() - 1.0) < 1e-9
    assert features.max() > 0.9


def test_radon_features_shape_and_line_sensitivity() -> None:
    line = np.stack([np.linspace(-0.8, 0.8, 100), np.zeros(100)], axis=1)
    blob = np.random.default_rng(0).normal(0, 0.2, size=(100, 2))

    line_features = radon_features(line)
    assert line_features.shape == (40,)
    assert line_features[20:].max() > radon_features(blob)[20:].max()


def test_feature_vector_length() -> None:
    image = make_wafer_image([(0.1, 0.1), (-0.3, 0.2)])
    assert feature_vector(image).shape == (72,)
