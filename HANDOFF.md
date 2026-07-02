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
  device**), `--model-name yolo26m-seg.pt`, `--resume`, `--seed 42`.
- fixed training policy dict: `imgsz=640, patience=50, mosaic=0.0, degrees=180.0, flipud=0.5,
fliplr=0.5, scale=0.1, hsv_h/s/v=0.0, project="runs/train"`.
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

Tests (80): Stage 1 tests plus `test_fields.py`, `test_labels.py`, `test_generator.py`,
`test_review.py`, `test_layout.py`, `test_classical.py`, and `test_resnet_baseline.py`.
There are deliberately NO tests for CLI/argparse plumbing or for constant values.

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

## 8. Next work: Stage 2 gates (plan: `docs/superpowers/plans/2026-07-02-stage2-data-engine.md`)

Code tasks are complete. Remaining execution is gated:

1. Generate the pilot set:
   `uv run python -m scripts.datagen.generator --out-dir data/generated/pilot --count 1000 --seed 42`
2. Render review sheets:
   `uv run python -m scripts.datagen.review --generated-dir data/generated/pilot`
3. STOP for user approval of `data/generated/pilot/review/*.png` before generating 10k.
4. After approval, follow `colab/stage2_data_engine.md` for the 10k generation, YOLO scaling
   study at {500,1k,2k,5k,10k}, ResNet baseline training, and exit-gate comparison.

Exit gates: (A) user approves pilot sheets; (B) model trained on ~500 generated-only images ≥
Stage-1 baseline mask mAP50 on the raw test split; (C) scaling curve + 10k production model;
(D) baseline comparison table (detector vs. SVM vs. ResNet — the "why detection" evidence).

Stage 2 deps added: `pillow`, `scikit-learn`, `torchvision`, and `tqdm`.

## 9. Roadmap after Stage 2

Stage 3: physics modules (`datagen/physics/` — heat-equation thermal/slip, Emslie–Bonner–Peck
spin-coat, Preston CMP, shot-grid) as generation modes + future dashboard Physics Lab.
Stage 4: WM-811K (convert pkl → render die grids in our visual style → zero-shot → few-shot
with pseudo-labels; image-level metrics only). Stage 5: analytics engine (die grid, negative
binomial yield model, systematic-vs-random $-decomposition, knowledge base, diagnosis JSON).
Stage 6: stream simulator + Shewhart/EWMA/CUSUM. Stage 7: FastAPI. Stage 8: React/Vite/Tailwind
dashboard (six views; user's React conventions: TS, typed props interfaces, Tailwind-only with
dark: variants, Recharts, react-icons). Stage 9: polish/release. Then F1/F2.
