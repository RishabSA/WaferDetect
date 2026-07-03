import base64
import io
import numpy as np
from matplotlib.figure import Figure
from PIL import Image


def field_png(field: np.ndarray, cmap: str = "viridis") -> str:
    figure = Figure(figsize=(4, 4))
    axis = figure.subplots()
    mappable = axis.imshow(field, cmap=cmap)
    figure.colorbar(mappable, ax=axis, fraction=0.046)
    axis.axis(False)

    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
    return base64.b64encode(buffer.getvalue()).decode()


def sinogram_png(sinogram: np.ndarray) -> str:
    figure = Figure(figsize=(6, 4))
    axis = figure.subplots()
    axis.imshow(sinogram, cmap="magma", aspect="auto")
    axis.axis(False)

    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=100, bbox_inches="tight", pad_inches=0)
    return base64.b64encode(buffer.getvalue()).decode()


def image_png(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()
