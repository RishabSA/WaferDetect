from fastapi.testclient import TestClient

from scripts.api.main import create_app
from scripts.api.routers.detect import detections_to_response

client = TestClient(create_app(None))


def test_detect_without_model_is_503() -> None:
    response = client.post("/api/detect", params={"stem": "0101_scratch"})
    assert response.status_code == 503


def test_detect_requires_exactly_one_source() -> None:
    assert client.post("/api/detect").status_code == 422


def test_detections_to_response_shapes() -> None:
    segments = [[(0.1, 0.1), (0.4, 0.1), (0.4, 0.4), (0.1, 0.4)]]
    body = detections_to_response([4], [0.9], segments, ["a"] * 4 + ["scratch"])

    assert body[0]["class"] == "scratch"
    assert body[0]["confidence"] == 0.9
    assert abs(body[0]["area_frac"] - 0.09) < 1e-9
    assert len(body[0]["polygon"]) == 4
