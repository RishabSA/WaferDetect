import base64
import io
import textwrap
from datetime import datetime, timezone
import numpy as np
from PIL import Image
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon

page_size = (8.5, 11.0)
overlay_colors = ["#f87171", "#4ade80", "#60a5fa", "#fbbf24", "#c084fc", "#2dd4bf"]
ink = "#111827"
body = "#374151"
muted = "#6b7280"
rule = "#e5e7eb"
accent = "#0e7490"
loss_red = "#dc2626"
yield_green = "#059669"
kinematics_violet = "#7c3aed"
chart_cyan = "#0891b2"
line_height = 0.014


def decode_png(data: str) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(data)))


def new_page(section: str, subtitle: str) -> Figure:
    figure = Figure(figsize=page_size)
    figure.text(0.07, 0.955, "WaferDetect", fontsize=15, fontweight="bold", color=ink)
    figure.text(0.265, 0.955, section, fontsize=10, color=accent)
    figure.text(0.93, 0.957, subtitle, fontsize=7.5, color=muted, ha="right")
    figure.add_artist(
        Line2D(
            [0.07, 0.93],
            [0.94, 0.94],
            color=rule,
            linewidth=0.8,
            transform=figure.transFigure,
        )
    )
    return figure


def stat(
    figure: Figure,
    x: float,
    y: float,
    label: str,
    value: str,
    color: str,
    size: float = 20,
) -> None:
    figure.text(x, y, label.upper(), fontsize=6.5, color=muted, family="monospace")
    figure.text(
        x,
        y - 0.033,
        value,
        fontsize=size,
        color=color,
        fontweight="bold",
        family="monospace",
    )


def paragraph(
    figure: Figure,
    x: float,
    y: float,
    text: str,
    color: str,
    size: float = 8.5,
    width: int = 96,
) -> float:
    lines = textwrap.wrap(text, width)
    figure.text(
        x, y, "\n".join(lines), fontsize=size, color=color, va="top", linespacing=1.35
    )
    return y - len(lines) * line_height * 1.15


def clean_axis(axis) -> None:
    for spine in ("top", "right"):
        axis.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        axis.spines[spine].set_color(rule)
    axis.tick_params(colors=muted, labelsize=6.5, length=2)


def overview_page(
    analysis: dict,
    subtitle: str,
    die_mm: float,
    die_value: float,
    wafer_radius_mm: float,
) -> Figure:
    figure = new_page("Wafer analysis report", subtitle)
    summary = analysis["wafer_summary"]
    detections = analysis["detections"]

    axis = figure.add_axes((0.06, 0.44, 0.5, 0.46))
    image = decode_png(analysis["image"])
    axis.imshow(image)
    axis.axis(False)

    handles = []
    for index, detection in enumerate(detections):
        color = overlay_colors[index % len(overlay_colors)]
        points = np.array(detection["polygon"]) * (image.width, image.height)
        axis.add_patch(
            Polygon(
                points,
                closed=True,
                facecolor=to_rgba(color, 0.15),
                edgecolor=color,
                linewidth=1.4,
            )
        )
        handles.append(
            Line2D(
                [0],
                [0],
                color=color,
                linewidth=3,
                label=f"{detection['class']} ({detection['confidence']:.0%})",
            )
        )
    if handles:
        axis.legend(
            handles=handles,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.01),
            fontsize=7,
            frameon=False,
            ncol=2,
        )

    x = 0.62
    stat(
        figure,
        x,
        0.865,
        "Attributed loss",
        f"${summary['total_loss_dollars']:,.0f}",
        loss_red,
    )
    stat(figure, x, 0.775, "Wafer yield", f"{summary['yield']:.1%}", yield_green)
    stat(
        figure,
        x,
        0.685,
        "Failed dies",
        f"{summary['failed_dies']} / {summary['gross_dies']}",
        ink,
        size=15,
    )
    top = max(
        detections, key=lambda entry: entry["yield_loss"]["dollars"], default=None
    )
    stat(
        figure, x, 0.61, "Top defect", top["class"] if top else "none", accent, size=15
    )

    figure.text(x, 0.545, "PARAMETERS", fontsize=6.5, color=muted, family="monospace")
    parameters = (
        f"wafer radius   {wafer_radius_mm:.0f} mm ({wafer_radius_mm * 2:.0f} mm dia)\n"
        f"die size       {die_mm:.1f} mm\n"
        f"die value      ${die_value:,.2f}"
    )
    figure.text(
        x,
        0.535,
        parameters,
        fontsize=8,
        color=body,
        family="monospace",
        va="top",
        linespacing=1.6,
    )

    figure.text(
        0.07, 0.365, "MODEL DETECTIONS", fontsize=6.5, color=muted, family="monospace"
    )
    columns = (0.07, 0.34, 0.47, 0.62, 0.79)
    header = ("class", "confidence", "area", "excess failed", "loss")
    for column, title in zip(columns, header, strict=True):
        figure.text(column, 0.345, title, fontsize=7.5, color=muted, family="monospace")
    figure.add_artist(
        Line2D(
            [0.07, 0.93],
            [0.338, 0.338],
            color=rule,
            linewidth=0.6,
            transform=figure.transFigure,
        )
    )

    y = 0.322
    for index, detection in enumerate(detections[:10]):
        color = overlay_colors[index % len(overlay_colors)]
        loss = detection["yield_loss"]
        figure.text(
            0.07,
            y,
            f"● {detection['class']}",
            fontsize=8,
            color=color,
            family="monospace",
        )
        row = (
            f"{detection['confidence']:.1%}",
            f"{detection['geometry']['area_frac']:.1%}",
            f"{loss['excess_failed']:.0f} dies",
            f"${loss['dollars']:,.0f}",
        )
        for column, value in zip(columns[1:], row, strict=True):
            figure.text(column, y, value, fontsize=8, color=body, family="monospace")
        y -= 0.02
    if not detections:
        figure.text(
            0.07, y, "No defects detected on this wafer.", fontsize=8.5, color=body
        )

    if analysis["ground_truth"] is not None:
        figure.text(
            0.07,
            0.06,
            f"ground truth: {', '.join(analysis['ground_truth'])}",
            fontsize=7.5,
            color=muted,
            family="monospace",
        )

    return figure


