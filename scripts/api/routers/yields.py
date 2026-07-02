from fastapi import APIRouter

from scripts.analytics.diagnosis import kb_path, load_knowledge_base
from scripts.analytics.diegrid import radial_yield, wafer_summary, zone_yields
from scripts.analytics.economics import decompose, pareto
from scripts.analytics.yieldmodels import (
    estimate_alpha,
    estimate_defect_density,
    quadrat_counts,
)
from scripts.api.routers.diagnose import wafer_dots_and_detections
from scripts.perception.dataset import read_manifests

router = APIRouter()


@router.get("/api/yield/wafer/{stem}")
def yield_wafer(stem: str, die_mm: float = 6.0, die_value: float = 25.0) -> dict:
    dots, detections = wafer_dots_and_detections(stem)
    polygons = [polygon for _, _, polygon in detections]

    summary = wafer_summary(dots, die_mm)
    failed_fraction = 1 - summary["yield"]
    summary["d0_per_mm2"] = (
        estimate_defect_density(failed_fraction, die_mm**2)
        if failed_fraction < 1
        else None
    )

    summary["alpha"] = estimate_alpha(quadrat_counts(dots)) if len(dots) else None

    return {
        "summary": summary,
        "radial": radial_yield(dots, die_mm),
        "zones": zone_yields(dots, die_mm),
        "regions": decompose(dots, polygons, die_mm, die_value)["regions"],
    }


@router.get("/api/yield/pareto")
def yield_pareto(split: str = "test", limit: int = 0, die_value: float = 25.0) -> dict:
    kb = load_knowledge_base(kb_path)
    stems = sorted(read_manifests()[split])

    if limit:
        stems = stems[:limit]

    losses = []
    for stem in stems:
        dots, detections = wafer_dots_and_detections(stem)
        regions = decompose(
            dots, [polygon for _, _, polygon in detections], die_value=die_value
        )["regions"]

        for (name, _, _), region in zip(detections, regions, strict=True):
            losses.append((kb[name]["process_steps"][0], region["dollars"]))

    return {"wafers": len(stems), "pareto": pareto(losses)}
