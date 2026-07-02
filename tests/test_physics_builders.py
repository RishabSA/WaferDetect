from pathlib import Path

import numpy as np
import pytest

from scripts.datagen.fields import disk_coordinates
from scripts.datagen.generator import generate_sample
from scripts.datagen.physics.builders import physics_field_builders
from scripts.perception.annotations import load_class_names, parse_label_line

classes_file = Path("data/raw/classes.txt")
covered = {"slip_lines", "center", "donut", "edge_ring", "gradient", "shot_grid"}


def test_registry_covers_expected_classes() -> None:
    assert set(physics_field_builders) == covered
    assert covered <= set(load_class_names(classes_file))


@pytest.mark.parametrize("name", sorted(covered))
def test_physics_builder_contract(name: str) -> None:
    field = physics_field_builders[name](128, np.random.default_rng(0))
    _, _, rr, _ = disk_coordinates(128)

    assert field.shape == (128, 128)
    assert field.min() >= 0.0
    assert field.max() > 0.0
    assert float(field[rr > 1.0].max(initial=0.0)) == 0.0


def test_generate_sample_physics_mode() -> None:
    class_names = load_class_names(classes_file)
    _, lines = generate_sample(
        ["slip_lines"], class_names, np.random.default_rng(0), physics_frac=1.0
    )

    instance = parse_label_line(lines[0])
    assert class_names[instance.class_id] == "slip_lines"


def test_physics_generation_is_deterministic() -> None:
    class_names = load_class_names(classes_file)
    image_a, lines_a = generate_sample(
        ["donut"], class_names, np.random.default_rng(5), physics_frac=1.0
    )
    image_b, lines_b = generate_sample(
        ["donut"], class_names, np.random.default_rng(5), physics_frac=1.0
    )

    assert lines_a == lines_b
    assert np.array_equal(np.asarray(image_a), np.asarray(image_b))
