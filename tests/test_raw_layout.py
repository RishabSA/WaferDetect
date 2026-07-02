from pathlib import Path

RAW_IMAGES_DIR = Path("data/raw/images")
RAW_LABELS_DIR = Path("data/raw/labels")
RAW_OVERLAYS_DIR = Path("data/raw/overlays")
CLASSES_FILE = Path("data/raw/classes.txt")

EXPECTED_PAIR_COUNT = 580


def test_raw_directories_exist() -> None:
    assert RAW_IMAGES_DIR.is_dir()
    assert RAW_LABELS_DIR.is_dir()
    assert RAW_OVERLAYS_DIR.is_dir()
    assert CLASSES_FILE.is_file()


def test_raw_counts() -> None:
    assert len(list(RAW_IMAGES_DIR.glob("*.jpg"))) == EXPECTED_PAIR_COUNT
    assert len(list(RAW_LABELS_DIR.glob("*.txt"))) == EXPECTED_PAIR_COUNT
    assert len(list(RAW_OVERLAYS_DIR.glob("*.jpg"))) == EXPECTED_PAIR_COUNT


def test_old_layout_gone() -> None:
    assert not Path("data/images").exists()
    assert not Path("data/annotated").exists()
