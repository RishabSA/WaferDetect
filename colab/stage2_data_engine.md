# Stage 2 data-engine runs on Colab (A100)

Prereq: Stage 1 baseline numbers exist (`runs/eval/stage1_baseline/report.md`) and the
pilot review sheets were approved.

1. Runtime -> A100 GPU. Clone the repo; upload and unzip `waferdetect_raw.zip` into `data/`
   as in Stage 1; `!pip install -q uv && !uv sync`.
2. Rebuild the raw YOLO layout. The frozen test split lives here:
   `!uv run python -m scripts.perception.dataset --force`
3. Generate the production set. This is CPU-bound, around 30-60 min for 10k:
   `!uv run python -m scripts.datagen.generator --out-dir data/generated/v1 --count 10000 --seed 42`
4. Scaling study. Use nested subsets, one training per size:

```bash
for N in 500 1000 2000 5000 10000; do
  uv run python -m scripts.datagen.layout --generated-dir data/generated/v1 --out-dir data/generated/v1_yolo_${N} --limit ${N}
  uv run python -m scripts.perception.train --data data/generated/v1_yolo_${N}/data.yaml --name stage2_scale_${N} --device 0
  uv run python -m scripts.perception.evaluate --model-path runs/train/stage2_scale_${N}/weights/best.pt --data data/generated/v1_yolo_${N}/data.yaml --name stage2_scale_${N}
done
```

Evaluate scores on the raw test split because the generated layout's `data.yaml` points `test`
at `data/yolo/images/test`.

5. ResNet baseline: `!uv run python -m scripts.baselines.resnet --device cuda --epochs 20`
6. Copy `runs/` to Drive.
