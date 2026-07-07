<p align="center">
  <img src="resources/WaferDetect_Icon.svg" alt="WaferDetect icon" width="110" />
</p>

<h1 align="center">WaferDetect: Segmenting Complex Defect Patterns in Silicon Wafers with YOLO for Root-Cause Diagnosis</h1>

<p align="center">
  <strong>An intelligent, autonomous, and economic wafer-map defect-detection platform for semiconductor fabs</strong><br />
  WaferDetect is an AI-powered wafer-map defect intelligence platform for semiconductor fabs that segments failure patterns in silicon wafers with AI, diagnoses their root causes and possible errors in the manufacturing process, and quantifies the wafer map die yield loss in dollars.
</p>

<p align="center">
  <img src="poster/Rishab Alagharu - WaferDetect GHP 63 CS Poster.jpeg" alt="WaferDetect GHP 63 computer science poster" width="900" />
</p>

<p align="center">
  <img src="resources/WaferDetect_Demo.jpg" alt="WaferDetect dashboard showing wafer defect detections and analytics" width="900" />
</p>

---

## Introduction

Chips power everyday tech — from phones and cars to AI tools — making semiconductor supply
a major news issue. Semiconductor fabrication laboratories (fabs) build those chips on
300 mm silicon wafers through hundreds of steps, including film deposition, lithography,
etching, polishing, and heat treatment, over several weeks. Afterward, every die (chip) on
the wafer is electrically tested, and plotting the failures by position produces a
_wafer map_.

The failure pattern is a fingerprint of a specific process problem: a scratch indicates
handling damage, rings indicate polishing non-uniformity, slip lines indicate thermal
stress, and a repeating grid points to the lithography stepper. Yield engineers read these
maps to decide which tool to fix. A single wafer can be worth up to hundreds of thousands
of dollars, so misreading one — or failing to correct the error behind it — is extremely
expensive.

Prior publicly accessible AI methods classify each wafer with a single label; however,
real wafers exhibit multiple overlapping defects, and a label provides no location
information, so it cannot measure a defect's size, direction, or cost. WaferDetect instead
uses instance segmentation: it localizes every pattern on the wafer with a polygon mask,
which also unlocks the downstream analytics — defect area, scratch kinematics, and
per-defect yield-loss attribution.

## What it does

```
wafer image ──► YOLO26-seg detection ──► root-cause diagnosis ──► yield & $ economics
                (21 defect classes,      (knowledge base +        (die grid, Poisson/
                 polygon masks)           scratch kinematics)      negative-binomial, $/defect)
```

One request to `POST /api/analyze` (a dataset wafer or an uploaded image) returns the
detections with confidence and masks, a per-defect diagnosis (mechanism, responsible process
steps, recommended action, scratch kinematics verdicts), the wafer yield summary (gross/failed
dies, defect density D0, cluster factor α), the dollar loss attributed to each defect region,
and a Radon sinogram of the defect dots — everything the dashboard shows. From the same
analysis the dashboard also exports a KLARF defect file, a multi-page PDF diagnosis report,
and a transparent-background PNG of the annotated wafer. KLARF works in both directions:
upload a KLARF file and its defect list is rebuilt into a wafer map and run through the
same pipeline, so WaferDetect can operate directly on fab inspection-tool output.

## Highlights

- **Perception** — YOLO26-seg trained on real, annotated wafer map images; frozen 87-wafer test split:
  **mask mAP50 0.852**, box mAP50 0.909, ~4 ms/wafer on an A100. Classical baseline for
  scale: zone-density + Radon + SVM reaches 0.819 accuracy on single-defect wafers and 0 on
  multi-defect combos — the gap segmentation exists to close.
- **Physics suite** — four first-principles simulators that _cause_ patterns instead of
  drawing them: a finite-difference thermal solver whose stress field places slip lines,
  Emslie–Bonner–Peck spin-coating, Preston-equation CMP, and a stepper shot-grid model —
  all interactive in the dashboard's Physics Lab.
- **Analytics** — virtual die grid, Poisson and negative-binomial (Stapper) yield models,
  excess-over-background dollar attribution per defect, scratch kinematics (line vs. arc,
  entry bearing), and a 21-class root-cause knowledge base.
- **Dashboard** — FastAPI backend + React 19/TypeScript/Tailwind frontend: a Detect home
  view (upload or browse, detection overlays, defect-dot and sinogram views, inline
  diagnosis report, KLARF ingest + export, PDF-report and wafer-PNG export), Wafer
  Explorer, Yield
  Analytics with a fleet-wide Pareto of loss by process step, and the interactive
  Physics Lab.

## Methodology

- **Dataset** — 580 real, annotated silicon wafer maps (640×640: white disk, black dots =
  failing dies), spanning 21 defect pattern classes (center, donut, edge_ring, scratch,
  swirl, shot_grid, lift_pin, slip_lines, …) with polygon instance labels in YOLO
  segmentation format (`<class_id> x1 y1 x2 y2 ...`, normalized coordinates). Includes a
  four-level size axis for edge scratches and 100 multi-defect ("combo") wafers with 2–4
  overlapping patterns. Frozen, stratified 406/87/87 train/val/test split (seed 42) — the
  87-wafer test split is the fixed measuring stick for every model in the project.
- **Model architecture** — YOLO26x segmentation model, a single-pass detector with a
  convolutional backbone that extracts features at multiple scales as input to parallel
  heads that predict each defect's class, box, and pixel mask together, outlining every
  defect.
- **Analysis** — each detection queries a root-cause knowledge base for the manufacturing
  error, recommended action, and the yield model used to quantify failed dies and dollars
  lost.

