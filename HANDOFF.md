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
mechanisms, a root-cause + yield-economics analytics engine, SPC excursion monitoring, and a
FastAPI + React dashboard. Framing is
**product-for-fabs first, research second** — every component answers a question a yield
engineer actually asks.

```
Layer 0  DATA LIBRARY     intensity fields + rendering (training-data generation dropped 2026-07-04)
Layer 1  PERCEPTION       YOLO26-seg instance segmentation (baselines: SVM)
Layer 3  ANALYTICS        geometry, kinematics, knowledge base, yield $-economics
Layer 4  MONITORING       stream simulator -> EWMA/CUSUM -> alarms
Layer 5  DASHBOARD        FastAPI + React/Vite/Tailwind (6 views incl. interactive Physics Lab)
FUTURE   F1 spatial statistics (CSR, similarity, stacked maps)   F2 virtual fab (commonality)
```

## 2. Current status (updated 2026-07-02)

- **Stage 1 (foundation & baseline): code COMPLETE, 27/27 tests passing.** The full baseline
  training run is PENDING — the user runs it on Colab A100.
  A local overfit smoke run reached epoch 22 with box mAP50 ≈ 0.47 and rising before being
  intentionally stopped — the pipeline mechanically works (YOLO26 weights download, MPS
  training, label ingestion all verified).
- **Stage 2 (data engine): code COMPLETE, 80/80 tests passing.** Implemented
  `datagen/fields.py`, `datagen/labels.py`, `datagen/generator.py`, `datagen/review.py`,
  `datagen/layout.py`, `baselines/classical.py`, and tests. Local smoke verified generator/review/layout CLIs. Classical
  baseline was run locally: singles accuracy 0.8194, singles macro-F1 0.7911, combo exact-match
  0 by construction. (2026-07-04: the pilot/10k/scaling-study direction was dropped and its
  pipeline deleted — see §8.)
