# Stage 4 WM-811K Runs On Colab (A100)

Prereqs: `LSWMD.pkl` uploaded to Drive; a trained model on Drive. Prefer the Stage 2
production model at `runs/train/stage2_scale_10000/weights/best.pt`.

1. Runtime -> A100. Clone repo; `!pip install -q uv && !uv sync`; copy `LSWMD.pkl` into
   `data/wm811k/` and model weights into `weights/`.
2. One-time data pipeline:

```bash
uv run python -m scripts.wm811k.convert
uv run python -m scripts.wm811k.manifests
uv run python -m scripts.wm811k.render --manifest data/wm811k/manifests/calibration.txt --out-dir data/wm811k/images/calibration
uv run python -m scripts.wm811k.render --manifest data/wm811k/manifests/eval.txt --out-dir data/wm811k/images/eval
```

3. Zero-shot headline:

```bash
uv run python -m scripts.wm811k.zero_shot --model-path weights/best.pt
```

4. Few-shot sweep:

```bash
for BUDGET in 10 50 100 500; do
  for SEED in 42 43 44; do
    uv run python -m scripts.wm811k.pseudolabel --budget ${BUDGET} --seed ${SEED}
    uv run python -m scripts.perception.train --data data/wm811k/fewshot_${BUDGET}_${SEED}/data.yaml \
      --name wm811k_ft_${BUDGET}_${SEED} --model-name weights/best.pt --epochs 60 --device 0 --seed ${SEED}
    uv run python -m scripts.wm811k.zero_shot --model-path runs/train/wm811k_ft_${BUDGET}_${SEED}/weights/best.pt \
      --out-dir runs/wm811k/ft_${BUDGET}_${SEED}
    uv run python -m scripts.perception.train --data data/wm811k/fewshot_${BUDGET}_${SEED}/data.yaml \
      --name wm811k_scratch_${BUDGET}_${SEED} --model-name yolo26m-seg.pt --epochs 60 --device 0 --seed ${SEED}
    uv run python -m scripts.wm811k.zero_shot --model-path runs/train/wm811k_scratch_${BUDGET}_${SEED}/weights/best.pt \
      --out-dir runs/wm811k/scratch_${BUDGET}_${SEED}
  done
done
```

5. Quantization ablation: compare zero-shot macro-F1 for Stage 2 10k generated models built
   with `--die-grid-frac 0.0` versus `0.5`.
6. Copy `runs/wm811k/` to Drive.