## Results

For each silicon wafer map image in the frozen test split (87 wafers, containing all
21 classes), run the YOLO model once and compute the box and mask mean average precision
(mAP).

- **0.852 mask mAP50 / 0.909 box mAP50** on the frozen 87-wafer test split containing all
  21 classes.
- **Multi-defect wafers: 0.686 mask mAP50**, where a single-label classifier baseline
  (zone-density + Radon + SVM) scores 0 by construction.
- 12 of 21 classes at ≥ 0.995 mask AP50; known hard case: the thin, non-convex swirl
  (0.042 mask AP50).

| Split                                 | Box mAP50 | Mask mAP50 | Box mAP50-95 | Mask mAP50-95 |
| ------------------------------------- | --------- | ---------- | ------------ | ------------- |
| Full test (87 wafers, all 21 classes) | 0.909     | 0.852      | 0.741        | 0.632         |
| Combo (multi-defect wafers)           | 0.782     | 0.686      | 0.607        | 0.419         |
| Tiny edge scratches                   | 0.995     | 0.995      | 0.524        | 0.565         |

Per-class results on the full test split:

| Class         | Box AP50 | Mask AP50 | Box AP50-95 | Mask AP50-95 |
| ------------- | -------- | --------- | ----------- | ------------ |
| center        | 0.795    | 0.795     | 0.662       | 0.637        |
| donut         | 0.855    | 0.596     | 0.783       | 0.495        |
| edge_ring     | 0.995    | 0.995     | 0.895       | 0.544        |
| edge_loc      | 0.912    | 0.912     | 0.746       | 0.770        |
| scratch       | 0.995    | 0.995     | 0.864       | 0.821        |
| random        | 0.816    | 0.745     | 0.809       | 0.745        |
| loc           | 0.715    | 0.517     | 0.517       | 0.390        |
| near_full     | 0.835    | 0.835     | 0.805       | 0.733        |
| swirl         | 0.610    | 0.042     | 0.492       | 0.011        |
| radial_spokes | 0.995    | 0.995     | 0.864       | 0.768        |
| shot_grid     | 0.912    | 0.872     | 0.306       | 0.257        |
| crescent      | 0.995    | 0.995     | 0.785       | 0.687        |
| half_wafer    | 0.995    | 0.995     | 0.807       | 0.791        |
| wedge         | 0.995    | 0.995     | 0.814       | 0.744        |
| comet         | 0.995    | 0.995     | 0.678       | 0.478        |
| edge_scratch  | 0.995    | 0.995     | 0.799       | 0.663        |
| lift_pin      | 0.705    | 0.640     | 0.434       | 0.386        |
| bullseye      | 0.995    | 0.995     | 0.995       | 0.995        |
| gradient      | 0.995    | 0.995     | 0.987       | 0.995        |
| slip_lines    | 0.995    | 0.995     | 0.618       | 0.521        |
| double_ring   | 0.995    | 0.995     | 0.895       | 0.829        |

## Discussion and future work

In a real fab line, automating the detection and cost-analysis process can save fabs
millions of dollars. Because the model is single-pass and runs in milliseconds, it can sit
directly on a live, real-time wafer-test data stream — segmenting each wafer map as it
comes off the prober, flagging errors across lots, and alerting engineers to defects
before they damage more wafers.

## Setup and usage

Requires Python ≥ 3.13, [uv](https://docs.astral.sh/uv/), and Node ≥ 20 for the frontend.

```bash
uv sync

# Build the YOLO dataset layout and split manifests from data/raw
uv run python -m scripts.perception.dataset --force

# Train the YOLO segmentatio nmodel
uv run python -m scripts.perception.train --device 0

# Evaluate on the frozen test split and combo/tiny scratch subsets
uv run python -m scripts.perception.evaluate

# Diagnose a single wafer image from the command line
uv run python -m scripts.analytics.diagnosis --image data/raw/images/0101_scratch.jpg --labels data/raw/labels/0101_scratch.txt

# Run the test suite
uv run pytest
```

Run the dashboard (two terminals):

```bash
# Run the API on 127.0.0.1:8000
uv run python -m scripts.api.main

# Run the frontend on http://localhost:5173
cd frontend && npm install && npm run dev
```

Full training runs are intended for GPU (the Colab notebook `WaferDetect.ipynb` at the
repo root); outputs land in `runs/train/<name>/` and `runs/eval/<name>/`.

## Project structure

```
data/raw/                  source dataset: images, labels, overlays, classes.txt (immutable)
data/splits/               frozen train/val/test manifests (seed 42)
scripts/
  perception/              label parsing, split/layout builder, YOLO26-seg train + evaluate
  datagen/                 intensity-field, auto-labeling, and wafer-rendering library
    physics/               thermal, spin-coat, CMP, and shot-grid simulators
  baselines/               zone-density + Radon + SVM and ResNet whole-image baselines
  analytics/               die grid, yield models, $-economics, kinematics, knowledge base
  api/                     FastAPI app: analyze, wafers, yield, physics routers + KLARF and PDF export
frontend/                  React 19 + TypeScript + Vite + Tailwind dashboard
poster/                    GHP poster (PDF/PPTX/JPEG), SVG diagrams, and poster assets
resources/                 README icon and dashboard screenshot
runs/                      training and evaluation outputs (runs/train/, runs/eval/)
tests/                     pytest suite
WaferDetect.ipynb          Colab notebook for full GPU training runs
plot_annotated.py          standalone viewer: polygon labels drawn over a wafer image
wafer_map.py               standalone exploration: extract failing-die dots from a wafer image
```
