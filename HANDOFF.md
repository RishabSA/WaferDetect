# WaferDetect — Agent Handoff

Read this before touching anything. It is the compressed institutional memory of the project:
what exists, why it is the way it is, and the rules that are not negotiable. Pair it with the
spec and the current stage's implementation plan.

**Document authority order:** (1) direct instructions from the user → (2) this file →
(3) the spec `docs/superpowers/specs/2026-07-01-waferdetect-design.md` (§3.3 coding style is
binding) → (4) the stage implementation plans in `docs/superpowers/plans/`.
Stage plans contain complete code to transcribe; where a plan's code conflicts with the coding
style in this file / spec §3.3, the style governs (the Stage 1 plan predates the style and shows
a heavier idiom — do not imitate it).

**Maintenance rule:** whenever a new stage implementation plan is created, this file gets
updated (status, interfaces, decisions). If you create or execute a plan, keep HANDOFF.md true.

---

## 1. What this project is

WaferDetect is a fab-oriented wafer-map defect intelligence system, built as a staged ML +
systems project. A wafer map plots which dies on a semiconductor wafer failed electrical test;
the _spatial pattern_ of failures fingerprints the process problem (scratch → handling/CMP,
slip lines → RTP thermal stress, shot grid → litho stepper, rings → uniformity, lift_pin →
chuck pins…). The system detects and segments those patterns with a YOLO26 segmentation model
trained on synthetic data, and will grow into: physics simulations of the defect-forming
mechanisms, validation on real fab data (WM-811K), a root-cause + yield-economics analytics
engine, SPC excursion monitoring, and a FastAPI + React dashboard. Framing is
**product-for-fabs first, research second** — every component answers a question a yield
engineer actually asks.

```
Layer 0  DATA ENGINE      heuristic generator + auto polygon labels (+ physics modes later)
Layer 1  PERCEPTION       YOLO26-seg instance segmentation (baselines: SVM, ResNet-18)
Layer 2  REAL VALIDATION  WM-811K zero-shot + few-shot
Layer 3  ANALYTICS        geometry, kinematics, knowledge base, yield $-economics
Layer 4  MONITORING       stream simulator -> EWMA/CUSUM -> alarms
Layer 5  DASHBOARD        FastAPI + React/Vite/Tailwind (6 views incl. interactive Physics Lab)
FUTURE   F1 spatial statistics (CSR, similarity, stacked maps)   F2 virtual fab (commonality)
```

## 2. Current status (updated 2026-07-02)

- **Stage 1 (foundation & baseline): code COMPLETE, 27/27 tests passing.** The full baseline
  training run is PENDING — the user runs it on Colab A100 per `colab/stage1_baseline.md`.
  A local overfit smoke run reached epoch 22 with box mAP50 ≈ 0.47 and rising before being
  intentionally stopped — the pipeline mechanically works (YOLO26 weights download, MPS
  training, label ingestion all verified).
- **Stage 2 (data engine): code COMPLETE, 80/80 tests passing.** Implemented
  `datagen/fields.py`, `datagen/labels.py`, `datagen/generator.py`, `datagen/review.py`,
  `datagen/layout.py`, `baselines/classical.py`, `baselines/resnet.py`, tests, and
  `colab/stage2_data_engine.md`. Local smoke verified generator/review/layout CLIs. Classical
  baseline was run locally: singles accuracy 0.8194, singles macro-F1 0.7911, combo exact-match
  0 by construction. Remaining Stage 2 work is human/A100 gated: pilot review approval, 10k
  generation, YOLO scaling study, ResNet training, and exit-gate comparison.
- **Stage 3 (physics suite): code COMPLETE, 108/108 tests passing.** Implemented
  `scripts/datagen/physics/{thermal,spincoat,cmp,shotgrid,builders}.py`, generator
  `physics_frac` integration, and tests. Local smoke verified physics-mode generation and
  review-sheet rendering in `/private/tmp`. Remaining Stage 3 work is the human visual gate:
  generate the 300-sample physics pilot in `data/generated/physics_pilot`, review sheets for
  the six physics-covered classes, and choose the production `--physics-frac`.
- **Stage 4 (WM-811K validation): code COMPLETE, 127/127 tests passing.** Implemented
  `scripts/wm811k/{convert,manifests,render,zero_shot,pseudolabel}.py`, fixture-only tests,
  `colab/stage4_wm811k.md`, and deps `pandas` + `pyarrow`. Code builds and tests without the
  dataset or weights. Remaining Stage 4 work is execution-gated: user download of `LSWMD.pkl`
  (~2 GB → `data/wm811k/`) plus trained weights, then conversion/rendering, zero-shot scoring,
  few-shot sweeps, and the die-grid quantization ablation.
