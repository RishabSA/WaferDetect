from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

image_path = "data/images/images/0163_swirl.jpg"

image = Image.open(image_path)
width, height = image.size

image_np = np.array(image)
image_bw_np = image_np[:, :, 0] / image_np.max()

black_threshold = 0.5
black_mask = image_bw_np < black_threshold

ys, xs = np.nonzero(black_mask)

# Drop the wafer outline and only keep interior defect dots
center_x, center_y = width / 2.0, height / 2.0
radii = np.sqrt((xs - center_x) ** 2 + (ys - center_y) ** 2)
wafer_radius = radii.max()
interior = radii < 0.98 * wafer_radius
xs, ys = xs[interior], ys[interior]

print(f"Number of dot pixels: {xs.size}")

plt.imshow(image_bw_np, cmap="gray")
plt.scatter(xs, ys, c="red", s=4)
plt.axis(False)
plt.show()
