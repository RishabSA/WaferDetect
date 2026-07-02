from pathlib import Path

import numpy as np
from PIL import Image

from scripts.datagen.fields import field_builders
from scripts.datagen.generator import (
    background_dots,
    choose_categories,
    generate_sample,
    image_size,
    quantize_dots,
    sample_dots,
    sample_name,
)
from scripts.perception.annotations import load_class_names, parse_label_line

classes_file = Path("data/raw/classes.txt")


def test_sample_dots_follow_field() -> None:
    field = field_builders["center"](128, np.random.default_rng(0))
    dots = sample_dots(field, 300, np.random.default_rng(1))

    assert dots.shape == (300, 2)
    assert np.hypot(dots[:, 0], dots[:, 1]).mean() < 0.5


def test_background_dots_inside_disk() -> None:
    dots = background_dots(500, np.random.default_rng(0))
    assert np.hypot(dots[:, 0], dots[:, 1]).max() <= 1.0


def test_quantize_snaps_and_dedupes() -> None:
    dots = np.array([[0.101, 0.101], [0.109, 0.108], [-0.5, 0.5]])
    snapped = quantize_dots(dots, die_grid=20)

    assert len(snapped) == 2
    cell = 2.0 / 20
    offsets = (snapped + 1) / cell - 0.5
    assert np.allclose(offsets, offsets.round())


def test_generate_single_sample() -> None:
    class_names = load_class_names(classes_file)
    image, lines = generate_sample(["donut"], class_names, np.random.default_rng(0))

    assert isinstance(image, Image.Image)
    assert image.size == (image_size, image_size)
    assert len(lines) == 1

    instance = parse_label_line(lines[0])
    assert class_names[instance.class_id] == "donut"
    assert all(0 <= value <= 1 for point in instance.polygon for value in point)


def test_generate_combo_sample() -> None:
    class_names = load_class_names(classes_file)
    _, lines = generate_sample(["scratch", "edge_ring"], class_names, np.random.default_rng(0))
    assert len(lines) == 2


def test_generation_is_deterministic() -> None:
    class_names = load_class_names(classes_file)
    image_a, lines_a = generate_sample(["swirl"], class_names, np.random.default_rng(7))
    image_b, lines_b = generate_sample(["swirl"], class_names, np.random.default_rng(7))

    assert lines_a == lines_b
    assert np.array_equal(np.asarray(image_a), np.asarray(image_b))


def test_choose_categories_shapes() -> None:
    rng = np.random.default_rng(0)
    singles = [choose_categories(rng, combo_frac=0.0) for _ in range(20)]
    combos = [choose_categories(rng, combo_frac=1.0) for _ in range(20)]

    assert all(len(categories) == 1 for categories in singles)
    assert all(2 <= len(categories) <= 4 for categories in combos)
    assert all(category in field_builders for categories in singles + combos for category in categories)


def test_sample_name_convention() -> None:
    assert sample_name(7, ["swirl"]) == "0007_swirl"
    assert sample_name(466, ["edge_scratch_small"]) == "0466_edge_scratch_small"
    assert sample_name(481, ["half_wafer", "donut"]) == "0481_combo_half_wafer+donut"
    assert sample_name(9, ["edge_scratch_tiny", "loc"]) == "0009_combo_edge_scratch+loc"
