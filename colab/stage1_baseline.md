# Stage 1 baseline training on Colab (A100)

1. Runtime → Change runtime type → A100 GPU.
2. Get the code and data:
   - If `data/raw` is git-tracked: `!git clone <repo-url> && %cd WaferDetect`
   - Otherwise: clone, then upload `waferdetect_raw.zip` (a zip of `data/raw/`) to Drive,
     mount Drive, and `!unzip -q /content/drive/MyDrive/waferdetect_raw.zip -d data/`
3. Install: `!pip install -q uv && !uv sync`
4. Build the dataset (idempotent, uses committed split manifests' seed):
   `!uv run python -m scripts.perception.dataset --force`
5. Train (resumable — rerun with `--resume` after a session drop, pointing
   `--weights runs/train/stage1_baseline/weights/last.pt`):
   `!uv run python -m scripts.perception.train --device 0`
6. Evaluate:
   `!uv run python -m scripts.perception.evaluate --weights runs/train/stage1_baseline/weights/best.pt`
7. Copy `runs/` to Drive:
   `!cp -r runs /content/drive/MyDrive/waferdetect_runs_stage1`
