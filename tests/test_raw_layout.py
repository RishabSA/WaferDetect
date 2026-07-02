from pathlib import Path

raw_images_dir = Path("data/raw/images")
raw_labels_dir = Path("data/raw/labels")
raw_overlays_dir = Path("data/raw/overlays")
classes_file = Path("data/raw/classes.txt")

expected_pair_count = 580


def test_raw_directories_exist() -> None:
    assert raw_images_dir.is_dir()
    assert raw_labels_dir.is_dir()
    assert raw_overlays_dir.is_dir()
    assert classes_file.is_file()


def test_raw_counts() -> None:
    assert len(list(raw_images_dir.glob("*.jpg"))) == expected_pair_count
    assert len(list(raw_labels_dir.glob("*.txt"))) == expected_pair_count
    assert len(list(raw_overlays_dir.glob("*.jpg"))) == expected_pair_count


def test_old_layout_gone() -> None:
    assert not Path("data/images").exists()
    assert not Path("data/annotated").exists()
