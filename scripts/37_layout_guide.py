"""t3-g: place the evaluation layouts with the top camera. Camera only, no robot.

Opens the `top` camera with the recording's fixed settings (configs/real.yaml) and shows it live in a browser,
http://localhost:PORT, with the targets of the chosen layout (configs/eval_layouts.yaml) drawn on it: a circle
per item (C carrot orange, O Oreo blue, R RITZ red) around its grasp point. A layout that already has a saved
photo (data/eval/layouts/L<n>.jpg) is blended in at half strength, to put the items back on it.

Keys in this terminal (no Enter): 1-5 = layout, s = save the current image (without drawings) as the layout's
photo, q = quit. Keep the robot at the ready pose (its gripper is in the top view at the start of a trial).
The camera cannot be open here and in a policy run at the same time. During the evaluation the policy run shows
the same view itself (python -m rb5_lerobot.run ... --trial N).

    python scripts/37_layout_guide.py              # env rb5 (or lerobot)
    python scripts/37_layout_guide.py --port 8081
    python scripts/37_layout_guide.py --sheet      # only writes data/eval/eval_sheet.csv (the trial order)
"""
import argparse
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from rb5_lerobot.layouts import PHOTOS, SHEET, draw, load_layouts, load_photo, photo_path, serve, write_sheet  # noqa: E402
from teleop.cameras import camera_defs, open_camera  # noqa: E402
from teleop.episodes import KeyReader  # noqa: E402
from teleop.settings import SettingsError, load_settings  # noqa: E402


def parse(data):
    return [c for c in data.decode("latin-1") if c in "12345sSqQ"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--sheet", action="store_true", help="only write data/eval/eval_sheet.csv (the trial order)")
    args = ap.parse_args()
    if args.sheet:
        try:
            n = write_sheet()
        except FileExistsError as e:
            raise SystemExit(str(e))
        return print(f"saved {SHEET.relative_to(ROOT)} ({n} trials)")
    layouts, _, M = load_layouts()
    names = list(layouts)
    try:
        s, _ = load_settings(ROOT / "configs" / "real.yaml", real=True)
    except SettingsError as e:
        raise SystemExit(f"settings: {e}")
    (name, device, settings, fmt), = camera_defs(s.record, ["top"])
    cam = open_camera(device, 640, 480, 30, settings, False, fmt)
    PHOTOS.mkdir(parents=True, exist_ok=True)
    state = {"name": names[0], "photo": load_photo(names[0]), "img": None}

    def frame():
        if state["img"] is None:
            return None
        title = state["name"] + ("  (saved photo blended)" if state["photo"] is not None else "  (no photo yet)")
        return draw(state["img"], layouts[state["name"]], M, title, state["photo"])

    url, problem = serve(frame, args.port, "Layout guide: keys in the terminal 1-5 layout, s save photo, q quit")
    if problem:
        cam.close()
        raise SystemExit(problem)
    keys = KeyReader(parse=parse)
    if not keys.start():
        cam.close()
        raise SystemExit("needs a terminal for the keys")
    show = lambda n: print(f"{n}: " + ", ".join(f"{a} {b}" for a, b in layouts[n].items())  # noqa: E731
                           + ("  (photo blended)" if state["photo"] is not None else ""))
    print(f"top camera {device}; open {url}  (1-5 layout, s save photo, q quit)")
    show(state["name"])
    try:
        while True:
            got = cam.read()
            if got is None:
                continue
            state["img"] = got[0]
            for k in keys.keys():
                if k in "12345" and int(k) <= len(names):
                    state["name"] = names[int(k) - 1]
                    state["photo"] = load_photo(state["name"])
                    show(state["name"])
                elif k in "sS":
                    p = photo_path(state["name"])
                    Image.fromarray(got[0]).save(p, quality=95)
                    state["photo"] = load_photo(state["name"])
                    print(f"saved {p.relative_to(ROOT)}")
                elif k in "qQ":
                    return
    finally:
        keys.stop()
        cam.close()


if __name__ == "__main__":
    main()
