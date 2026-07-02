from pathlib import Path

import numpy as np

from scripts.analytics.diagnosis import diagnose, kb_path, load_knowledge_base, polygon_area
from scripts.baselines.classical import dot_coordinates
from scripts.perception.annotations import load_class_names, load_label_file

classes_file = Path("data/raw/classes.txt")


def test_knowledge_base_covers_all_classes() -> None:
    kb = load_knowledge_base(kb_path)
    assert set(kb) == set(load_class_names(classes_file))
    assert all("action" in entry and "process_steps" in entry for entry in kb.values())


def test_diagnose_synthetic_structure() -> None:
    kb = load_knowledge_base(kb_path)
    square = [(0.015, 0.015), (0.5, 0.015), (0.5, 0.985), (0.015, 0.985)]
    rng = np.random.default_rng(0)
    dots = np.stack([rng.uniform(-0.9, -0.1, 60), rng.uniform(-0.9, 0.9, 60)], axis=1)

    report = diagnose(dots, [("center", 0.9, square)], kb)
    entry = report["detections"][0]

    assert entry["class"] == "center"
    assert entry["diagnosis"]["process_steps"] == ["spin coat", "CMP"]
    assert entry["yield_loss"]["dollars"] >= 0
    assert 0 < polygon_area(square) < 1
    assert report["wafer_summary"]["gross_dies"] > 1000
    assert "d0_per_mm2" in report["wafer_summary"]


def test_diagnose_real_scratch_wafer() -> None:
    from PIL import Image

    kb = load_knowledge_base(kb_path)
    names = load_class_names(classes_file)
    image = np.asarray(Image.open("data/raw/images/0101_scratch.jpg").convert("L"))
    instances = load_label_file(Path("data/raw/labels/0101_scratch.txt"))

    detections = [(names[instance.class_id], 1.0, instance.polygon) for instance in instances]
    report = diagnose(dot_coordinates(image), detections, kb)
    entry = report["detections"][0]

    assert entry["class"] == "scratch"
    assert entry["kinematics"]["verdict"] in {
        "handling_linear",
        "cmp_rotational",
        "off_axis_arc",
    }
    assert report["wafer_summary"]["total_loss_dollars"] >= 0