def analytics_page(analysis: dict, subtitle: str) -> Figure:
    figure = new_page("Yield analytics", subtitle)
    summary = analysis["wafer_summary"]

    radial = analysis["radial"]
    radial_axis = figure.add_axes((0.09, 0.64, 0.84, 0.23))
    radial_axis.bar(range(len(radial)), radial, color=chart_cyan)
    radial_axis.set_xticks(
        range(len(radial)), [f"r{index}" for index in range(len(radial))]
    )
    radial_axis.set_title(
        "Radial fail rate (center → edge)", fontsize=9, color=ink, loc="left"
    )
    radial_axis.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    clean_axis(radial_axis)

    zones = analysis["zones"]
    zone_axis = figure.add_axes((0.09, 0.4, 0.38, 0.15))
    names = list(zones)
    zone_axis.barh(
        names, [zones[name] for name in names], color=yield_green, height=0.55
    )
    zone_axis.set_xlim(0, 1)
    zone_axis.invert_yaxis()
    zone_axis.set_title("Zone yields", fontsize=9, color=ink, loc="left")
    for position, name in enumerate(names):
        zone_axis.text(
            zones[name] + 0.02,
            position,
            f"{zones[name]:.1%}",
            fontsize=7,
            color=body,
            va="center",
        )
    clean_axis(zone_axis)

    x = 0.58
    figure.text(x, 0.55, "YIELD MODEL", fontsize=6.5, color=muted, family="monospace")
    d0 = summary["d0_per_mm2"]
    alpha = summary["alpha"]
    model_text = (
        f"random yield     {summary['yield_random']:.1%}\n"
        f"D0 / mm2         {f'{d0:.2e}' if d0 is not None else 'n/a'}\n"
        f"cluster alpha    {f'{alpha:.2f}' if alpha is not None else 'none'}"
    )
    figure.text(
        x,
        0.54,
        model_text,
        fontsize=8,
        color=body,
        family="monospace",
        va="top",
        linespacing=1.6,
    )

    sinogram_axis = figure.add_axes((0.09, 0.08, 0.5, 0.24))
    sinogram_axis.imshow(decode_png(analysis["sinogram"]), aspect="auto")
    sinogram_axis.axis(False)
    sinogram_axis.set_title(
        "Radon sinogram of defect dots", fontsize=9, color=ink, loc="left"
    )
    paragraph(
        figure,
        0.63,
        0.3,
        "Each column is one projection angle (0-180°); rotation-invariant structure "
        "such as scratches, spokes, and rings concentrates into bright features.",
        muted,
        size=7.5,
        width=42,
    )

    return figure


def diagnosis_page(analysis: dict, subtitle: str) -> Figure:
    figure = new_page("Diagnosis & recommended actions", subtitle)
    detections = analysis["detections"]

    y = 0.885
    if not detections:
        figure.text(
            0.07, y, "No defects detected on this wafer.", fontsize=9, color=body
        )

    for index, detection in enumerate(detections):
        if y < 0.14:
            figure.text(
                0.07,
                y,
                f"… and {len(detections) - index} more detections.",
                fontsize=8.5,
                color=muted,
            )
            break

        color = overlay_colors[index % len(overlay_colors)]
        diagnosis = detection["diagnosis"]
        figure.text(0.07, y, "●", fontsize=10, color=color)
        figure.text(
            0.09,
            y,
            f"{detection['class']}  —  ${detection['yield_loss']['dollars']:,.0f}",
            fontsize=10.5,
            color=ink,
            fontweight="bold",
        )
        y -= 0.024

        y = paragraph(figure, 0.09, y, diagnosis["mechanism"], body)
        y = paragraph(figure, 0.09, y, f"Action: {diagnosis['action']}", accent)
        context = (
            f"process steps: {', '.join(diagnosis['process_steps'])} · "
            f"tools: {', '.join(diagnosis['tool_families'])}"
        )
        y = paragraph(figure, 0.09, y, context, muted, size=7.5)

        kinematics = detection.get("kinematics")
        if kinematics:
            radius = kinematics["radius_of_curvature"]
            details = f"kinematics: {kinematics['verdict']} · orientation {kinematics['orientation_deg']:.0f}°"
            if radius is not None:
                details += f" · curvature radius {radius:.2f}"
            y = paragraph(figure, 0.09, y, details, kinematics_violet, size=7.5)

        y -= 0.02

    return figure


def report_pdf(
    analysis: dict, name: str, die_mm: float, die_value: float, wafer_radius_mm: float
) -> bytes:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    subtitle = f"{name} · {timestamp}"

    buffer = io.BytesIO()
    metadata = {"Title": f"WaferDetect report — {name}", "Creator": "WaferDetect"}
    with PdfPages(buffer, metadata=metadata) as pdf:
        pdf.savefig(
            overview_page(analysis, subtitle, die_mm, die_value, wafer_radius_mm)
        )
        pdf.savefig(analytics_page(analysis, subtitle))
        pdf.savefig(diagnosis_page(analysis, subtitle))

    return buffer.getvalue()
