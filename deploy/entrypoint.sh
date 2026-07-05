#!/usr/bin/env bash
# Container boot: fetch the model weights and dataset (both are gitignored, so
# they cannot ship in the build context), then start the API + dashboard server.
set -euo pipefail

if [ ! -f models/best.pt ]; then
	: "${MODEL_URL:?MODEL_URL must point at the .pt weights (e.g. an HF resolve URL)}"
	mkdir -p models
	curl -fsSL "$MODEL_URL" -o models/best.pt
fi

if [ ! -d data/raw ]; then
	: "${DATA_URL:?DATA_URL must point at the data tarball (data/raw + data/splits)}"
	curl -fsSL "$DATA_URL" | tar -xz
fi

exec python -m scripts.api.main \
	--host 0.0.0.0 \
	--port "${PORT:-7860}" \
	--model-path models/best.pt
