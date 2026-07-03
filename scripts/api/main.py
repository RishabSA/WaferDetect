import argparse
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

default_model_path = Path("runs/train/stage1_baseline/weights/best.pt")
cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]


def create_app(model_path: Path | None) -> FastAPI:
    app = FastAPI(title="WaferDetect API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if model_path is not None:
        from ultralytics import YOLO

        app.state.model = YOLO(model_path)
    else:
        app.state.model = None

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "model_loaded": app.state.model is not None}

    from scripts.api.routers import (
        analyze,
        detect,
        diagnose,
        generate,
        physics,
        wafers,
        yields,
    )

    for router_module in (analyze, detect, diagnose, generate, physics, wafers, yields):
        app.include_router(router_module.router)

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model-path",
        type=str,
        default=str(default_model_path),
        help="Trained *.pt weights to serve (default: runs/train/stage1_baseline/weights/best.pt).",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Bind host (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Bind port (default: 8000).",
    )

    args = parser.parse_args()

    uvicorn.run(create_app(Path(args.model_path)), host=args.host, port=args.port)
