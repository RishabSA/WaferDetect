from dataclasses import dataclass
from pathlib import Path


@dataclass()
class DefectInstance:
    class_id: int  # 0 - 20
    polygon: list[tuple[float, float]]  # [0, 1] vertices tracing the defect outline


def load_class_names(classes_file: Path) -> list[str]:
    with open(classes_file) as file:
        # Load all class names in order
        return [line.strip() for line in file if line.strip()]


def parse_label_line(line: str) -> DefectInstance:
    tokens = line.split()

    # First token is the class token
    class_id = int(tokens[0])

    # Get all x and y polygon coordinates
    coordinates = [float(token) for token in tokens[1:]]

    # Get x's at even positions and y's at odd positions, and pair them into (x, y) vertices.
    polygon = list(zip(coordinates[0::2], coordinates[1::2], strict=True))

    return DefectInstance(class_id=class_id, polygon=polygon)


def load_label_file(label_path: Path) -> list[DefectInstance]:
    with open(label_path) as file:
        lines = [line.strip() for line in file if line.strip()]

    # Get the defect instance labels for each label file
    # Single-defect wafers give a 1-element list, and combo wafers give 2–4 elements
    return [parse_label_line(line) for line in lines]


def load_dataset(images_dir: Path, labels_dir: Path) -> dict:
    stems = sorted(path.stem for path in images_dir.glob("*.jpg"))

    # Load the matching label for every image by file stem
    return {stem: load_label_file(labels_dir / f"{stem}.txt") for stem in stems}
