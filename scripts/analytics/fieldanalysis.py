import numpy as np


def shot_matrices(
    fail_grid: np.ndarray, field_rows: int, field_cols: int
) -> tuple[np.ndarray, np.ndarray]:
    rows, cols = fail_grid.shape
    n_shot_rows = int(np.ceil(rows / field_rows))
    n_shot_cols = int(np.ceil(cols / field_cols))

    # Compute the per-shot matrix (mean failure over each field-sized block)
    per_shot = np.zeros((n_shot_rows, n_shot_cols))
    for i in range(n_shot_rows):
        for j in range(n_shot_cols):
            block = fail_grid[
                i * field_rows : (i + 1) * field_rows,
                j * field_cols : (j + 1) * field_cols,
            ]
            per_shot[i, j] = block.mean()

    # Compute the intra-field matrix, made by folding every block onto a single reticle field with index modulo
    # Fold all shots into one reticle field and normalize partial edge blocks
    intra = np.zeros((field_rows, field_cols))
    counts = np.zeros((field_rows, field_cols))
    row_index = np.arange(rows) % field_rows
    col_index = np.arange(cols) % field_cols
    np.add.at(intra, (row_index[:, None], col_index[None, :]), fail_grid.astype(float))
    np.add.at(counts, (row_index[:, None], col_index[None, :]), 1.0)

    return per_shot, intra / np.maximum(counts, 1.0)


def field_verdict(
    per_shot: np.ndarray, intra: np.ndarray, z_threshold: float = 3.0
) -> dict:
    def max_z(matrix: np.ndarray) -> tuple[float, tuple[int, int]]:
        spread = matrix.std()
        if spread == 0:
            return 0.0, (0, 0)

        z = (matrix - matrix.mean()) / spread
        position = np.unravel_index(int(z.argmax()), z.shape)
        return float(z.max()), (int(position[0]), int(position[1]))

    shot_z, shot_position = max_z(per_shot)
    intra_z, intra_position = max_z(intra)

    if max(shot_z, intra_z) < z_threshold:
        verdict = "none"
    elif intra_z >= shot_z:
        verdict = "reticle_defect"
    else:
        verdict = "stage_or_dose"

    return {
        "verdict": verdict,
        "intra_max_z": intra_z,
        "intra_position": intra_position,
        "shot_max_z": shot_z,
        "shot_position": shot_position,
    }
