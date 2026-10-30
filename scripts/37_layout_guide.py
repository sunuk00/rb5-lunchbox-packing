"""t3-g: place the evaluation layouts with the top camera. Camera only, no robot.

Opens the `top` camera with the recording's fixed settings (configs/real.yaml) and shows it live in a browser,
http://localhost:PORT, with the targets of the chosen layout (configs/eval_layouts.yaml) drawn on it: a circle
per item (C carrot orange, O Oreo blue, R RITZ red) around its grasp point. A layout that already has a saved
photo (data/eval/layouts/L<n>.jpg) is blended in at half strength, to put the items back on it.

Keys in this terminal (no Enter): 1-5 = layout, s = save the current image (without drawings) as the layout's
photo, q = quit. Keep the robot at the ready pose (its gripper is in the top view at the start of a trial).
The camera cannot be open here and in a policy run at the same time: use this between trials.

    python scripts/37_layout_guide.py              # env rb5 (or lerobot)
    python scripts/37_layout_guide.py --port 8081
    python scripts/37_layout_guide.py --sheet      # only writes data/eval/eval_sheet.csv (the trial order)
"""
import argparse
import csv
import http.server
import io
import sys
import threading
import time
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from teleop.cameras import camera_defs, open_camera  # noqa: E402
from teleop.episodes import KeyReader  # noqa: E402
from teleop.settings import SettingsError, load_settings  # noqa: E402

OUT = ROOT / "data" / "eval"
COLORS = {"C": (255, 140, 0), "O": (0, 80, 255), "R": (230, 0, 0)}     # RGB
SHEET_HEADER = ["trial", "round", "layout", "run_file", "complete", "carrot", "oreo", "ritz", "misses",
                "recoveries", "order_error", "wrong_hole", "intervention", "completion_s", "failure", "notes"]
PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Layout guide</title><style>body{margin:0;
background:#111;color:#ddd;font:16px sans-serif}img{width:960px;max-width:100%}</style></head><body>
<img src="/stream"><p>Keys in the terminal: 1-5 layout, s save photo, q quit</p></body></html>"""


def load_layouts():
    cfg = yaml.safe_load((ROOT / "configs" / "eval_layouts.yaml").read_text())
    return cfg["layouts"], int(cfg["rounds"]), np.array(cfg["top_pixel_from_xy"], dtype=float)


def trial_order(names, rounds):
    """[(round, layout)]: each round starts one layout later (L1-L5, L2-L5 L1, ...)."""
    return [(r + 1, names[(r + k) % len(names)]) for r in range(rounds) for k in range(len(names))]


def write_sheet():
    layouts, rounds, _ = load_layouts()
    path = OUT / "eval_sheet.csv"
    if path.exists():
        raise SystemExit(f"{path.relative_to(ROOT)} exists (it may hold results): not overwritten")
    OUT.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(SHEET_HEADER)
        for i, (r, name) in enumerate(trial_order(list(layouts), rounds), 1):
            w.writerow([i, r, name] + [""] * (len(SHEET_HEADER) - 3))
    print(f"saved {path.relative_to(ROOT)} ({rounds * len(layouts)} trials)")


def draw(img, layout, M, name, saved):
    import cv2
    out = img.copy()
    if saved is not None:
        out = cv2.addWeighted(out, 0.5, saved, 0.5, 0)
    for item, (x, y) in layout.items():
        u, v = (int(round(c)) for c in M @ [x, y, 1.0])
        cv2.circle(out, (u, v), 24, COLORS[item], 3)
        cv2.putText(out, item, (u - 7, v + 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLORS[item], 2, cv2.LINE_AA)
    cv2.putText(out, name + ("  (saved photo blended)" if saved is not None else "  (no photo yet)"), (8, 470),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
    return out


def serve(latest, port):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path == "/":
                body = PAGE.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path != "/stream":
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()
            try:
                while True:
                    img = latest.get("view")
                    if img is not None:
                        buf = io.BytesIO()
                        Image.fromarray(img).save(buf, "JPEG", quality=85)
                        jpg = buf.getvalue()
                        self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                                         + str(len(jpg)).encode() + b"\r\n\r\n" + jpg + b"\r\n")
                    time.sleep(0.1)
            except (BrokenPipeError, ConnectionResetError):
                return

    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()


def parse(data):
    return [c for c in data.decode("latin-1") if c in "12345sSqQ"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--sheet", action="store_true", help="only write data/eval/eval_sheet.csv (the trial order)")
    args = ap.parse_args()
    if args.sheet:
        return write_sheet()
    import cv2
    layouts, _, M = load_layouts()
    names = list(layouts)
    try:
        s, _ = load_settings(ROOT / "configs" / "real.yaml", real=True)
    except SettingsError as e:
        raise SystemExit(f"settings: {e}")
    (name, device, settings, fmt), = camera_defs(s.record, ["top"])
    cam = open_camera(device, 640, 480, 30, settings, False, fmt)
    photos = OUT / "layouts"
    photos.mkdir(parents=True, exist_ok=True)

    def saved_photo(n):
        p = photos / f"{n}.jpg"
        return np.array(Image.open(p).convert("RGB")) if p.exists() else None

    current, saved = names[0], saved_photo(names[0])
    latest = {}
    serve(latest, args.port)
    keys = KeyReader(parse=parse)
    if not keys.start():
        cam.close()
        raise SystemExit("needs a terminal for the keys")
    print(f"top camera {device}; open http://localhost:{args.port}  (1-5 layout, s save photo, q quit)")
    print(f"{current}: " + ", ".join(f"{k} {v}" for k, v in layouts[current].items()))
    try:
        while True:
            got = cam.read()
            if got is None:
                continue
            img = got[0]
            for k in keys.keys():
                if k in "12345" and int(k) <= len(names):
                    current = names[int(k) - 1]
                    saved = saved_photo(current)
                    print(f"{current}: " + ", ".join(f"{a} {b}" for a, b in layouts[current].items())
                          + ("  (photo blended)" if saved is not None else ""))
                elif k in "sS":
                    p = photos / f"{current}.jpg"
                    Image.fromarray(img).save(p, quality=95)
                    saved = saved_photo(current)
                    print(f"saved {p.relative_to(ROOT)}")
                elif k in "qQ":
                    return
            latest["view"] = draw(img, layouts[current], M, current, saved)
    finally:
        keys.stop()
        cam.close()


if __name__ == "__main__":
    main()
