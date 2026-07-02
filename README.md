# WaferDetect

Wafer-map defect intelligence for semiconductor manufacturing: detect and segment failure
patterns on wafer maps with a deep segmentation model trained entirely on synthetic data, then
turn detections into the answers a fab actually needs — what pattern, where, what caused it,
and what it cost.

## Why wafer maps

After fabrication, every die on a silicon wafer is electrically tested. Plotting the failing
dies by position produces a *wafer map*, and the spatial pattern of failures is a fingerprint
of a specific process problem: a scratch means mechanical handling damage, slip lines mean
thermal stress during rapid thermal processing, a repeating shot grid points at the
lithography stepper, rings and center clusters point at deposition or polishing uniformity.
Yield engineers read these patterns to decide which tool to go fix. WaferDetect automates that
reading — and because real fab data is proprietary and pixel-level annotations barely exist,
it does so with models trained on synthetic wafer maps, validated against the real-world
WM-811K benchmark.

Instance segmentation (rather than whole-image classification) is the core design choice:
real wafers carry co-occurring defects, and a classifier can only ever name one. The detector
localizes every pattern on the wafer with a polygon mask, which also unlocks the downstream
analytics — defect area, scratch orientation, and per-defect yield-loss attribution.

## Dataset

- 580 synthetic wafer maps (640×640): white disk, black dots = failing dies.
- 21 defect classes (center, donut, edge_ring, scratch, swirl, shot_grid, lift_pin,
  slip_lines, …) with polygon instance labels in YOLO segmentation format
  (`<class_id> x1 y1 x2 y2 ...`, normalized coordinates).
- Includes a four-level size axis for edge scratches and 100 multi-defect ("combo") wafers
  with 2–4 overlapping patterns.
- Frozen, stratified 406/87/87 train/val/test split (seed 42) — the 87-wafer test split is the
  fixed measuring stick for every model in the project.

## Current state

- **Stage 1 — foundation & baseline (complete):** validated data pipeline, deterministic
  split manifests, YOLO dataset layout builder, YOLO26-seg training CLI with a wafer-aware
  augmentation policy (mosaic disabled — collaged part-wafers are physically impossible;
  full rotation/flips — wafer scenes are rotation-valid), and an evaluation harness that
  reports per-class box/mask mAP plus dedicated combo and tiny-scratch subsets.
- **Stage 2 — data engine (planned):** a parametric generator in which each defect class is a
  2D intensity field over the wafer disk; the same field samples the failing-die dots *and*
  produces the polygon label, scaling the dataset to 10k+ images with a data-scaling study and
  classical (density + Radon + SVM) and CNN baselines for comparison.
- **Later stages:** physics simulations of defect-forming mechanisms (thermal stress → slip
  lines, spin-coating and CMP uniformity, stepper shot grids), validation on WM-811K real fab
  data, a yield-economics and root-cause analytics engine, SPC excursion monitoring, and a
  FastAPI + React dashboard. See `docs/superpowers/specs/` for the full design.

## Setup and usage

Requires Python ≥ 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync

# build the YOLO dataset layout + split manifests from data/raw
uv run python -m waferdetect.perception.dataset --force

# train (local Apple Silicon: --device mps; CUDA: --device 0)
uv run python -m waferdetect.perception.train --device mps

# evaluate the trained model on the frozen test split + subsets
uv run python -m waferdetect.perception.evaluate

# run the test suite
uv run pytest
```

Full training runs are intended for GPU (see `colab/stage1_baseline.md` for the Colab A100
recipe); outputs land in `runs/train/<name>/` and `runs/eval/<name>/`.

## Project structure

```
data/raw/                  source dataset: images, labels, overlays, classes.txt (immutable)
data/splits/               frozen train/val/test manifests (seed 42)
data/yolo/                 derived YOLO layout (generated, gitignored)
src/waferdetect/
  perception/
    annotations.py         label parsing (DefectInstance, class-name registry)
    dataset.py             stratified split, manifests, YOLO layout builder (CLI)
    train.py               YOLO26-seg training CLI with the wafer augmentation policy
    evaluate.py            test-split + combo/tiny-subset evaluation, metrics.json + report.md
colab/                     GPU run recipes
docs/superpowers/          design spec and stage implementation plans
tests/                     pytest suite
```
