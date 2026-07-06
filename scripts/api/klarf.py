from datetime import datetime
import numpy as np
from matplotlib.path import Path as PolygonPath

from scripts.analytics.diegrid import die_centers, failed_dies
from scripts.datagen.generator import image_size, wafer_frac

# GEnerator renders failing-die dots at 1.2-2.4 px radius on the wafer map, so exported point defects get this nominal footprint scaled to physical units
nominal_dot_px = 3.6


def defect_size_um(wafer_radius_mm: float) -> float:
    return nominal_dot_px / image_size * (2 * wafer_radius_mm * 1000 / wafer_frac)


def cluster_assignments(dots: np.ndarray, detections: list) -> np.ndarray:
    clusters = np.zeros(len(dots), dtype=int)
    if len(dots) == 0:
        return clusters

    # polygons are in image-normalized coordinates (y down), so map dots there
    points = (dots * wafer_frac + 1) / 2  # shape: (n, 2)
    for index, (_, _, polygon) in enumerate(detections):
        inside = PolygonPath(polygon).contains_points(points)
        clusters[(clusters == 0) & inside] = index + 1

    return clusters


def klarf_text(
    dots: np.ndarray,
    detections: list,
    names: list[str],
    wafer_id: str,
    die_mm: float,
    wafer_radius_mm: float,
) -> str:
    timestamp = datetime.now().strftime("%m-%d-%y %H:%M:%S")
    pitch_um = die_mm * 1000

    # Mirror the diegrid convention: count cells spanning the wafer, origin at
    # the lower-left corner of die (0, 0)
    die = die_mm / wafer_radius_mm
    count = int(np.floor(2.0 / die))
    span = count * die
    origin_mm = -span / 2 * wafer_radius_mm

    # KLARF coordinates are Cartesian (y up); dot v comes from image rows (y down)
    x_mm = dots[:, 0] * wafer_radius_mm if len(dots) else np.zeros(0)
    y_mm = -dots[:, 1] * wafer_radius_mm if len(dots) else np.zeros(0)

    x_index = np.floor((x_mm - origin_mm) / die_mm).astype(int)
    y_index = np.floor((y_mm - origin_mm) / die_mm).astype(int)
    x_rel = (x_mm - origin_mm - x_index * die_mm) * 1000
    y_rel = (y_mm - origin_mm - y_index * die_mm) * 1000

    clusters = cluster_assignments(dots, detections)
    class_numbers = np.zeros(len(dots), dtype=int)
    for index, (name, _, _) in enumerate(detections):
        class_numbers[clusters == index + 1] = names.index(name) + 1

    size = defect_size_um(wafer_radius_mm)
    area = np.pi * (size / 2) ** 2

    centers = die_centers(die_mm, wafer_radius_mm)
    center_indices = np.round((centers + span / 2) / die - 0.5).astype(int)
    order = np.lexsort((center_indices[:, 0], center_indices[:, 1]))
    center_indices = center_indices[order]
    failed = failed_dies(dots, die_mm, wafer_radius_mm)
    density_per_cm2 = len(dots) / (np.pi * (wafer_radius_mm / 10) ** 2)

    lines = [
        "FileVersion 1 2;",
        f"FileTimestamp {timestamp};",
        'InspectionStationID "WaferDetect" "YOLO26-seg" "1.0";',
        "SampleType WAFER;",
        f"ResultTimestamp {timestamp};",
        'LotID "WaferDetect";',
        f"SampleSize 1 {round(2 * wafer_radius_mm)};",
        f'SetupID "WaferDetect" {timestamp};',
        "SampleOrientationMarkType NOTCH;",
        "OrientationMarkLocation DOWN;",
        f"DiePitch {pitch_um:.1f} {pitch_um:.1f};",
        "DieOrigin 0.0 0.0;",
        f'WaferID "{wafer_id}";',
        "Slot 1;",
        f"SampleCenterLocation {-origin_mm * 1000:.1f} {-origin_mm * 1000:.1f};",
    ]

    lookup = [f"ClassLookup {len(names) + 1}", ' 0 "Unclassified"']
    lookup += [f' {number} "{name}"' for number, name in enumerate(names, start=1)]
    lines.append("\n".join(lookup) + ";")

    lines.append("InspectionTest 1;")
    plan = [f"SampleTestPlan {len(center_indices)}"]
    plan += [f" {x} {y}" for x, y in center_indices]
    lines.append("\n".join(plan) + ";")

    lines.append(
        "DefectRecordSpec 11 DEFECTID XREL YREL XINDEX YINDEX XSIZE YSIZE "
        "DEFECTAREA DSIZE CLASSNUMBER CLUSTERNUMBER;"
    )
    rows = ["DefectList"]

    for index in range(len(dots)):
        rows.append(
            f" {index + 1} {x_rel[index]:.1f} {y_rel[index]:.1f}"
            f" {x_index[index]} {y_index[index]}"
            f" {size:.1f} {size:.1f} {area:.1f} {size:.1f}"
            f" {class_numbers[index]} {clusters[index]}"
        )

    lines.append("\n".join(rows) + ";" if len(rows) > 1 else "DefectList;")

    lines.append("SummarySpec 5 TESTNO NDEFECT DEFDENSITY NDIE NDEFDIE;")
    lines.append(
        f"SummaryList\n 1 {len(dots)} {density_per_cm2:.4f}"
        f" {len(centers)} {int(failed.sum())};"
    )
    lines.append("EndOfFile;")

    return "\n".join(lines) + "\n"
