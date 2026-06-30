import matplotlib.pyplot as plt
from PIL import Image

image_path = "data/annotated/0164_swirl.jpg"
label_path = "data/annotated/0164_swirl.txt"

image = Image.open(image_path)
width, height = image.size

plt.imshow(image)
plt.axis(False)

with open(label_path, "r") as file:
    lines = [line.strip() for line in file if line.strip()]

# each line is one annotated object: "<class_id> x1 y1 x2 y2 ... xn yn" with x/y normalized to [0, 1]
for line in lines:
    values = line.split()
    coords = [float(v) for v in values[1:]]
    xs = [coords[i] * width for i in range(0, len(coords), 2)]
    ys = [coords[i] * height for i in range(1, len(coords), 2)]
    # give every vertex its own color via the colormap so the dots are visibly different
    colors = list(range(len(xs)))
    plt.scatter(xs, ys, c=colors, cmap="hsv", s=40, edgecolors="black", linewidths=0.5, zorder=2)

plt.show()
