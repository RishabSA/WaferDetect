import numpy as np
import pytest
from fastapi.testclient import TestClient

from scripts.api.klarf import (
    cluster_assignments,
    is_klarf,
    klarf_text,
    parse_klarf,
    render_dots,
)
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


def test_is_klarf_sniffs_content() -> None:
    assert is_klarf(b"\nFileVersion 1 2;")
    assert not is_klarf(b"\x89PNG\r\n")


def test_parse_klarf_roundtrip() -> None:
    dots = np.array([[0.0, 0.0], [0.9, 0.0], [-0.3, 0.42]])
    names = ["center", "donut", "edge_ring", "edge_loc", "scratch"]
    text = klarf_text(
        dots, [("scratch", 0.9, center_polygon)], names, "wafer-1", 6.0, 150.0
    )

    parsed = parse_klarf(text)

    assert parsed["die_mm"] == 6.0
    assert parsed["wafer_radius_mm"] == 150.0
    assert parsed["wafer_id"] == "wafer-1"
    assert parsed["classes"] == ["scratch"]
    # XREL/YREL are written at 0.1 µm precision, so positions survive to
    # well under 1e-5 of the wafer radius
    assert np.allclose(parsed["dots"], dots, atol=1e-5)


def test_parse_klarf_coordinates_from_minimal_file() -> None:
    text = (
        "FileVersion 1 2;\n"
        "DiePitch 6000.0 6000.0;\n"
        "SampleSize 1 300;\n"
        "SampleCenterLocation 150000.0 150000.0;\n"
        'WaferID "w";\n'
        "DefectRecordSpec 5 DEFECTID XREL YREL XINDEX YINDEX;\n"
        "DefectList\n"
        " 1 0.0 0.0 25 25\n"
        " 2 0.0 3000.0 25 40;\n"
        "EndOfFile;\n"
    )

    parsed = parse_klarf(text)

    # die (25, 25) with zero offset is the exact wafer center
    assert np.allclose(parsed["dots"][0], [0.0, 0.0])
    # die row 40: y = -150 + 40*6 + 3 = +93 mm (Cartesian up), so the image-
    # convention dot sits at v = -0.62
    assert np.allclose(parsed["dots"][1], [0.0, -0.62])
    assert parsed["classes"] == []


def test_render_dots_paints_single_pixels() -> None:
    pixels = np.asarray(render_dots(np.array([[0.0, 0.0]])))

    assert pixels.shape == (640, 640)
    assert pixels[320, 320] == 0
    # single-pixel footprint: exactly one dark pixel around the wafer center
    assert (pixels[315:326, 315:326] < 128).sum() == 1


def test_parse_klarf_missing_record_raises() -> None:
    with pytest.raises(ValueError, match="DiePitch"):
        parse_klarf("FileVersion 1 2;\nEndOfFile;")


def test_analyze_rejects_malformed_klarf() -> None:
    # The parse failure happens before any model call, so a sentinel suffices
    app = create_app(None)
    app.state.model = object()
    response = TestClient(app).post(
        "/api/analyze",
        files={"file": ("bad.klarf", b"FileVersion 1 2;\nEndOfFile;", "text/plain")},
    )

    assert response.status_code == 422
    assert "DiePitch" in response.text


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
