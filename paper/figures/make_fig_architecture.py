"""Fig. 2: system architecture, recording (teleoperation) on top and learning / autonomous execution below.

Drawn on a 100 x 50 grid (one unit = 1/14 in at the two-column width). Hardware images in this folder:
photo_leader.png (RB-Y1 leader arm; since 2026-11-03 an image made with ChatGPT gpt-image from our photo, C2PA
digitalSourceType trainedAlgorithmicMedia; our photo is in git history) and photo_rb5.png (RB5-850 with the
gripper; also made with ChatGPT gpt-image, C2PA trainedAlgorithmicMedia, 2026-10-31); a missing image is drawn as
a gray placeholder.

    conda run -n rb5 python paper/figures/make_fig_architecture.py

Writes paper/figures/fig_architecture.pdf and .png.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).resolve().parent
OUT = HERE / "fig_architecture"
W, H = 100, 50
TITLE, DETAIL = 7.0, 5.6            # font sizes [pt]
BLUE_TXT = "#1f3d7a"                # detail text
GRAY, ORANGE, YELLOW = "#f1f1f1", "#fbe3cc", "#fdf3d0"
ORANGE_LN, BLUE_LN = "#c0661f", "#1f3d7a"


def box(ax, x, y, w, h, title=None, detail=None, fc=GRAY, ls="-", lw=0.8, ec="black", r=0.8, title_dy=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec, ls=ls, lw=lw))
    if title and detail:
        ty = y + h - (title_dy if title_dy is not None else 1.6)
        ax.text(x + w / 2, ty, title, ha="center", va="center", fontsize=TITLE)
        ax.text(x + w / 2, (y + ty - 1.0) / 2, detail, ha="center", va="center", fontsize=DETAIL,
                color=BLUE_TXT, linespacing=1.15)
    elif title:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=TITLE, linespacing=1.15)


def arrow(ax, pts, color="black", ls="-", both=False):
    """A polyline through pts with an arrowhead at the end (and at the start if both)."""
    for a, b in zip(pts[:-2], pts[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, ls=ls, lw=0.8, solid_capstyle="butt")
    ax.annotate("", xy=pts[-1], xytext=pts[-2],
                arrowprops=dict(arrowstyle="<|-|>" if both else "-|>", color=color, lw=0.8, ls=ls,
                                shrinkA=0, shrinkB=0, mutation_scale=6))


def label(ax, x, y, s, ha="center", va="center", italic=False, color="black", size=DETAIL):
    ax.text(x, y, s, ha=ha, va=va, fontsize=size, style="italic" if italic else "normal", color=color,
            linespacing=1.15)


def photo(ax, name, x0, y0, x1, y1):
    """The photo fitted inside the rectangle, centered, aspect kept."""
    p = HERE / name
    if not p.exists():
        ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#d9d9d9", ec="none"))
        label(ax, (x0 + x1) / 2, (y0 + y1) / 2, f"{name}\n(missing)", color="#555555")
        return
    img = plt.imread(p)
    if img.shape[2] == 3:                                  # no transparency: trim the white margins
        rows, cols = (img < 0.94).any(axis=2).nonzero()
    else:                                                  # transparent background: trim the clear margins
        rows, cols = (img[:, :, 3] > 0.05).nonzero()
    img = img[rows.min():rows.max() + 1, cols.min():cols.max() + 1]
    ih, iw = img.shape[:2]
    w, h = x1 - x0, y1 - y0
    if iw / ih > w / h:
        hh = w * ih / iw
        y0, y1 = y0 + (h - hh) / 2, y0 + (h + hh) / 2
    else:
        ww = h * iw / ih
        x0, x1 = x0 + (w - ww) / 2, x0 + (w + ww) / 2
    ax.imshow(img, extent=[x0, x1, y0, y1], interpolation="antialiased", zorder=2)


def main():
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Nimbus Roman", "Liberation Serif"],
                         "mathtext.fontset": "stix"})
    fig = plt.figure(figsize=(7.16, 7.16 * H / W))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.set_aspect("equal")
    ax.set_axis_off()

    # Recording: leader arm -> PC -> control box -> RB5
    box(ax, 0.3, 27, 12, 22.5, fc="white")   # white behind the leader image
    label(ax, 6.3, 47.2, "Leader arm\n(RB-Y1)", size=TITLE)
    photo(ax, "photo_leader.png", 1.5, 32.0, 11.1, 45.3)
    label(ax, 6.3, 29.8, "Dynamixel,\nU2D2, 2 Mbps")
    arrow(ax, [(12.3, 38.5), (21, 38.5)])
    label(ax, 16.65, 41.3, "joint angles,\nclutch, trigger", italic=True)
    label(ax, 16.65, 36.8, "(USB)")

    box(ax, 21, 27, 29, 22.5)
    label(ax, 35.5, 47.6, "PC — teleoperation (Python 3.10)", size=TITLE)
    box(ax, 22.3, 39.3, 26.4, 6.8, "a) Teleop loop (50 Hz)", "FK → cylindrical mapping\n→ command shaping",
        ls="--", lw=0.6, r=0.6)
    box(ax, 22.3, 33.6, 26.4, 5.0, "b) Gripper thread", "MX-106, U2D2", ls="--", lw=0.6, r=0.6)
    box(ax, 22.3, 27.9, 26.4, 5.0, "c) Camera process", "JPEG, 30 fps, one clock", ls="--", lw=0.6, r=0.6)

    box(ax, 61, 35.5, 12.5, 9, "RB5 control box", "rbpodo;\nIK + motor control", title_dy=2.0)
    arrow(ax, [(50, 42.5), (61, 42.5)])
    label(ax, 55.5, 46.2, "move_servo_l\n(x, y, z, rx, ry, rz),\nport 5000", italic=True)
    arrow(ax, [(61, 37.5), (50, 37.5)])
    label(ax, 55.5, 35.0, "robot state,\nport 5001", italic=True)

    photo(ax, "photo_rb5.png", 75.5, 29.5, 99.7, 49.5)
    arrow(ax, [(73.5, 40), (79, 40)], both=True)
    label(ax, 87.6, 27.8, "RB5-850 with gripper", size=TITLE)

    box(ax, 41.5, 16.5, 18.5, 7.5, "Cameras", "front D435, top C270 (fixed);\ngrip Brio 101 (on gripper)",
        title_dy=1.5)
    arrow(ax, [(47, 24), (47, 27)])
    label(ax, 47.6, 25.5, "images", ha="left", italic=True)

    # Dataset flow
    box(ax, 22.5, 17, 16.5, 7, "Session logs (raw)", "states 50 Hz, targets,\nJPEG 30 fps, one clock",
        fc=ORANGE, ec=ORANGE_LN, title_dy=1.5)
    arrow(ax, [(30.75, 27), (30.75, 24)], color=ORANGE_LN, ls="--")

    # Learning and autonomous execution
    box(ax, 0.3, 0.3, 75.7, 15, fc=YELLOW, r=1.0)
    ax.text(20, 13.9, r"$\bf{LeRobot\ 0.6.1}$ (Python 3.12)", ha="left", va="center", fontsize=TITLE)
    arrow(ax, [(22.5, 20.5), (7.5, 20.5), (7.5, 10.8)], color=ORANGE_LN, ls="--")
    box(ax, 1.5, 1.5, 12, 9.3, "Converter", "30 Hz grid,\nnearest frames,\nfiltering", title_dy=1.8)
    arrow(ax, [(13.5, 6.2), (16, 6.2)])
    box(ax, 16, 1.5, 16.5, 9.3, "LeRobot dataset",
        "state: 6 joints + gripper\naction: x, y, z, gripper\n3 cameras 320×240", fc=ORANGE, ec=ORANGE_LN,
        title_dy=1.8)
    arrow(ax, [(32.5, 6.2), (35, 6.2)])
    box(ax, 35, 1.5, 12.5, 9.3, "ACT training", "chunk 100, ResNet-18\nGPU: RTX A1000", title_dy=1.8)
    arrow(ax, [(47.5, 6.2), (51, 6.2)])
    label(ax, 49.25, 8.6, "trained\npolicy", italic=True)
    box(ax, 51, 1.0, 24, 12.3)
    label(ax, 63, 12.1, "Policy runner", size=TITLE)
    box(ax, 52.0, 6.4, 22, 4.6, "Policy process", "ACT inference, time-stamped chunks", r=0.5, title_dy=1.3)
    box(ax, 52.0, 1.6, 22, 4.6, "Servo process (50 Hz)", "temporal ensembling 30→50 Hz,\nsame command shaping",
        r=0.5, title_dy=1.2)

    # Execution links (blue dashed)
    arrow(ax, [(56, 16.5), (56, 13.3)], color=BLUE_LN, ls="--")
    label(ax, 55.4, 15.95, "images", ha="right", italic=True, color=BLUE_LN)
    arrow(ax, [(64.5, 35.5), (64.5, 13.3)], color=BLUE_LN, ls="--")
    label(ax, 64.0, 27.5, "robot\nstate", ha="right", italic=True, color=BLUE_LN)
    arrow(ax, [(70, 13.3), (70, 35.5)], color=BLUE_LN, ls="--")
    label(ax, 70.6, 22.0, "move_servo_l", ha="left", italic=True, color=BLUE_LN)

    # Legend
    box(ax, 78.5, 1.0, 21, 11.5, fc="white", lw=0.6)
    for i, (c, ls, s) in enumerate([("black", "-", "data / command flow"), (ORANGE_LN, "--", "dataset flow"),
                                    (BLUE_LN, "--", "autonomous execution")]):
        y = 9.6 - 3.3 * i
        arrow(ax, [(80, y), (85, y)], color=c, ls=ls)
        label(ax, 86, y, s, ha="left")

    for ext in ("pdf", "png"):
        fig.savefig(f"{OUT}.{ext}", dpi=300)
    print(f"wrote {OUT}.pdf and .png")


if __name__ == "__main__":
    main()
