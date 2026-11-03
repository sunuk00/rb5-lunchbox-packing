"""Fig. 1: the experimental setup (large, left) and the three camera views at one moment (stacked, right).

Camera views: the 640 x 480 JPEGs of a three-item demonstration (session real_20261029_123638, episode_001),
the frames captured nearest to 1.5 s after the first gripper close (the carrot just grasped), so that the grip
camera shows the carrot between the fingers. The setup photo is paper/figures/photo_setup.jpg (or .png),
cropped to fill its panel; while it is missing, a gray placeholder is drawn.

    conda run -n rb5 python paper/figures/make_fig1.py [--episode episode_001] [--after 1.5]

Writes paper/figures/fig1_setup.pdf and .png.
"""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SESSION = ROOT / "data/demos/real_20261029_123638"
OUT = HERE / "fig1_setup"
WIDTH, HEIGHT = 7.16, 2.6          # in: two-column width; the three views stacked set the height
GAP = 0.04                         # in, between panels
CAMS = (("front", "front"), ("top", "top"), ("grip", "grip"))


def camera_frames(episode, after_s):
    """The three camera frames nearest to after_s seconds after the episode's first gripper close."""
    e = json.loads((SESSION / "episodes.json").read_text())
    t0 = e["loop_t0"]
    a = next(x for x in e["attempts"] if x["dir"] == episode)
    with open(SESSION / "teleop.csv", newline="") as f:
        rows = [r for r in csv.DictReader(f)
                if r["grip_open_frac"] and a["t_start"] - t0 <= float(r["t_s"]) <= a["t_end"] - t0]
    opened = np.array([float(r["grip_open_frac"]) > 0.5 for r in rows])
    i = int(np.flatnonzero(opened[:-1] & ~opened[1:])[0]) + 1
    t = float(rows[i]["t_s"]) + t0 + after_s
    frames = {}
    for cam, _ in CAMS:
        with open(SESSION / episode / f"cam_{cam}.csv", newline="") as f:
            k = min(csv.DictReader(f), key=lambda r: abs(float(r["t_capture_s"]) - t))
        frames[cam] = np.asarray(Image.open(SESSION / episode / f"cam_{cam}" / f"{int(k['index']):06d}.jpg"))
    print(f"{episode}: first close {float(rows[i]['t_s']) + t0 - a['t_start']:.1f} s into the episode, "
          f"frames at +{after_s:.1f} s")
    return frames


def crop_to(img, aspect):
    """Center crop to width / height = aspect."""
    h, w = img.shape[:2]
    if w / h > aspect:
        nw = int(round(h * aspect))
        return img[:, (w - nw) // 2:(w - nw) // 2 + nw]
    nh = int(round(w / aspect))
    return img[(h - nh) // 2:(h - nh) // 2 + nh]


def tag(ax, text):
    ax.text(0.015, 0.03, text, transform=ax.transAxes, ha="left", va="bottom", fontsize=7,
            bbox=dict(fc="white", ec="none", pad=1.2))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--episode", default="episode_001")
    ap.add_argument("--after", type=float, default=1.5)
    a = ap.parse_args()
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Nimbus Roman", "Liberation Serif"]})
    frames = camera_frames(a.episode, a.after)

    view_h = (HEIGHT - 2 * GAP) / 3
    view_w = view_h * 4 / 3
    setup_w = WIDTH - view_w - GAP
    fig = plt.figure(figsize=(WIDTH, HEIGHT))
    ax = fig.add_axes([0, 0, setup_w / WIDTH, 1])
    photo = next((HERE / f"photo_setup.{ext}" for ext in ("jpg", "png") if (HERE / f"photo_setup.{ext}").exists()), None)
    if photo is None:
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, fc="#d9d9d9", ec="none"))
        ax.text(0.5, 0.5, "setup photograph (photo_setup.jpg)", transform=ax.transAxes, ha="center",
                va="center", fontsize=8, color="#555555")
    else:
        ax.imshow(crop_to(np.asarray(Image.open(photo).convert("RGB")), setup_w / HEIGHT))
    ax.set_axis_off()
    tag(ax, "(a) setup")

    for k, (cam, name) in enumerate(CAMS):
        y = HEIGHT - (k + 1) * view_h - k * GAP
        ax = fig.add_axes([(setup_w + GAP) / WIDTH, y / HEIGHT, view_w / WIDTH, view_h / HEIGHT])
        ax.imshow(frames[cam])
        ax.set_axis_off()
        tag(ax, f"({'bcd'[k]}) {name}")
    for ext in ("pdf", "png"):
        fig.savefig(f"{OUT}.{ext}", dpi=300)
    print(f"wrote {OUT}.pdf and .png ({WIDTH} x {HEIGHT} in; setup panel {setup_w:.2f} x {HEIGHT} in, "
          f"views {view_w:.2f} x {view_h:.2f} in)")


if __name__ == "__main__":
    main()
