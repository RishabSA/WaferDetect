import base64

from fastapi.testclient import TestClient

from scripts.api.main import create_app
from scripts.perception.annotations import parse_label_line

client = TestClient(create_app(None))


def test_generate_returns_parseable_labels() -> None:
    body = client.post(
        "/api/generate", json={"categories": ["donut"], "seed": 7}
    ).json()

    assert body["categories"] == ["donut"]
    assert base64.b64decode(body["image"])[:8] == b"\x89PNG\r\n\x1a\n"
    assert parse_label_line(body["labels"][0]).class_id == 1


def test_generate_unknown_category_is_422() -> None:
    response = client.post(
        "/api/generate", json={"categories": ["warp_core"], "seed": 7}
    )
    assert response.status_code == 422


def test_thermal_endpoint_returns_field_chain() -> None:
    body = client.post("/api/physics/thermal", json={"seed": 3}).json()

    assert {"temperature", "stress", "slip_probability", "sample"} <= set(body)
    assert body["stats"]["max_temperature"] > body["stats"]["min_temperature"]


def test_spincoat_mode_validated() -> None:
    assert (
        client.post("/api/physics/spincoat", json={"mode": "sideways"}).status_code
        == 422
    )
    assert (
        client.post("/api/physics/spincoat", json={"mode": "tilt"}).status_code == 200
    )


def test_shotgrid_returns_verdict() -> None:
    body = client.post(
        "/api/physics/shotgrid", json={"mode": "intra", "seed": 5}
    ).json()
    assert body["verdict"]["verdict"] in {"reticle_defect", "stage_or_dose", "none"}
