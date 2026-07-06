from PIL import Image
import numpy as np
from fastapi.testclient import TestClient

from scripts.api.main import create_app
from scripts.api.plots import image_png
from scripts.api.routers.analyze import analysis_cache

client = TestClient(create_app(None))


def test_report_without_model_is_503() -> None:
    response = client.post("/api/report", params={"stem": "0101_scratch"})
    assert response.status_code == 503


def test_report_requires_exactly_one_source() -> None:
    assert client.post("/api/report").status_code == 422


def test_report_renders_pdf_from_cache() -> None:
    wafer_png = image_png(Image.new("RGB", (64, 64), "white"))
    analysis_cache["0001_center"] = {
        "dots": np.array([[0.0, 0.0], [0.1, 0.2], [-0.3, 0.4]]),
        "detections": [("scratch", 0.9, [(0.4, 0.4), (0.6, 0.4), (0.6, 0.6)])],
        "image": wafer_png,
        "sinogram": wafer_png,
    }

    # A non-YOLO sentinel: any model call on a cache hit would crash the request
    app = create_app(None)
    app.state.model = object()
    response = TestClient(app).post("/api/report", params={"stem": "0001_center"})

    analysis_cache.clear()
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "waferdetect_0001_center.pdf" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")
