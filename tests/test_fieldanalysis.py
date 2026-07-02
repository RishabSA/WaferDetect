import numpy as np

from scripts.analytics.fieldanalysis import field_verdict, shot_matrices


def test_reticle_defect_detected() -> None:
    fail_grid = np.zeros((20, 20), dtype=bool)
    fail_grid[2::5, 3::5] = True

    per_shot, intra = shot_matrices(fail_grid, 5, 5)
    result = field_verdict(per_shot, intra)

    assert result["verdict"] == "reticle_defect"
    assert result["intra_position"] == (2, 3)


def test_whole_shot_failure_is_stage_or_dose() -> None:
    fail_grid = np.zeros((20, 20), dtype=bool)
    fail_grid[5:10, 10:15] = True

    per_shot, intra = shot_matrices(fail_grid, 5, 5)
    result = field_verdict(per_shot, intra)

    assert result["verdict"] == "stage_or_dose"
    assert result["shot_position"] == (1, 2)


def test_clean_grid_is_none() -> None:
    per_shot, intra = shot_matrices(np.zeros((20, 20), dtype=bool), 5, 5)
    assert field_verdict(per_shot, intra)["verdict"] == "none"