- **Stage 5 (analytics engine): code COMPLETE, 149/149 tests passing.** Implemented
  `scripts/analytics/{diegrid,yieldmodels,economics,kinematics,fieldanalysis,diagnosis}.py`,
  `knowledge_base.yaml`, `image_to_wafer`, and tests. Generated sample ground-truth reports:
  `runs/analytics/0101_scratch.json` ($1606), `runs/analytics/0001_center.json` ($3194),
  `runs/analytics/0481_combo_half_wafer+donut.json` ($19064). Remaining Stage 5 work is the
  human report review/tuning gate.
- **Stage 7 (FastAPI backend): plan written, not started** —
  `docs/superpowers/plans/2026-07-02-stage7-fastapi.md`. Six tasks; see §8 below. **Stage 6
  (monitoring) was deliberately skipped for now by user decision** — the spec's
  `/api/monitor/*` endpoints are NOT in the Stage 7 plan; Stage 6 adds its own router later.
- **Stage 1 baseline TRAINED (2026-07-02, A100):** test-split mask mAP50 **0.842** (≥ 0.80
  target met), box mAP50 0.896; combo subset mask mAP50 0.670 (17-point gap — misses the
  ≤10-point criterion; swirl masks are the main failure at 0.151, plus random-in-combo and
  donut masks); edge_scratch_tiny subset 0.995. **0.842 is the frozen Gate B bar.** Weights in
  `runs/train/stage1_baseline/weights/best.pt` (user's `waferdetect_runs/`). Known data wart:
  ultralytics deduped duplicate label lines in `0170_swirl` (3) and one combo file (1).
- 2026-07-02: all code moved from `src/waferdetect/` to `scripts/` (no installed package,
  no build system — see §4). All docs and commands were updated in the same pass.
- The user personally rewrote the Stage 1 code after generation to enforce the coding style in
  §6 — that style is now mandatory on the first pass. They deleted `config.py`,
  `test_config.py`, `test_train_args.py` in that sweep; do not reintroduce them.

## 3. Dataset facts (memorize these)

- `data/raw/` — the source of truth, **immutable**: `images/` (580 JPGs, 640×640, white
  background, black circle = wafer outline, black dots = failing dies), `labels/` (580 txts),
  `overlays/` (human-review JPGs with drawn polygons), `classes.txt`.
- **`classes.txt` line order defines the zero-indexed class ID** (21 classes; the file has a
  trailing blank line — parsers skip blanks): 0 center, 1 donut, 2 edge_ring, 3 edge_loc,
  4 scratch, 5 random, 6 loc, 7 near_full, 8 swirl, 9 radial_spokes, 10 shot_grid, 11 crescent,
  12 half_wafer, 13 wedge, 14 comet, 15 edge_scratch, 16 lift_pin, 17 bullseye, 18 gradient,
  19 slip_lines, 20 double_ring.
- **Label format (YOLO segmentation):** one line per defect instance:
  `<class_id> x1 y1 x2 y2 ...` — alternating x,y polygon vertices, normalized to [0,1],
  implicitly closed, variable vertex count (4 for scratches, up to 30 for round blobs),
  6-decimal coords.
- **Filenames encode ground truth:** `NNNN_<category>.jpg`. 24 single categories = 20 plain
  classes + `edge_scratch_{tiny,small,medium,large}` (a size/difficulty axis — all four map to
  class 15). 100 `combo_<a>+<b>[+...]` images carry 2–4 co-occurring defects (one label line
  each). Combos are WHY this is a detection project: whole-image classifiers structurally
  cannot handle them.
- `data/splits/{train,val,test}.txt` — frozen manifests, 406/87/87, stratified per category,
  seed 42. **The 87-image raw test split is the permanent measuring stick**: every model in
  every stage (including generated-data models) is evaluated against it.
- `data/yolo/` — derived YOLO layout (copies + `data.yaml`), gitignored, rebuild with
  `uv run python -m scripts.perception.dataset --force`.
- The dataset is synthetic (rendered, perfectly balanced). WM-811K (Stage 4) is the real-fab
  counterpart: 811k die-grid maps, ~173k labeled, 8 classes (all a subset of ours),
  image-level labels only — no polygons (drives the pseudo-label design in the spec §6).

## 4. Codebase map and exact interfaces (post-cleanup — trust THIS, not the Stage 1 plan)

Python ≥ 3.13, `uv`-managed. **All code lives in `scripts/`** (`scripts/perception/`,
`scripts/datagen/`, `scripts/baselines/`, and future subpackages) as plain modules — there is
NO installed package and NO build system; `pyproject.toml` only manages dependencies, and
pytest resolves `from scripts...` imports via `[tool.pytest.ini_options] pythonpath = ["."]`.
Run everything from repo root (`uv run python -m scripts....` — `-m` puts the cwd on
`sys.path`). Tests in `tests/` (pytest; they use the real `data/raw` files freely).

`scripts/perception/annotations.py` — label-format layer:

- `@dataclass class DefectInstance: class_id: int; polygon: list[tuple[float, float]]`
  (**renamed from `Instance`** — older docs/plans may say `Instance`).
- `load_class_names(classes_file: Path) -> list[str]` (skips blank lines, no count check)
- `parse_label_line(line: str) -> DefectInstance` — validation is _implicit_: `int()` raises on
  bad class, `zip(strict=True)` raises on odd coordinate counts.
- `load_label_file(label_path: Path) -> list[DefectInstance]` (empty file → `[]`)
- `load_dataset(images_dir: Path, labels_dir: Path) -> dict` — `{stem: [instances]}`; missing
  label surfaces as `FileNotFoundError` from `open`.

`scripts/perception/dataset.py` — dataset preparation:

- module globals: `classes_file`, `raw_images_dir`, `raw_labels_dir`, `splits_dir`, `yolo_dir`
  (lowercase `Path` constants), `split_names = ("train", "val", "test")`.
- `stem_category(stem: str) -> str` — filename → stratum; **all combos pool into one "combo"
  stratum** (deliberate spec deviation: per-first-class combo groups are too small to span
  three splits). Raises on malformed stems (kept guard).
- `compute_split(stems: list[str], train_frac: float, val_frac: float, seed: int) -> dict` —
  per-category seeded shuffle (private `random.Random(seed)`), `round()` allocation, sorted
  outputs. No tiny-category guard (removed by user).
- `write_manifests(split: dict) -> None` / `read_manifests() -> dict` — use the module-global
  `splits_dir`; tests redirect it with `monkeypatch.setattr`.
- `write_data_yaml(dataset_dir: Path, class_names: list[str], split_paths: dict[str, str]) -> Path`
- `build_yolo_layout(split: dict[str, list[str]], class_names: list[str]) -> Path` — copies
  (never moves) from the module-global raw dirs into `yolo_dir`.
- CLI (`__main__` inline): `--force`, `--train-frac 0.70`, `--val-frac 0.15`, `--seed 42`.
  Guards `data/yolo` with `FileExistsError` unless `--force` (kept guard).

`scripts/perception/train.py` — pure CLI script (no importable functions):

- args: `--data data/yolo/data.yaml`, `--name stage1_baseline`, `--epochs 200`,
  `--device cpu` (pass `mps` locally, `0` on CUDA; **"auto" is NOT a valid ultralytics
  device**), `--model-name yolo26m-seg.pt`, `--project`, `--resume`, `--seed 42`.
- fixed training policy dict: `imgsz=640, patience=50, mosaic=0.0, degrees=180.0, flipud=0.5,
fliplr=0.5, scale=0.1, hsv_h/s/v=0.0`. `--project` defaults to `runs/train` locally and
  `/content/waferdetect_runs/train` when the repo is run from mounted Colab Drive, because
  Drive's FUSE layer can reject direct `.pt` checkpoint writes.
  **`mosaic=0.0` is the single most important line** — mosaicked quarter-wafers are physically
  impossible scenes. Rotation/flips are safe because wafer scenes are rotation/mirror valid and
  ultralytics transforms polygons with pixels. HSV off because images are near-binary.

`scripts/perception/evaluate.py`:

- module globals: `classes_file`, `yolo_dir`, `runs_dir`, `combo_token = "_combo_"`,
  `tiny_token = "_edge_scratch_tiny"`.
- `subset_image_list(images_dir: Path, token: str) -> list[Path]` (empty → `[]`, no raise)
- `write_subset_yaml(base_yaml, subset_name, image_paths, out_dir) -> Path` — the subset trick:
  ultralytics dataset yamls accept a **txt file of absolute image paths**; labels resolve by
  the `/images/` → `/labels/` path swap; `train` and `val` both point at the list file because
  the yaml validator requires both keys.
- `metrics_to_dict(metrics, class_names) -> dict` — per-class AP arrays are dense; decode
  positions through `metrics.box.ap_class_index` (never assume position = class ID).
- `render_report(results) -> str` — markdown with per-class table.
- CLI: `--model-path` (default `runs/train/stage1_baseline/weights/best.pt`), `--name`,
  `--data`. Runs full test split (`split="test"`, plots → confusion matrix), then combo and
  edge_scratch_tiny subsets; writes `runs/eval/<name>/{metrics.json,report.md}`.
  Subset images intentionally always come from `data/yolo/images/test` (the raw test split) —
  correct for all stages.

`scripts/datagen/fields.py` — Stage 2 field library:

- `disk_coordinates(grid: int) -> tuple`, `gaussian_blob(...)`, `annulus(...)`, `angular_mask(...)`,
  `curve_band(...)`
- `field_builders` — 24 category builders: 20 plain classes plus
  `edge_scratch_{tiny,small,medium,large}`
- `category_class(category: str) -> str` maps all edge-scratch size categories to
  `edge_scratch`

`scripts/datagen/labels.py` — field-to-label layer:

- `field_mask(field, threshold_frac=0.35) -> np.ndarray`
- `field_to_polygon(field, threshold_frac=0.35, tolerance_frac=0.01) -> list[tuple[float, float]]`
  (≤30 vertices; padded contours for rim-touching masks; convex hull for disjoint components)
- `wafer_to_image(points, wafer_frac) -> list[tuple[float, float]]`
- `yolo_line(class_id, polygon) -> str`
- `mask_iou(a, b) -> float`

`scripts/datagen/generator.py` — synthetic wafer generator:

- module globals: `image_size = 640`, `grid_size = 256`, `wafer_frac = 0.97`,
  combo weights/IoU retry controls, dot-count ranges
- `sample_dots`, `background_dots`, `quantize_dots`, `render`, `choose_categories`,
  `generate_sample`, `sample_name`
- CLI writes `images/`, `labels/`, and `manifest.json`

`scripts/datagen/review.py`:

- `write_review_sheets(generated_dir: Path, per_category: int = 5) -> Path`

`scripts/datagen/layout.py`:

- `raw_test_images = Path("data/yolo/images/test")`
- `build_layout(generated_dir, out_dir, val_frac, seed, limit=0) -> Path`; train/val comes from
  generated data, `test:` in `data.yaml` points at the frozen raw YOLO test split

`scripts/baselines/classical.py`:

- `dot_coordinates`, `density_features`, `radon_features`, `feature_vector`
- CLI trains StandardScaler + RBF SVM on raw single-pattern train wafers and writes
  `runs/baselines/classical/metrics.json`; combo exact-match is recorded as 0

`scripts/baselines/resnet.py`:

- `multi_hot(label_path, n_classes) -> torch.Tensor`
- `WaferDataset(images_dir, labels_dir, n_classes)`
- `evaluate(model, loader, device)` plus CLI for ResNet-18 multi-label training/evaluation

`scripts/datagen/physics/thermal.py` — Stage 3 thermal stress/slip model:

- `masked_laplacian(temperature, disk) -> np.ndarray` — conservative insulated disk exchange
- `solve_heat(...) -> np.ndarray` — explicit-FDM lamp ramp, rim cooling, lift-pin sinks, optional
  cold spot
- `thermal_stress(temperature, disk) -> np.ndarray`
- `slip_probability(temperature, disk, sharpness=2.0) -> np.ndarray`
- `slip_lines_field(grid, rng) -> np.ndarray`

`scripts/datagen/physics/spincoat.py`:

- `film_thickness(spin_speed, evaporation, duration) -> float`
- `thickness_deviation(grid, mode, amplitude, rng) -> np.ndarray`, modes:
  `center`, `annular`, `tilt`, `edge_bead`
- `deviation_to_probability(deviation, amplitude) -> np.ndarray`
- `spincoat_field(grid, rng, mode) -> np.ndarray`

`scripts/datagen/physics/cmp.py`:

- `removal_profile(grid, mode, amplitude, velocity_mismatch, rng) -> np.ndarray`, modes:
  `center`, `edge_ring`, `donut`
- `cmp_field(grid, rng, mode) -> np.ndarray`

`scripts/datagen/physics/shotgrid.py`:

- `intra_field_mask(grid, cell, offset, spot, spot_radius) -> np.ndarray`
- `shot_grid_physics_field(grid, rng) -> np.ndarray`

`scripts/datagen/physics/builders.py`:

- `physics_field_builders` covers exactly `slip_lines`, `center`, `donut`, `edge_ring`,
  `gradient`, `shot_grid`; center/donut/edge_ring randomly choose spin-coat vs. CMP.

`scripts/datagen/generator.py` Stage 3 addition:

- `generate_sample(..., physics_frac: float = 0.0)` and CLI `--physics-frac`; default `0.0`
  preserves Stage 2 behavior.

`scripts/wm811k/convert.py` — Stage 4 WM-811K converter:

- `wm811k_class_map` — exact closed mapping: Center, Donut, Edge-Ring, Edge-Loc, Scratch,
  Random, Loc, Near-full, none
- `flatten_label(value) -> str | None`
- `convert(pickle_path: Path, parquet_path: Path) -> pd.DataFrame`
- `load_map(row) -> np.ndarray`

`scripts/wm811k/manifests.py`:

- `build_manifests(frame, seed, eval_cap=2000, calibration_per_class=50,
  fewshot_reserve=600, none_calibration=200, none_eval=2000) -> dict[str, list[int]]`
- `write_manifests(manifests, frame, out_dir) -> None`
- `read_manifest(path: Path) -> list[int]`

`scripts/wm811k/render.py`:

- `die_dots(wafer_map: np.ndarray) -> np.ndarray`
- `render_manifest(frame, indices, out_dir, seed) -> None`; uses the Stage 2 renderer verbatim
  and stems `{index:06d}_{failure_type}.jpg`

`scripts/wm811k/zero_shot.py`:

- `defect_classes` — the 8 mapped defect classes, excluding `none`
- `reduce_detections(class_ids, confidences, class_names, threshold) -> str`
- `predict_directory(model, images_dir, batch_size=64) -> dict`
- `choose_threshold(predictions, truths, class_names) -> tuple[float, float]`
- `score(predictions, truths, class_names, threshold) -> dict`
- `truths_from_directory(images_dir) -> dict`

`scripts/wm811k/pseudolabel.py`:

- `pseudo_polygon(wafer_map, class_name) -> list[tuple[float, float]]`
- `pseudo_label_line(wafer_map, class_name, class_names) -> str`
- CLI builds complete few-shot YOLO layouts under `data/wm811k/fewshot_<budget>_<seed>/`

`scripts/analytics/diegrid.py` — Stage 5 virtual die grid:

- module globals: `wafer_radius_mm = 150.0`, `edge_exclusion_mm = 3.0`,
  `default_die_mm = 6.0`, `radial_bins = 10`
- `die_centers(die_mm=6.0) -> np.ndarray`
- `failed_dies(dots, die_mm=6.0) -> np.ndarray`
- `wafer_summary(dots, die_mm=6.0) -> dict`
- `radial_yield(dots, die_mm=6.0, bins=10) -> list[float]`
- `zone_yields(dots, die_mm=6.0) -> dict`

`scripts/analytics/yieldmodels.py`:

- `poisson_yield(defect_density, die_area) -> float`
- `negative_binomial_yield(defect_density, die_area, alpha) -> float`
- `estimate_defect_density(failed_fraction, die_area) -> float`
- `quadrat_counts(dots, quadrats=8) -> np.ndarray`
- `estimate_alpha(counts) -> float | None`

`scripts/datagen/labels.py` Stage 5 addition:

- `image_to_wafer(points, wafer_frac) -> list[tuple[float, float]]`

`scripts/analytics/economics.py`:

- die value is NOT a module global — it lives as the `die_value: float = 25.0` parameter
  default on `decompose` and on the diagnosis CLI (`--die-value`); a 2026-07-02 cleanup
  removed the former `die_value_dollars` global (importing it broke the suite once — fixed)
- `points_in_polygon(points, polygon_image) -> np.ndarray`
- `decompose(dots, polygons_image, die_mm=6.0, die_value=25.0) -> dict`
- `pareto(items) -> list[tuple[str, float]]`

`scripts/analytics/kinematics.py`:

- `radon_orientation(points) -> float`
- `line_deviation(points) -> float`
- `circle_fit(points) -> tuple[float, float, float]`
- `scratch_verdict(points) -> dict`

`scripts/analytics/fieldanalysis.py`:

- `shot_matrices(fail_grid, field_rows, field_cols) -> tuple[np.ndarray, np.ndarray]`
- `field_verdict(per_shot, intra, z_threshold=3.0) -> dict`

`scripts/analytics/knowledge_base.yaml`:

- covers all 21 `classes.txt` classes with mechanism, process steps, tool families,
  severity weight, and action.

`scripts/analytics/diagnosis.py`:

- `load_knowledge_base(path) -> dict`
- `polygon_area(polygon) -> float`
- `diagnose(dots, detections, kb, die_mm=6.0, die_value=25.0) -> dict`
- CLI supports exactly one of `--labels` (ground-truth mode) or `--model-path` (lazy YOLO).

Tests (149): Stage 1/2/3/4 tests plus `test_diegrid.py`, `test_yieldmodels.py`,
`test_economics.py`, `test_kinematics.py`, `test_fieldanalysis.py`, and `test_diagnosis.py`.
There are deliberately NO tests for CLI/argparse plumbing, training loops, or real WM-811K data.

Other repo items: `colab/stage1_baseline.md` (A100 recipe); root-level `experiment.ipynb`,
`wafe_map.py`, `plot_annotated.py` are the user's exploratory scripts — **do not modify,
"fix", or delete them**; `.superpowers/` is orchestration scratch — ignore it.

## 5. Load-bearing decisions and their reasons

- **Detection/segmentation over classification** — combos require multiple labeled instances
  per wafer; masks feed the future analytics layer (area, orientation, per-defect $-loss).
- **Frozen raw test split (seed 42) as the universal bar** — Stage 2's generated-data layouts
  write a `data.yaml` whose `test:` key is the absolute path to `data/yolo/images/test`, so
  scores across stages are directly comparable. Never retune or regenerate this split.
- **Model: YOLO26m-seg default** (user's choice; s/l variants only as capacity ablation),
  COCO-pretrained. mAP conventions: report box AND mask, mAP50 and mAP50-95, per-class; mask
  mAP50 is the headline; combo-subset-vs-overall gap is the honesty metric.
- **Generator design (Stage 2): the intensity field is the single source of truth** — the same
  2D field over the unit disk both samples the dots and produces the polygon label
  (threshold 35% of max → contour; convex hull when components are disjoint). Pixels and labels
  cannot drift apart. Wafer coords [-1,1] map to image coords via `0.5 + u*wafer_frac/2`,
  `wafer_frac = 0.97` — labels land in [0.015, 0.985] by construction.
- **Combo stratification pooled** (see §4 `stem_category`) — documented spec deviation.
- **Stage-1 baselines deferred**: classical zone-density+Radon+SVM (Wu et al. 2015 — the
  historical WM-811K method; the user independently prototyped these features) and ResNet-18
  multi-label ride with Stage 2. **Mask R-CNN was cut** pending user sign-off (cost/value).
- **Physics simulations are current-scope product features** (Stage 3): thermal→slip-lines,
  spin-coat/CMP radial models, scratch arc kinematics (Radon-based orientation), shot-grid
  analysis — all interactive on the dashboard later. Group B spatial statistics = future F1;
  Group D virtual fab = far-future F2; A5 (FEM/CFD) and D4 (discrete-event fab) permanently cut.
- **WM-811K evaluation is image-level only** (no real polygons exist); fine-tuning uses
  DBSCAN-derived pseudo-polygons but reported metrics never trust them.

## 6. Coding style — MANDATORY, first pass, no exceptions

The user rewrote generated code once to enforce this and does not want to again.

**Structure & configuration**

- NO central config module, no pydantic settings, no config.py. Each script owns its paths as
  **lowercase snake_case module-level globals** (`classes_file = Path("data/raw/classes.txt")`)
  and takes tunables (seed, fractions, epochs, model name, physics constants) as argparse
  arguments with defaults. Shared defaults (e.g. seed 42) are repeated per script, not
  centralized.
- Lowercase snake_case for ALL module-level constants and globals in `scripts/` — never
  UPPER_SNAKE_CASE.
- Relative paths assume repo-root cwd; invoke everything as `uv run python -m scripts....`.
- All code lives under `scripts/` (no `src/`, no installed package, no build system).
- CLI entry is an inline `if __name__ == "__main__":` block with argparse — no `main()`
  wrapper. Every argument carries `type=` and a help string ending `"(default: X)."`.
  NEVER combine `type=` with `action="store_true"` (argparse crashes).

**Validation & errors**

- Minimal validation: rely on natural Python exceptions — `int()` → ValueError, `open()`/
  `Path.read_text()` → FileNotFoundError, `zip(strict=True)` → ValueError. Keep only
  operationally meaningful guards (a format check with a clear message; a `--force`
  FileExistsError guard protecting built artifacts). No precondition walls, no error-context
  threading, no catch-all handlers, never silently swallow, no fallbacks unless the user asks.
- Exceptions are specific types with clear, actionable f-string messages.

**Tests**

- Lean: happy path + natural-error cases only. NO tests for CLI/argparse plumbing, training
  loops, or constant values. Redirect module path globals via
  `monkeypatch.setattr(module, "global_name", tmp_path)`. Tests may read the real `data/raw`
  files. Run `uv run pytest -q` (full suite) before declaring any task done.

**Typing & formatting**

- Full type hints on every signature; `|` unions (`str | None`), never `Optional`. Bare `dict`
  returns are fine — do not over-parameterize generics.
- No docstrings (only to state a truly non-obvious constraint). Comments explain _why_ only,
  on the line above, brief. Blank lines separate logical steps inside functions.
- f-strings exclusively. No wildcard imports. No magic numbers — name them (module global or
  argparse default). Plain `@dataclass()` — not frozen. `functools.partial` over lambdas for
  partial application. `os.makedirs(path, exist_ok=True)` before writing.
- `tqdm(iterable, desc="...")` on long loops; training loops use
  `progress_bar.set_postfix(loss=f"{loss:.6f}")`.

**PyTorch (for baseline/physics/analytics code)**

- Device-agnostic (`.to(device)`, never hardcoded cuda), `torch.inference_mode()` for eval,
  explicit `model.train()`/`model.eval()`, `optimizer.zero_grad()` before the forward pass,
  accumulate losses with `.item()`, explicit `dim=` kwargs, inline tensor-shape comments
  (`# shape: (batch, 21)`), `nn.` layers in `__init__` / `F.` functional in `forward`.

**Tooling**

- `uv` exclusively: `uv add`, `uv add --dev`, `uv run`, `uv sync`. Never pip/conda/poetry.
  `uv run ruff check scripts tests` should stay clean.

## 7. Git and workflow rules — ABSOLUTE

- **NEVER run `git commit`, `git push`, `git add`, `git mv`, or any state-mutating git
  command. No staging. No suggested commit messages. No branch creation.** The user handles
  all version control personally. Read-only git (status/log/diff) is fine.
- Do not modify `data/raw/` contents, the split manifests, the user's root scripts, or
  `.gitignore` (the user's `data/` and `docs/` blanket ignores are their deliberate choice).
- Do not launch long training runs unprompted — heavy compute (full trainings, sweeps,
  WM-811K) belongs on the user's Colab A100 (`colab/*.md` docs carry the exact commands);
  local Mac (MPS) is for development, unit tests, and short smoke runs only.
- Human gates are real stops: Stage 2's pilot review sheets must be approved by the user
  before the 10k generation; exit-gate reviews happen with the user.
- Work stage-by-stage from the plan; the plan's task order is deliberate. Report deviations
  explicitly rather than improvising.

## 8. Next work

### Stage 7 implementation (plan: `docs/superpowers/plans/2026-07-02-stage7-fastapi.md`)

Six tasks, all in `scripts/api/`: (1) deps (`fastapi`, `uvicorn`, `python-multipart`; dev
`httpx`) + `plots.py` (field/image → base64 PNG) + `main.py` — `create_app(model_path | None)`
factory loading YOLO into `app.state.model`, CORS for Vite (localhost:5173), `/api/health`,
inline `__main__` argparse → `uvicorn.run` (`--model-path` default
`runs/train/stage1_baseline/weights/best.pt`), plus six one-line router stubs so the factory
never changes again; (2) `routers/wafers.py` — manifest-backed browse/filter/detail +
`FileResponse` images; (3) `routers/detect.py` — pure `detections_to_response` helper (reuses
Stage 5 geometry), stem-or-upload exactly-one, **503 when no model** (all other endpoints work
model-free; tests use `create_app(None)`); (4) `routers/diagnose.py` + `routers/yields.py`
(NOT `yield.py` — Python keyword) — §7.4 report, per-wafer yield panel, `/api/yield/pareto`
with `limit`; shared `wafer_dots_and_detections`; (5) `routers/generate.py` +
`routers/physics.py` — pydantic `Literal` modes for auto-422, thermal chain returns
temperature/stress/slip-probability PNGs + rendered sample, shotgrid composes
`intra_field_mask`/inter-field logic with fixed `cell = 0.25` (6×6-die fields on a 48-die
grid) and returns the Stage 5 `field_verdict` — physics → pattern → analysis in one response;
(6) live-server walkthrough against the real Stage 1 weights + `/docs` QA → **human gate**
(response shapes reviewed before Stage 8 builds on them).

Rule: the API layer contains NO business logic — every endpoint delegates to existing
modules. Physics endpoints stay under 3 s (thermal at `solver_grid = 96`). Expected suite
total after Stage 7: 165 tests.

### Stage 5 report review gate

Code tasks are complete. Remaining execution is user review/tuning:

1. Review sample reports already generated in `runs/analytics/`:
   `0101_scratch.json`, `0001_center.json`, and `0481_combo_half_wafer+donut.json`.
2. Sanity-check scratch kinematics against `data/raw/overlays/0101_scratch.jpg`.
3. Check the combo report has separate region dollar attributions and sensible knowledge-base text.
4. Tune constants only if needed: the `--die-value` CLI default, kinematics thresholds
   (`straightness_tolerance` — see the off_axis_arc note in the review), die size, or YAML
   action text.

No new dependencies were added for Stage 5.

### Stage 4 execution gate

Code tasks are complete. Remaining execution requires external data and trained weights:

1. Put the user-downloaded WM-811K pickle at `data/wm811k/LSWMD.pkl`.
2. Provide trained weights, preferably the Stage 2 production model.
3. Follow `colab/stage4_wm811k.md`: convert to `labeled.parquet`, build manifests, render
   calibration/eval images, run zero-shot, run few-shot sweeps, and run the die-grid
   quantization ablation.
4. Exit-gate review: report zero-shot defect macro-F1, none-FPR, confusion matrix,
   few-shot budget curves with 3-seed error bars, and the quantization ablation delta.

Hard rules: image-level metrics only; pseudo-polygons exist only for fine-tuning layouts and are
never used as reported ground truth. Tests run on tiny fixtures, never the real 2 GB pickle.

### Stage 3 visual gate

Code tasks are complete. Remaining execution is gated:

1. Generate the physics pilot:
   `uv run python -m scripts.datagen.generator --out-dir data/generated/physics_pilot --count 300 --combo-frac 0.0 --physics-frac 1.0 --seed 42`
2. Render review sheets:
   `uv run python -m scripts.datagen.review --generated-dir data/generated/physics_pilot`
3. STOP for user approval of `data/generated/physics_pilot/review/*.png`, focused on
   `slip_lines`, `center`, `donut`, `edge_ring`, `gradient`, and `shot_grid`.
4. With the user, choose the production `--physics-frac` for future generated datasets
   (recommendation remains 0.5).

Key contracts: every physics builder has the Stage 2 field signature
`(grid, rng) -> np.ndarray` (non-negative, zero off-disk), so labeling/rendering/review work
unchanged. Physics tests are structural, never absolute-calibrated.

### Still-pending execution (Stages 1–2, user/A100 gated)

1. Stage 2 Gate A: generate the heuristic pilot
   (`uv run python -m scripts.datagen.generator --out-dir data/generated/pilot --count 1000 --seed 42`),
   render review sheets, user approves before 10k.
2. One Colab A100 session: Stage 1 baseline training + eval (`colab/stage1_baseline.md` —
   the Gate B measuring stick), then `colab/stage2_data_engine.md` (10k generation, scaling
   study {500,1k,2k,5k,10k}, ResNet baseline).
3. Exit-gate review: Gate B (500-generated model ≥ Stage 1 baseline mask mAP50), Gate C
   (scaling curve), Gate D (detector vs. SVM 0.8194-singles/0-combo vs. ResNet table).

Stage 2 deps added: `pillow`, `scikit-learn`, `torchvision`, `tqdm`.

## 9. Roadmap after Stage 7

Stage 6 (deferred, still owed): stream simulator + Shewhart/EWMA/CUSUM, plus its
`/api/monitor/*` router. Stage 8: React/Vite/Tailwind dashboard (six views; user's React
conventions: TS, typed props interfaces, Tailwind-only with dark: variants, Recharts,
react-icons; Line Monitor view depends on Stage 6). Stage 9: polish/release. Then F1/F2.
