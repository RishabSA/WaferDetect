from fastapi.testclient import TestClient

from scripts.api.main import create_app

client = TestClient(create_app(None))


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
