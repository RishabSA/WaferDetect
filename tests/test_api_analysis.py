from fastapi.testclient import TestClient

from scripts.api.main import create_app

client = TestClient(create_app(None))


def test_yield_wafer_endpoint() -> None:
    body = client.get("/api/yield/wafer/0001_center").json()

    assert body["summary"]["gross_dies"] > 1000
    assert body["summary"]["total_loss_dollars"] >= 0
    assert 0 <= body["summary"]["yield_random"] <= 1
    assert len(body["radial"]) == 10
    assert set(body["zones"]) == {"center", "mid", "edge"}
    assert len(body["regions"]) == 1


def test_pareto_endpoint_limited() -> None:
    body = client.get("/api/yield/pareto", params={"split": "test", "limit": 3}).json()

    assert body["wafers"] == 3
    assert all(
        isinstance(step, str) and dollars >= 0 for step, dollars in body["pareto"]
    )
