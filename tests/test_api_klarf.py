import numpy as np
from fastapi.testclient import TestClient

from scripts.api.klarf import cluster_assignments, klarf_text
from scripts.api.main import create_app
from scripts.api.routers.analyze import analysis_cache

client = TestClient(create_app(None))

# a square detection polygon covering the wafer center in image coordinates
center_polygon = [(0.4, 0.4), (0.6, 0.4), (0.6, 0.6), (0.4, 0.6)]


def test_klarf_without_model_is_503() -> None:
    response = client.post("/api/klarf", params={"stem": "0101_scratch"})
    assert response.status_code == 503


def test_klarf_requires_exactly_one_source() -> None:
    assert client.post("/api/klarf").status_code == 422


def test_cluster_assignments_inside_and_outside() -> None:
    dots = np.array([[0.0, 0.0], [0.9, 0.0]])
    clusters = cluster_assignments(dots, [("scratch", 0.9, center_polygon)])
    assert clusters.tolist() == [1, 0]


def test_klarf_text_coordinates_and_classes() -> None:
    # die 6 mm on a 150 mm wafer: 50 dies per axis, origin at -150 mm, so a dot
    # at the exact wafer center lands in die (25, 25) with zero die-relative offset
    dots = np.array([[0.0, 0.0], [0.9, 0.0]])
    names = ["center", "donut", "edge_ring", "edge_loc", "scratch"]
    text = klarf_text(
        dots, [("scratch", 0.9, center_polygon)], names, "wafer-1", 6.0, 150.0
    )

    assert "FileVersion 1 2;" in text
    assert "DiePitch 6000.0 6000.0;" in text
    assert "SampleCenterLocation 150000.0 150000.0;" in text
    assert ' 5 "scratch"' in text
    assert 'WaferID "wafer-1";' in text
    assert text.rstrip().endswith("EndOfFile;")

    defect_rows = [
        line
        for line in text.splitlines()
        if line.startswith(" ") and len(line.split()) == 11
    ]
    assert len(defect_rows) == 2

    # center dot: die (25, 25), XREL/YREL 0, class 5 (scratch), cluster 1
    first = defect_rows[0].split()
    assert first[1:5] == ["0.0", "0.0", "25", "25"]
    assert first[9:] == ["5", "1"]

    # dot at x = +135 mm: die index 47, unclassified, no cluster
    # (the final DefectList row carries the list-terminating semicolon)
    second = defect_rows[1].rstrip(";").split()
    assert second[3:5] == ["47", "25"]
    assert second[9:] == ["0", "0"]


def test_klarf_endpoint_renders_from_cache() -> None:
    analysis_cache["0001_center"] = {
        "dots": np.array([[0.0, 0.0], [0.1, 0.2]]),
        "detections": [("scratch", 0.9, center_polygon)],
        "image": "cached-image",
        "sinogram": "cached-sinogram",
    }

    # A non-YOLO sentinel: any model call on a cache hit would crash the request
    app = create_app(None)
    app.state.model = object()
    response = TestClient(app).post("/api/klarf", params={"stem": "0001_center"})

    analysis_cache.clear()
    assert response.status_code == 200
    assert "waferdetect_0001_center.klarf" in response.headers["content-disposition"]
    assert response.text.startswith("FileVersion 1 2;")
    assert "DefectRecordSpec 11" in response.text
