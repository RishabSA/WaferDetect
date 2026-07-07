import hashlib
import io
import time
from collections import OrderedDict
from pathlib import Path
from PIL import Image
import numpy as np
from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile
from skimage.transform import radon
from ultralytics import YOLO

from scripts.analytics.diagnosis import diagnose, kb_path, load_knowledge_base
from scripts.analytics.diegrid import radial_yield, zone_yields
from scripts.api.klarf import is_klarf, klarf_text, parse_klarf, render_dots
from scripts.api.plots import image_png, sinogram_png
from scripts.api.report import report_pdf
from scripts.baselines.classical import dot_coordinates
from scripts.datagen.generator import wafer_frac
from scripts.perception.annotations import load_class_names, load_label_file

router = APIRouter()

classes_file = Path("data/raw/classes.txt")
raw_images_dir = Path("data/raw/images")
raw_labels_dir = Path("data/raw/labels")

sinogram_grid = 128
sinogram_angles = 180
max_display_dots = 4000

cache_size = 16
analysis_cache: OrderedDict = OrderedDict()

# Public-deployment guards: inference is CPU-bound, so cap what one client can queue
max_upload_bytes = 8 * 1024 * 1024
rate_limit_calls = 30
rate_window_seconds = 60.0
max_tracked_clients = 1024
request_log: dict = {}


def enforce_rate_limit(request: Request) -> None:
    forwarded = request.headers.get("x-forwarded-for")
    client = (
        forwarded.split(",")[0].strip()
        if forwarded
        else (request.client.host if request.client else "unknown")
    )

    now = time.monotonic()
    recent = [
        stamp
        for stamp in request_log.get(client, [])
        if now - stamp < rate_window_seconds
    ]
    if len(recent) >= rate_limit_calls:
        raise HTTPException(
            429,
            f"Rate limit exceeded: {rate_limit_calls} analyses "
            f"per {rate_window_seconds:.0f}s",
        )

    recent.append(now)
    request_log[client] = recent

    if len(request_log) > max_tracked_clients:
        stale = [
            key
            for key, stamps in request_log.items()
            if now - stamps[-1] >= rate_window_seconds
        ]
        for key in stale:
            del request_log[key]


def dot_sinogram(dots: np.ndarray) -> np.ndarray:
    grid = np.zeros((sinogram_grid, sinogram_grid))
    if len(dots):
        cols = np.clip(
            ((dots[:, 0] + 1) / 2 * (sinogram_grid - 1)).astype(int),
            0,
            sinogram_grid - 1,
        )
        rows = np.clip(
            ((dots[:, 1] + 1) / 2 * (sinogram_grid - 1)).astype(int),
            0,
            sinogram_grid - 1,
        )
        grid[rows, cols] = 1.0

    angles = np.linspace(0.0, 180.0, sinogram_angles, endpoint=False)
    return radon(grid, theta=angles)


def image_artifacts(
    image: Image.Image, model: YOLO, dots: np.ndarray | None = None
) -> dict:
    # Everything derived from the image alone — independent of the what-if
    # parameters. A KLARF ingest passes its exact dot set instead of
    # re-extracting pixel centers from the rendered image.
    if dots is None:
        dots = dot_coordinates(np.asarray(image.convert("L")))
    names = load_class_names(classes_file)

    result = model.predict(np.asarray(image), verbose=False)[0]
    detections = (
        []
        if result.masks is None
        else [
            (
                names[int(class_id)],
                float(confidence),
                [(float(x), float(y)) for x, y in segment],
            )
            for class_id, confidence, segment in zip(
                result.boxes.cls, result.boxes.conf, result.masks.xyn, strict=True
            )
        ]
    )

    return {
        "dots": dots,
        "detections": detections,
        "image": image_png(image),
        "sinogram": sinogram_png(dot_sinogram(dots)),
    }


