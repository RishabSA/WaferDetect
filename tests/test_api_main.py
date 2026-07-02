import base64

import numpy as np
from fastapi.testclient import TestClient

from scripts.api.main import create_app
from scripts.api.plots import field_png


def test_health_without_model() -> None:
    client = TestClient(create_app(None))
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model_loaded": False}


def test_field_png_is_decodable() -> None:
    encoded = field_png(np.random.default_rng(0).random((32, 32)))
    decoded = base64.b64decode(encoded)
    assert decoded[:8] == b"\x89PNG\r\n\x1a\n"
