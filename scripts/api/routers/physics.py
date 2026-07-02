from typing import Literal
import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel

from scripts.analytics.fieldanalysis import field_verdict, shot_matrices
from scripts.api.plots import field_png, image_png
from scripts.datagen.fields import disk_coordinates
from scripts.datagen.generator import grid_size, quantize_dots, render, sample_dots
from scripts.datagen.physics.cmp import cmp_field
from scripts.datagen.physics.shotgrid import intra_field_mask
from scripts.datagen.physics.spincoat import spincoat_field
from scripts.datagen.physics.thermal import (
    slip_lines_field,
    slip_probability,
    solve_heat,
    solver_grid,
    thermal_stress,
)

router = APIRouter()

pattern_dot_count = 220
analysis_die_grid = 48
shot_cell = 0.25


class ThermalRequest(BaseModel):
    steps: int = 250
    ramp_per_step: float = 2.0
    edge_loss: float = 0.08
    pin_strength: float = 0.05
    spot_x: float | None = None
    spot_y: float | None = None
    spot_strength: float = 0.0
    seed: int = 42


class FilmRequest(BaseModel):
    mode: Literal["center", "annular", "tilt", "edge_bead"] = "center"
    seed: int = 42


class CmpRequest(BaseModel):
    mode: Literal["center", "edge_ring", "donut"] = "edge_ring"
    seed: int = 42


class ShotGridRequest(BaseModel):
    mode: Literal["intra", "inter"] = "intra"
    seed: int = 42


def field_sample(field: np.ndarray, rng: np.random.Generator) -> str:
    return image_png(render(sample_dots(field, pattern_dot_count, rng), rng))


def shot_fail_grid(dots: np.ndarray) -> np.ndarray:
    snapped = quantize_dots(dots, analysis_die_grid)
    fail_grid = np.zeros((analysis_die_grid, analysis_die_grid), dtype=bool)
    cells = np.clip(
        np.floor((snapped + 1) / (2.0 / analysis_die_grid)).astype(int),
        0,
        analysis_die_grid - 1,
    )
    fail_grid[cells[:, 1], cells[:, 0]] = True
    return fail_grid


@router.post("/api/physics/thermal")
def thermal(request: ThermalRequest) -> dict:
    rng = np.random.default_rng(request.seed)
    phase = rng.uniform(0, 2 * np.pi)
    angles = phase + np.arange(3) * 2 * np.pi / 3
    pins = np.stack([0.55 * np.cos(angles), 0.55 * np.sin(angles)], axis=1)
    spot = None
    if request.spot_x is not None and request.spot_y is not None:
        spot = (request.spot_x, request.spot_y)

    temperature = solve_heat(
        solver_grid,
        request.steps,
        request.ramp_per_step,
        request.edge_loss,
        pins,
        request.pin_strength,
        spot_center=spot,
        spot_strength=request.spot_strength,
    )
    _, _, _, disk = disk_coordinates(solver_grid)
    stress = thermal_stress(temperature, disk)
    probability = slip_probability(temperature, disk)

    sample_rng = np.random.default_rng(request.seed)
    slip_field = slip_lines_field(grid_size, sample_rng)

    return {
        "temperature": field_png(temperature, cmap="inferno"),
        "stress": field_png(stress, cmap="coolwarm"),
        "slip_probability": field_png(probability),
        "sample": field_sample(slip_field, sample_rng),
        "stats": {
            "min_temperature": float(temperature.min()),
            "max_temperature": float(temperature.max()),
        },
    }


@router.post("/api/physics/spincoat")
def spincoat(request: FilmRequest) -> dict:
    rng = np.random.default_rng(request.seed)
    field = spincoat_field(grid_size, rng, mode=request.mode)
    return {"probability": field_png(field), "sample": field_sample(field, rng)}


@router.post("/api/physics/cmp")
def cmp(request: CmpRequest) -> dict:
    rng = np.random.default_rng(request.seed)
    field = cmp_field(grid_size, rng, mode=request.mode)
    return {"probability": field_png(field), "sample": field_sample(field, rng)}


@router.post("/api/physics/shotgrid")
def shotgrid(request: ShotGridRequest) -> dict:
    rng = np.random.default_rng(request.seed)
    offset = rng.uniform(0, shot_cell, size=2)
    xx, yy, _, disk = disk_coordinates(grid_size)

    if request.mode == "intra":
        spot = rng.uniform(0.2, 0.8, size=2)
        hot = intra_field_mask(
            grid_size, shot_cell, offset, spot, rng.uniform(0.1, 0.2)
        )
    else:
        cols = np.floor((xx + 1 - offset[0]) / shot_cell).astype(int)
        rows = np.floor((yy + 1 - offset[1]) / shot_cell).astype(int)
        chosen = (
            rng.random((rows.max() - rows.min() + 1, cols.max() - cols.min() + 1))
            < 0.25
        )
        hot = chosen[rows - rows.min(), cols - cols.min()] & disk

    field = np.where(hot, 1.0, 0.0)
    dots = sample_dots(field, pattern_dot_count, rng)
    field_rows = round(shot_cell * analysis_die_grid / 2)
    per_shot, intra = shot_matrices(shot_fail_grid(dots), field_rows, field_rows)

    return {
        "field": field_png(field),
        "sample": image_png(render(dots, rng)),
        "verdict": field_verdict(per_shot, intra),
    }
