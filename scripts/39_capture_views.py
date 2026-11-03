"""Paper Fig. 1: save one frame of each recording camera (front, top, grip). Cameras only, no robot.

Opens the cameras of configs/real.yaml record.cameras with the recording's fixed settings (the same code as the
teleop and the policy runs), drops the first frames while the camera settles, and saves the latest frame of
each as a 640x480 PNG. The scene is assumed to be still, so the three frames are read one after another.
Nothing else may have the cameras open (teleop, policy run, scripts/37).

Usage (env rb5):
    python scripts/39_capture_views.py [--warmup 30]
Output: data/cameras/views_<time>/front.png, top.png, grip.png (use with paper/figures/make_fig1.py --views).
"""
import argparse
import sys
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from teleop.cameras import camera_defs, open_camera  # noqa: E402
from teleop.settings import SettingsError, load_settings  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--warmup", type=int, default=30, help="frames dropped before the saved one")
    args = ap.parse_args()
    try:
        s, _ = load_settings(ROOT / "configs" / "real.yaml", real=True)
    except SettingsError as e:
        raise SystemExit(f"settings: {e}")
    out = ROOT / "data" / "cameras" / time.strftime("views_%Y%m%d_%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    for name, device, settings, fmt in camera_defs(s.record, ["front", "top", "grip"]):
        cam = open_camera(device, 640, 480, 30, settings, False, fmt)
        try:
            got, n = None, 0
            while n <= args.warmup:
                r = cam.read()
                if r is not None:
                    got, n = r, n + 1
            Image.fromarray(got[0]).save(out / f"{name}.png")
            print(f"{name}: {device} -> {(out / f'{name}.png').relative_to(ROOT)}")
        finally:
            cam.close()
    print(f"saved {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
