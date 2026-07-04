import numpy as np
from PIL import Image, ImageDraw

image_size = 640
grid_size = 256
wafer_frac = 0.97


def sample_dots(field: np.ndarray, count: int, rng: np.random.Generator) -> np.ndarray:
    grid = field.shape[0]
    flat = field.ravel()

    # Draw cells with probability proportional to intensity (bright field regions get many dots while dim ones get few)
    cells = rng.choice(flat.size, size=count, p=flat / flat.sum())

    rows, cols = np.divmod(cells, grid)
    jitter = rng.uniform(-0.5, 0.5, size=(count, 2))
    u = (cols + jitter[:, 0]) / (grid - 1) * 2 - 1
    v = (rows + jitter[:, 1]) / (grid - 1) * 2 - 1
    dots = np.stack([u, v], axis=1)

    radius = np.hypot(dots[:, 0], dots[:, 1])
    outside = radius > 0.99
    dots[outside] = dots[outside] / radius[outside, None] * 0.99

    return dots


def quantize_dots(dots: np.ndarray, die_grid: int) -> np.ndarray:
    cell = 2.0 / die_grid
    snapped = (np.floor((dots + 1) / cell) + 0.5) * cell - 1
    return np.unique(snapped.round(6), axis=0)


def render(dots: np.ndarray, rng: np.random.Generator) -> Image.Image:
    # Make the image canvas
    image = Image.new("L", (image_size, image_size), 255)
    draw = ImageDraw.Draw(image)

    # Drawthe wafer outline circle
    margin = image_size * (1 - wafer_frac) / 2
    draw.ellipse(
        [margin, margin, image_size - margin, image_size - margin], outline=0, width=2
    )

    # Draw Each dot, which is a filled circle of jittered radius 1.2 – 2.4
    for u, v in dots:
        x = (0.5 + u * wafer_frac / 2) * image_size
        y = (0.5 + v * wafer_frac / 2) * image_size
        radius = rng.uniform(1.2, 2.4)
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=0)

    return image
