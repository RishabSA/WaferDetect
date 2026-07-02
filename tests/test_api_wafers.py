from fastapi.testclient import TestClient

from scripts.api.main import create_app

client = TestClient(create_app(None))


def test_list_wafers_filters() -> None:
    response = client.get("/api/wafers", params={"split": "test", "category": "donut"})
    body = response.json()

    assert response.status_code == 200
    assert body["total"] >= 1
    assert all(
        item["category"] == "donut" and item["split"] == "test"
        for item in body["items"]
    )


def test_wafer_detail_lists_instances() -> None:
    body = client.get("/api/wafers/0101_scratch").json()
    assert body["category"] == "scratch"
    assert body["instances"][0]["class"] == "scratch"


def test_wafer_image_serves_jpeg() -> None:
    response = client.get("/api/wafers/0101_scratch/image")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    assert client.get("/api/wafers/9999_nothing/image").status_code == 404
