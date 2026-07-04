import numpy as np
from fastapi.testclient import TestClient

from scripts.api.main import create_app
from scripts.api.routers.analyze import (
    analysis_cache,
    dot_sinogram,
    sinogram_angles,
    sinogram_grid,
)

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


def test_analyze_cache_hit_skips_model() -> None:
    analysis_cache["0001_center"] = {
        "dots": np.array([[0.0, 0.0], [0.1, 0.2]]),
        "detections": [],
        "image": "cached-image",
        "sinogram": "cached-sinogram",
    }

    # A non-YOLO sentinel: any model call on a cache hit would crash the request
    app = create_app(None)
    app.state.model = object()
    body = TestClient(app).post("/api/analyze", params={"stem": "0001_center"}).json()

    analysis_cache.clear()
    assert body["image"] == "cached-image"
    assert body["sinogram"] == "cached-sinogram"
    assert body["wafer_summary"]["gross_dies"] > 1000
    assert body["ground_truth"] == ["center"]
