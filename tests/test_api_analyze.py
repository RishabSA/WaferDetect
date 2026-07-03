import numpy as np
from fastapi.testclient import TestClient

from scripts.api.main import create_app
from scripts.api.routers.analyze import dot_sinogram, sinogram_angles, sinogram_grid

client = TestClient(create_app(None))


def test_analyze_without_model_is_503() -> None:
    response = client.post("/api/analyze", params={"stem": "0101_scratch"})
    assert response.status_code == 503


def test_analyze_requires_exactly_one_source() -> None:
    assert client.post("/api/analyze").status_code == 422


def test_dot_sinogram_shape() -> None:
    dots = np.array([[0.0, 0.0], [0.5, 0.5], [-0.3, 0.2]])
    assert dot_sinogram(dots).shape == (sinogram_grid, sinogram_angles)


def test_dot_sinogram_empty_dots() -> None:
    assert dot_sinogram(np.zeros((0, 2))).max() == 0.0