- **Stage 3 (physics suite): code COMPLETE, 108/108 tests passing.** Implemented
  `scripts/datagen/physics/{thermal,spincoat,cmp,shotgrid,builders}.py`, generator
  `physics_frac` integration, and tests. (2026-07-04: `builders.py` and the `physics_frac`
  generation integration were deleted with the generated-data direction; the four simulators
  remain and power the dashboard's Physics Lab.)
- **Stage 5 (analytics engine): code COMPLETE, 149/149 tests passing.** Implemented
  `scripts/analytics/{diegrid,yieldmodels,economics,kinematics,fieldanalysis,diagnosis}.py`,
  `knowledge_base.yaml`, `image_to_wafer`, and tests. Generated sample ground-truth reports:
  `runs/analytics/0101_scratch.json` ($1606), `runs/analytics/0001_center.json` ($3194),
  `runs/analytics/0481_combo_half_wafer+donut.json` ($19064). Remaining Stage 5 work is the
  human report review/tuning gate.
- **Stage 7 (FastAPI backend): code COMPLETE, 165/165 tests passing.** Implemented
  `scripts/api/{main,plots}.py` plus routers for wafers, yield, and physics
  (detect, diagnose, and generate routers existed until 2026-07-04: `/api/detect` and
  `/api/generate` were deleted — `/api/analyze` is the inference endpoint now — and
  `diagnose.py` merged into yields). Added FastAPI/Uvicorn/multipart deps and `httpx` for TestClient.
  The API can run model-free for all non-inference endpoints; `/api/analyze` returns 503 when
  started without weights. **Stage 6 (monitoring) was deliberately skipped for now by user
  decision** — `/api/monitor/*` endpoints remain absent until Stage 6 adds its router later.
- **Stage 1 baseline TRAINED (2026-07-02, A100):** test-split mask mAP50 **0.842** (≥ 0.80
  target met), box mAP50 0.896; combo subset mask mAP50 0.670 (17-point gap — misses the
  ≤10-point criterion; swirl masks are the main failure at 0.151, plus random-in-combo and
  donut masks); edge_scratch_tiny subset 0.995. **0.842 is the project's headline model
  result** (formerly the Gate B bar; the generated-data comparison it anchored was dropped
  2026-07-04). Weights in
  `runs/train/yolo26x_detector/weights/best.pt` (user's `waferdetect_runs/`). Known data wart:
  ultralytics deduped duplicate label lines in `0170_swirl` (3) and one combo file (1).
- **Stage 8 (dashboard frontend): code COMPLETE + UI REDESIGN (2026-07-02).** Frontend tests
  were removed entirely on 2026-07-04 by user decision (vitest/jsdom/testing-library
  uninstalled; `npm run build` = tsc is the only frontend gate). Python suite: 141/141.
  React 19 + TypeScript + Vite + Tailwind v4 in
  `frontend/`, redesigned dark-native ("fab control room": cyan/violet on near-black, glassy
  cards, scan-line loading animation, count-up hero numbers). The home view is now **Analyze**
  (`views/Analyze.tsx`): boots on demo wafer `0487_combo_random+edge_loc+comet`
  (changed from `0101_scratch` 2026-07-04), auto-fetches on wafer pick or
  image upload (no button), two canvas tabs (detections / defect dots) + always-visible
  Radon sinogram side panel,
  headline loss+yield front and center, inline expandable report — the separate Detection
  Viewer and Reports views were deleted. Backed by new `POST /api/analyze` (stem XOR file →
  YOLO detections + diagnosis + yield + display dots + sinogram in one response). Fixed
  `/api/yield/wafer/{stem}` missing `total_loss_dollars`/`yield_random` (crashed Yield
  Analytics). Live-verified via curl (stem + upload paths). Remaining: human browser gate.
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
  6-decimal coordinates.
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
- The dataset is synthetic (rendered, perfectly balanced).

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

- args: `--data data/yolo/data.yaml`, `--name yolo26x_detector`, `--epochs 200`,
  `--device cpu` (pass `mps` locally, `0` on CUDA; **"auto" is NOT a valid ultralytics
  device**), `--model-name yolo26x-seg.pt`, `--project`, `--resume`, `--seed 42`.
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
- CLI: `--model-path` (default `runs/train/yolo26x_detector/weights/best.pt`), `--name`,
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

`scripts/datagen/generator.py` — rendering library (2026-07-04: the user dropped the
generated-training-data direction; the dataset-production surface — `generate_sample`,
`choose_categories`, `sample_name`, `background_dots`, the CLI — plus `review.py`,
`layout.py`, and `physics/builders.py` were all deleted, along with `data/generated/*`. What remains is the library other layers use):

- module globals: `image_size = 640`, `grid_size = 256`, `wafer_frac = 0.97`
- `sample_dots`, `quantize_dots`, `render` (Physics Lab); `wafer_frac` (analytics + analyze)

`scripts/baselines/classical.py`:

- `dot_coordinates`, `density_features`, `radon_features`, `feature_vector`
- CLI trains StandardScaler + RBF SVM on raw single-pattern train wafers and writes
  `runs/baselines/classical/metrics.json`; combo exact-match is recorded as 0

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

`scripts/analytics/diegrid.py` — Stage 5 virtual die grid:

- module globals: `default_wafer_radius_mm = 150.0`, `edge_exclusion_mm = 3.0`,
  `default_die_mm = 6.0`, `radial_bins = 10` (2026-07-04: wafer radius became a
  per-function parameter so the dashboard can vary wafer size; the global was renamed)
- `die_centers(die_mm=6.0, wafer_radius_mm=150.0) -> np.ndarray`
- `failed_dies(dots, die_mm=6.0, wafer_radius_mm=150.0) -> np.ndarray`
- `wafer_summary(dots, die_mm=6.0, wafer_radius_mm=150.0) -> dict`
- `radial_yield(dots, die_mm=6.0, bins=10, wafer_radius_mm=150.0) -> list[float]`
- `zone_yields(dots, die_mm=6.0, wafer_radius_mm=150.0) -> dict`

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
- `decompose(dots, polygons_image, die_mm=6.0, die_value=25.0, wafer_radius_mm=150.0) -> dict`
- `pareto(items) -> list[tuple[str, float]]`

`scripts/analytics/kinematics.py`:

- `raster_size = 128` (raised from 64 on 2026-07-04)
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
- `polygon_centroid_radius(polygon) -> float`
- `diagnose(dots, detections, kb, die_mm=6.0, die_value=25.0) -> dict`
- CLI supports exactly one of `--labels` (ground-truth mode) or `--model-path` (lazy YOLO).

`scripts/api/plots.py`:

- `field_png(field, cmap="viridis") -> str` — base64 PNG for server-rendered heatmaps
  (colorbar removed 2026-07-04 by user decision; edge-to-edge render).
- `image_png(image) -> str` — base64 PNG for generated wafer maps.

`scripts/api/main.py`:

- `create_app(model_path: Path | None) -> FastAPI`; loads YOLO once into `app.state.model`
  when a path is provided, otherwise leaves non-detection endpoints available.
- CLI: `uv run python -m scripts.api.main --model-path <weights> --host 127.0.0.1 --port 8000`.

`scripts/api/routers/wafers.py`:

- `GET /api/wafers?split=&category=&offset=0&limit=50`
- `GET /api/wafers/{stem}`
- `GET /api/wafers/{stem}/image`

`scripts/api/routers/yields.py`:

- `wafer_dots_and_detections(stem) -> tuple` (moved here when `routers/diagnose.py` was
  deleted 2026-07-04; the ground-truth `GET /api/diagnose/{stem}` endpoint was removed —
  `/api/analyze` covers full reports via model predictions)
- `GET /api/yield/wafer/{stem}?die_mm=6&die_value=25&wafer_radius_mm=150`
- `POST /api/analyze` and `diagnose()` also take `wafer_radius_mm=150.0`; the Analyze view
  exposes all three what-if knobs (wafer-size preset dropdown + custom, die-size slider,
  die-value input with an implied-wafer-value warning), debounced 500 ms
- `analyze.py` caches image-derived artifacts (dots, detections, image/sinogram PNGs) in a
  module-level LRU (`analysis_cache`, cap 16) keyed by stem or upload SHA-256 — what-if
  parameter changes skip YOLO entirely and recompute only diagnose/radial/zones
  (measured live 2026-07-04: ~0.92 s cold → ~0.03 s on a hit)
- `GET /api/yield/pareto?split=test&limit=0&die_value=25`

`scripts/api/routers/physics.py`:

- `POST /api/physics/thermal`
- `POST /api/physics/spincoat`
- `POST /api/physics/cmp`
- `POST /api/physics/shotgrid`

Tests (165): Stage 1/2/3 tests plus analytics and API tests. API tests use
`create_app(None)` and stay weight-free.
There are deliberately NO tests for CLI/argparse plumbing, training loops, or trained model weights.

Other repo items: root-level `experiment.ipynb`,
`wafe_map.py`, `plot_annotated.py` are the user's exploratory scripts — **do not modify,
"fix", or delete them**; `.superpowers/` is orchestration scratch — ignore it.

`frontend/` — Stage 8 dashboard:

- Vite/React/Tailwind configs: `package.json`, `vite.config.ts`, three tsconfigs,
  `index.html`, `src/index.css` (flat theme background, scan/fade keyframes).
- `src/api.ts` — typed Stage 7/analyze response interfaces, relative `/api` client,
  `waferImageUrl`, `waferCategories`, and small `useApi` hook.
- `src/format.ts` — `dollars`, `percent`, `png`. `src/ui.ts` — shared Tailwind class
  constants (card/select/input/buttons/chip). `src/useCountUp.ts` — rAF count-up hook.
- `src/App.tsx` — dark sidebar shell, routes (`/` Analyze, `/explorer`, `/yield`,
  `/physics`); the disabled Line Monitor Stage 6 badge was removed 2026-07-04 (re-add a
  nav entry when Stage 6 ships).
- Shared components: `components/WaferCanvas.tsx` (circular canvas, polygon overlays,
  dot markers, scan animation), `MetricTile.tsx`, `FieldHeatmap.tsx`, `DiagnosisCard.tsx`,
  `ParamField.tsx`.
- Views: `views/Analyze.tsx` (home: upload + gallery picker + view tabs + inline report),
  `WaferExplorer.tsx`, `YieldAnalytics.tsx`, `PhysicsLab.tsx`.
- No frontend tests (removed 2026-07-04 by user decision); `npm run build` is the gate.

## 5. Load-bearing decisions and their reasons

- **Detection/segmentation over classification** — combos require multiple labeled instances
  per wafer; masks feed the future analytics layer (area, orientation, per-defect $-loss).
- **Frozen raw test split (seed 42) as the universal bar** — Stage 2's generated-data layouts
  write a `data.yaml` whose `test:` key is the absolute path to `data/yolo/images/test`, so
  scores across stages are directly comparable. Never retune or regenerate this split.
- **Model: YOLO26x-seg default** (user's choice),
  COCO-pretrained. mAP conventions: report box AND mask, mAP50 and mAP50-95, per-class; mask
  mAP50 is the headline; combo-subset-vs-overall gap is the honesty metric.
- **Generator design (Stage 2): the intensity field is the single source of truth** — the same
  2D field over the unit disk both samples the dots and produces the polygon label
  (threshold 35% of max → contour; convex hull when components are disjoint). Pixels and labels
  cannot drift apart. Wafer coordinates [-1,1] map to image coordinates via `0.5 + u*wafer_frac/2`,
  `wafer_frac = 0.97` — labels land in [0.015, 0.985] by construction.
- **Combo stratification pooled** (see §4 `stem_category`) — documented spec deviation.
- **Stage-1 baselines deferred**: classical zone-density+Radon+SVM (Wu et al. 2015 — the
  historical wafer-map method; the user independently prototyped these features)
  multi-label ride with Stage 2. **Mask R-CNN was cut** pending user sign-off (cost/value).
- **Physics simulations are current-scope product features** (Stage 3): thermal→slip-lines,
  spin-coat/CMP radial models, scratch arc kinematics (Radon-based orientation), shot-grid
  analysis — all interactive on the dashboard later. Group B spatial statistics = future F1;
  Group D virtual fab = far-future F2; A5 (FEM/CFD) and D4 (discrete-event fab) permanently cut.

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
- Do not launch long training runs unprompted — heavy compute (full trainings, sweeps)
  belongs on the user's Colab A100;
  local Mac (MPS) is for development, unit tests, and short smoke runs only.
- Work stage-by-stage from the plan; the plan's task order is deliberate. Report deviations
  explicitly rather than improvising.

## 8. Next work

### Stage 8 manual dashboard gate

Code tasks are complete. Remaining work is manual browser QA:

1. Start the backend:
   `uv run python -m scripts.api.main --model-path waferdetect_runs/train/yolo26x_detector/weights/best.pt`
2. Start the frontend:
   `cd frontend && npm run dev`
3. Walk the Analyze home view (boot on demo wafer, gallery pick, image upload, both canvas
   tabs + sinogram panel, what-if knobs, expandable report), Explorer filters, Yield
   Analytics Pareto/wafer panel, and all four Physics Lab tabs.
4. Check a narrow viewport (the UI is dark-native; there is no light theme).
5. STOP for user review of response shapes and dashboard ergonomics before Stage 9.

### Stage 7 live API gate

Code tasks are complete. Remaining manual gate requires the real Stage 1 checkpoint locally:

1. Put the trained checkpoint at `runs/train/yolo26x_detector/weights/best.pt`.
2. Start the server:
   `uv run python -m scripts.api.main --model-path runs/train/yolo26x_detector/weights/best.pt`
3. Review `http://127.0.0.1:8000/docs`.
4. Exercise `/api/analyze?stem=0101_scratch`,
   `/api/yield/pareto?split=test&limit=20`, and `/api/physics/thermal`.
5. STOP for user review of response shapes before Stage 8 builds the dashboard.

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

### Dropped direction (2026-07-04): training on generated data

The user dropped the generated-training-data direction entirely — no 10k generation, no
scaling study, no pilot gates, no physics-informed generation modes, no Gates A–D. Deleted:
`datagen/{layout,review}.py`, `datagen/physics/builders.py`, the generator's dataset CLI and
`generate_sample`/`choose_categories`/`sample_name`/`background_dots`, their tests, and
`data/generated/*`. The datagen package survives as a
library (fields, labels, generator core, four physics simulators) serving the Physics Lab,
analytics, and the classical baseline. The 0.842 mask mAP50 stays the project's headline
model result — it just no longer functions as a comparison bar for generated-data models.
`scripts/wm811k/` and `colab/` were also removed by the user in the same sweep.

## 9. Roadmap after Stage 8

Stage 6 (deferred, still owed): stream simulator + Shewhart/EWMA/CUSUM, its `/api/monitor/*`
router, and then the dashboard's Line Monitor view (adding a new nav entry — the old
disabled placeholder was removed 2026-07-04).
Stage 9: polish/release. Then F1/F2.
