"""Figure of the five evaluation layouts: the saved top-camera photographs, one per layout, in a row.

Each panel is labelled with the layout name and the items in order of distance from the base axis, nearest
first (C carrot, O Oreo, R RITZ), computed from configs/eval_layouts.yaml.

    conda run -n rb5 python paper/figures/make_fig_layouts.py

Reads data/eval/layouts/L1.jpg .. L5.jpg; writes paper/figures/fig_layouts.pdf and .png.
"""
import math
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yaml

ROOT = Path(__file__).resolve().parents[2]
PHOTOS = ROOT / "data/eval/layouts"
CROP_BOTTOM = 30          # px; a strip of tape at the lower edge of the 640 x 480 photos
OUT = Path(__file__).resolve().parent / "fig_layouts"


def main():
    layouts = yaml.safe_load((ROOT / "configs/eval_layouts.yaml").read_text())["layouts"]
    fig, axes = plt.subplots(1, len(layouts), figsize=(7.16, 1.2), dpi=300)
    for ax, (name, items) in zip(axes, layouts.items()):
        img = cv2.imread(str(PHOTOS / f"{name}.jpg"))
        ax.imshow(cv2.cvtColor(img[:img.shape[0] - CROP_BOTTOM], cv2.COLOR_BGR2RGB))
        ax.set_axis_off()
        order = sorted(items, key=lambda k: math.hypot(*items[k]))
        ax.set_title(f"{name}: {', '.join(order)}", fontsize=7, pad=2)
        print(name, order)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=0.86, wspace=0.03)
    for ext in ("pdf", "png"):
        fig.savefig(f"{OUT}.{ext}", dpi=300)
    print(f"wrote {OUT}.pdf and .png")


if __name__ == "__main__":
    main()