async def resolve_artifacts(
    request: Request, stem: str, file: UploadFile | None
) -> dict:
    if bool(stem) == (file is not None):
        raise HTTPException(422, "Provide exactly one of stem or file")

    enforce_rate_limit(request)

    model = request.app.state.model
    if model is None:
        raise HTTPException(503, "The model is not loaded")

    # Resolve the cache key: stem for dataset wafers, content hash for uploads
    if stem:
        image_path = raw_images_dir / f"{stem}.jpg"

        if not image_path.is_file():
            raise HTTPException(404, f"Unknown wafer stem: {stem}")

        key = stem
    else:
        payload = await file.read()
        if len(payload) > max_upload_bytes:
            raise HTTPException(
                413,
                f"Upload too large: {len(payload)} bytes "
                f"(limit {max_upload_bytes})",
            )
        key = hashlib.sha256(payload).hexdigest()

    # A hit skips image loading, dot extraction, YOLO, and both PNG renders —
    # only the per-request analytics are recomputed
    if key in analysis_cache:
        analysis_cache.move_to_end(key)
        return analysis_cache[key]

    if not stem and is_klarf(payload):
        # KLARF ingest: rebuild the wafer map from the defect list, then run
        # the normal pipeline on the rendered image
        try:
            parsed = parse_klarf(payload.decode())
        except (ValueError, IndexError) as error:
            raise HTTPException(422, f"KLARF parse failed: {error}") from error

        image = render_dots(parsed["dots"]).convert("RGB")
        artifacts = image_artifacts(image, model, dots=parsed["dots"])
        artifacts["klarf"] = {
            "die_mm": parsed["die_mm"],
            "wafer_radius_mm": parsed["wafer_radius_mm"],
            "wafer_id": parsed["wafer_id"],
            "classes": parsed["classes"],
        }
    else:
        source = image_path if stem else io.BytesIO(payload)
        artifacts = image_artifacts(Image.open(source).convert("RGB"), model)

    analysis_cache[key] = artifacts
    if len(analysis_cache) > cache_size:
        analysis_cache.popitem(last=False)

    return artifacts


@router.post("/api/analyze")
async def analyze(
    request: Request,
    stem: str = "",
    die_mm: float = 6.0,
    die_value: float = 25.0,
    wafer_radius_mm: float = 150.0,
    file: UploadFile | None = File(default=None),
) -> dict:
    artifacts = await resolve_artifacts(request, stem, file)

    dots = artifacts["dots"]
    detections = artifacts["detections"]

    # Use extracted dots and detections to produce per-detection yield loss in dollars, an action form the knowledge-base, scratch kinematics, and a wafer summary
    report = diagnose(
        dots,
        detections,
        load_knowledge_base(kb_path),
        die_mm,
        die_value,
        wafer_radius_mm,
    )
    for entry, (_, _, polygon) in zip(report["detections"], detections, strict=True):
        entry["polygon"] = polygon

    # Subsample for SVG rendering; convert wafer coordinates to normalized image coordinates
    display = dots[:: max(1, len(dots) // max_display_dots)]
    display_image = (display * wafer_frac + 1) / 2  # shape: (n, 2)

    ground_truth = None
    if stem:
        names = load_class_names(classes_file)
        instances = load_label_file(raw_labels_dir / f"{stem}.txt")
        ground_truth = [names[instance.class_id] for instance in instances]
    elif artifacts.get("klarf") and artifacts["klarf"]["classes"]:
        # an ingested KLARF's own class labels play the role of ground truth
        ground_truth = artifacts["klarf"]["classes"]

    return {
        "stem": stem or None,
        "image": artifacts["image"],
        "dots": np.round(display_image, 4).tolist(),
        "sinogram": artifacts["sinogram"],
        "detections": report["detections"],
        "wafer_summary": report["wafer_summary"],
        "radial": radial_yield(dots, die_mm, wafer_radius_mm=wafer_radius_mm),
        "zones": zone_yields(dots, die_mm, wafer_radius_mm),
        "ground_truth": ground_truth,
        "klarf": artifacts.get("klarf"),
    }


@router.post("/api/report")
async def report(
    request: Request,
    stem: str = "",
    die_mm: float = 6.0,
    die_value: float = 25.0,
    wafer_radius_mm: float = 150.0,
    file: UploadFile | None = File(default=None),
) -> Response:
    # Same sources, params, cache, and rate limit as /api/analyze
    analysis = await analyze(request, stem, die_mm, die_value, wafer_radius_mm, file)

    name = stem or (file.filename if file and file.filename else "upload")
    pdf = report_pdf(analysis, name, die_mm, die_value, wafer_radius_mm)

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="waferdetect_{name}.pdf"'
        },
    )


@router.post("/api/klarf")
async def klarf(
    request: Request,
    stem: str = "",
    die_mm: float = 6.0,
    wafer_radius_mm: float = 150.0,
    file: UploadFile | None = File(default=None),
) -> Response:
    artifacts = await resolve_artifacts(request, stem, file)

    names = load_class_names(classes_file)
    name = stem or (file.filename if file and file.filename else "upload")
    text = klarf_text(
        artifacts["dots"], artifacts["detections"], names, name, die_mm, wafer_radius_mm
    )

    return Response(
        content=text,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="waferdetect_{name}.klarf"'
        },
    )
