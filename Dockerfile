# Single-container deployment for Hugging Face Spaces (Docker SDK, free CPU tier).
# Stage 1 builds the React dashboard; stage 2 serves it and the API from FastAPI.

FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# curl fetches weights/data at boot; libgl1 + libglib2.0-0 are opencv runtime deps
RUN apt-get update \
	&& apt-get install -y --no-install-recommends curl libgl1 libglib2.0-0 \
	&& rm -rf /var/lib/apt/lists/* \
	&& useradd -m -u 1000 user

USER user
ENV HOME=/home/user \
	UV_LINK_MODE=copy
WORKDIR /home/user/app

COPY --chown=user pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
ENV PATH="/home/user/app/.venv/bin:$PATH"

COPY --chown=user scripts/ scripts/
COPY --chown=user deploy/entrypoint.sh ./
COPY --chown=user --from=frontend /build/dist frontend/dist

EXPOSE 7860
CMD ["bash", "entrypoint.sh"]
