"""Fig. 3: front-camera frames of one autonomous packing trial (default: trial 18, layout L1).

Six panels: the start key, the carrot lifted, the carrot and the Oreo resting in their containers, the
RITZ lifted, and the end of the recording. A resting item is shown halfway between its release and the
next close, when the arm has left the container (at the release it hides it). Times come from the run log
on the run clock and are printed relative to the start key.

    conda run -n rb5 python paper/figures/make_fig3.py [--run data/policy/run_real_20261031_070212]

Writes paper/figures/fig3_sequence.pdf and .png.
"""
import argparse
import csv
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

LIFT_MM = 50.0            # an item counts as lifted once the target is this far above its close height
LIFT_SHOW_S = 0.5         # a lifted item is shown this long after that
FRONT = (0, 320)          # the front view is the left 320 px of the 960 x 240 run video
OUT = Path(__file__).resolve().parent / "fig3_sequence"


def read_log(path):
    """Start key time, close times, lift times and release times (run clock, s) from the run csv."""
    t_start, closes, opens, rows = None, [], [], []
    closed = False
    with open(path) as f:
        for r in csv.DictReader(f):
            if r["running"] != "1":
                continue
            t, z, c = float(r["t_s"]), float(r["target_z"]), float(r["grip_action"]) < 0.5
            rows.append((t, z))
            if t_start is None:
                t_start = t
            if c and not closed:
                closes.append((t, z))
            elif closed and not c:
                opens.append(t)
            closed = c
    lifts = [next(t for t, z in rows if t > tc and z > zc + LIFT_MM) for tc, zc in closes]
    return t_start, [t for t, _ in closes], lifts, opens


def frame_at(video_csv, t):
    """Index of the first video frame at or after run-clock time t."""
    with open(video_csv) as f:
        for r in csv.DictReader(f):
            if float(r["t_s"]) >= t:
                return int(r["frame"])
    raise ValueError(f"no frame at {t:.2f} s")


def last_frame(video_csv):
    with open(video_csv) as f:
        r = list(csv.DictReader(f))[-1]
    return int(r["frame"]), float(r["t_s"])


def grab(cap, n):
    cap.set(cv2.CAP_PROP_POS_FRAMES, n)
    ok, img = cap.read()
    if not ok:
        raise RuntimeError(f"cannot read frame {n}")
    img = img[:, FRONT[0]:FRONT[1]].copy()
    # Remove the white "front" label burned into the video: fill its pixels from the table around them.
    mask = np.zeros(img.shape[:2], np.uint8)
    mask[:20, :50] = cv2.inRange(img[:20, :50], (200, 200, 200), (255, 255, 255))
    img = cv2.inpaint(img, cv2.dilate(mask, np.ones((3, 3), np.uint8)), 3, cv2.INPAINT_TELEA)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", default="data/policy/run_real_20261031_070212")
    a = ap.parse_args()
    t_start, closes, lifts, opens = read_log(a.run + ".csv")
    if len(closes) != 3 or len(opens) != 3:
        raise SystemExit(f"expected 3 closes and 3 releases (a trial without misses), found {len(closes)}, {len(opens)}")
    video_csv = a.run + "_video.csv"
    n_end, t_end = last_frame(video_csv)
    panels = [(t_start, "start"), (lifts[0] + LIFT_SHOW_S, "carrot lifted"),
              ((opens[0] + closes[1]) / 2, "carrot in black box"), ((opens[1] + closes[2]) / 2, "Oreo in large hole"),
              (lifts[2] + LIFT_SHOW_S, "RITZ lifted"), (t_end, "all placed")]
    print(f"start key {t_start:.2f} s; releases " + ", ".join(f"{t - t_start:.1f}" for t in opens) + " s after it")

    cap = cv2.VideoCapture(a.run + ".mp4")
    fig, axes = plt.subplots(2, 3, figsize=(3.45, 1.9), dpi=300)
    for i, (ax, (t, name)) in enumerate(zip(axes.flat, panels)):
        n = n_end if t == t_end else frame_at(video_csv, t)
        ax.imshow(grab(cap, n))
        ax.set_axis_off()
        # Bottom left: the robot arm is there; the containers are at the top.
        ax.text(3, 237, f"({'abcdef'[i]}) {t - t_start:.1f} s\n{name}", fontsize=5, va="bottom", ha="left",
                linespacing=1.1, bbox=dict(facecolor="white", edgecolor="none", pad=1.0))
        print(f"({'abcdef'[i]}) {name}: frame {n}, {t - t_start:.1f} s")
    cap.release()
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0.02, hspace=0.03)
    for ext in ("pdf", "png"):
        fig.savefig(f"{OUT}.{ext}", dpi=300)
    print(f"wrote {OUT}.pdf and .png")


if __name__ == "__main__":
    main()
