from pathlib import Path

from scripts.perception.annotations import load_class_names
from scripts.wm811k.zero_shot import (
    choose_threshold,
    defect_classes,
    reduce_detections,
    score,
)

classes_file = Path("data/raw/classes.txt")


def test_reduce_no_detections_is_none() -> None:
    names = load_class_names(classes_file)
    assert reduce_detections([], [], names, threshold=0.25) == "none"


def test_reduce_below_threshold_is_none() -> None:
    names = load_class_names(classes_file)
    assert reduce_detections([0], [0.10], names, threshold=0.25) == "none"


def test_reduce_picks_top_mapped_class() -> None:
    names = load_class_names(classes_file)
    assert reduce_detections([4, 0], [0.6, 0.9], names, threshold=0.25) == "center"


def test_reduce_unmapped_class_is_other() -> None:
    names = load_class_names(classes_file)
    assert reduce_detections([17], [0.9], names, threshold=0.25) == "other"
    assert "bullseye" not in defect_classes


def test_choose_threshold_and_score() -> None:
    names = load_class_names(classes_file)
    predictions = {"a": [(0, 0.5)], "b": [(4, 0.1)], "c": [(4, 0.6)]}
    truths = {"a": "center", "b": "none", "c": "scratch"}

    threshold, _ = choose_threshold(predictions, truths, names)
    assert 0.1 < threshold <= 0.5

    metrics = score(predictions, truths, names, threshold)
    assert metrics["none_fpr"] == 0.0
    assert metrics["per_class"]["center"]["f1-score"] == 1.0
    assert metrics["per_class"]["scratch"]["f1-score"] == 1.0
