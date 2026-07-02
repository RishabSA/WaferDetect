from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage as ndi

if __name__ == "__main__":
    image_path = "data/images/images/0163_swirl.jpg"

    image = Image.open(image_path)
    width, height = image.size

    image_np = np.array(image)
    image_bw_np = image_np[:, :, 0] / image_np.max()

    black_threshold = 0.5
    black_mask = image_bw_np < black_threshold  # True where black

    # Per-pixel radius map so we can drop the wafer outline (also dark) before labeling
    center_x, center_y = width / 2.0, height / 2.0
    yy, xx = np.indices((height, width))
    radius_map = np.sqrt((xx - center_x) ** 2 + (yy - center_y) ** 2)

    # The outline sits at the largest dark radius
    wafer_radius = radius_map[black_mask].max()
    interior_mask = radius_map < 0.98 * wafer_radius

    # Mask out the outline so only interior defect dots remain
    dots_mask = black_mask & interior_mask

    # Label connected blobs so that each blob of touching dark pixels is one defect dot
    labels, num_blobs = ndi.label(dots_mask)

    # Drop single-pixel JPEG speckle, then take one centroid per remaining blob
    component_sizes = np.bincount(labels.ravel())
    min_dot_pixels = 2
    keep_ids = [
        i for i in range(1, num_blobs + 1) if component_sizes[i] >= min_dot_pixels
    ]

    centroids = np.array(ndi.center_of_mass(dots_mask, labels, keep_ids))
    dot_ys, dot_xs = centroids[:, 0], centroids[:, 1]

    print(f"Number of distinct, die dot defects: {dot_xs.size}")

    # Build a wafer bin map

    # Number of die cells per axis (1:10 ratio)
    grid_resolution = 64
    wafer_map = np.zeros((grid_resolution, grid_resolution), dtype=int)

    # Map each centroid's pixel coords to its grid cell (clip guards the wafer edge)
    grid_cols = np.clip(
        (dot_xs / width * grid_resolution).astype(int), 0, grid_resolution - 1
    )
    grid_rows = np.clip(
        (dot_ys / height * grid_resolution).astype(int), 0, grid_resolution - 1
    )
    wafer_map[grid_rows, grid_cols] = 1

    print(f"Wafer map shape: {wafer_map.shape}, defect cells: {int(wafer_map.sum())}")

    fig, (ax_dots, ax_map) = plt.subplots(1, 2, figsize=(12, 6))
    ax_dots.imshow(image_bw_np, cmap="gray")
    ax_dots.scatter(dot_xs, dot_ys, c="red", s=8)
    ax_dots.set_title("Extracted defect dots")
    ax_dots.axis(False)

    ax_map.imshow(wafer_map, cmap="gray_r", origin="upper")
    ax_map.set_title(f"Wafer bin map ({grid_resolution}x{grid_resolution})")
    ax_map.axis(False)

    plt.show()
