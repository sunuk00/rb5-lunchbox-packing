"""t3-g: evaluation layouts (configs/eval_layouts.yaml), the trial sheet (data/eval/eval_sheet.csv) and the live
layout preview (the top camera in a browser with the layout's targets and its saved photo blended in).

Used by scripts/37_layout_guide.py (placing the layouts) and by rb5_lerobot.run --trial N (the policy process
serves the preview of trial N's layout). Only numpy, OpenCV, PIL and yaml: works in env rb5 and lerobot.
"""
import csv
import http.server
import io
import threading
import time
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parent.parent
LAYOUTS_FILE = ROOT / "configs" / "eval_layouts.yaml"
EVAL_DIR = ROOT / "data" / "eval"
SHEET = EVAL_DIR / "eval_sheet.csv"
PHOTOS = EVAL_DIR / "layouts"
COLORS = {"C": (255, 140, 0), "O": (0, 80, 255), "R": (230, 0, 0)}     # RGB: carrot, Oreo, RITZ
# Sheet codes (docs/data_rules.md "Evaluation"): carrot / oreo / ritz = 0 not attempted, G grasped, T transported,
# P placed in a wrong container, OK correct; complete / order_error / wrong_hole / intervention = 1 or 0.
SHEET_HEADER = ["trial", "round", "layout", "run_file", "complete", "carrot", "oreo", "ritz", "misses",
                "recoveries", "order_error", "wrong_hole", "intervention", "completion_s", "failure", "notes"]
PREVIEW_FPS = 10
PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>{title}</title><style>body{{margin:0;
background:#111;color:#ddd;font:16px sans-serif}}img{{width:960px;max-width:100%}}</style></head><body>
<img src="/stream"><p>{title}</p></body></html>"""


def load_layouts(path=LAYOUTS_FILE):
    """({name: {item: [x, y]}}, rounds, M): M maps a base-frame (x, y) at table height to a top-image pixel."""
    cfg = yaml.safe_load(Path(path).read_text())
    return cfg["layouts"], int(cfg["rounds"]), np.array(cfg["top_pixel_from_xy"], dtype=float)


def trial_order(names, rounds):
    """[(round, layout)]: each round starts one layout later (L1-L5, L2-L5 L1, ...)."""
    return [(r + 1, names[(r + k) % len(names)]) for r in range(rounds) for k in range(len(names))]


def photo_path(name):
    return PHOTOS / f"{name}.jpg"


def load_photo(name):
    """The layout's saved top photo as an RGB array, or None."""
    p = photo_path(name)
    if not p.exists():
        return None
    from PIL import Image
    return np.array(Image.open(p).convert("RGB"))


def draw(img, layout, M, title, photo=None):
    """A copy of the RGB image with the photo blended in at half strength, a circle per item target and the
    title at the bottom."""
    import cv2
    out = img.copy() if photo is None else cv2.addWeighted(img, 0.5, photo, 0.5, 0)
    for item, (x, y) in layout.items():
        u, v = (int(round(c)) for c in M @ [x, y, 1.0])
        cv2.circle(out, (u, v), 24, COLORS[item], 3)
        cv2.putText(out, item, (u - 7, v + 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLORS[item], 2, cv2.LINE_AA)
    cv2.putText(out, title, (8, out.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
    return out


def serve(get_frame, port, title):
    """MJPEG preview on 127.0.0.1:port (0 = any free port) in daemon threads; get_frame() -> RGB image or None,
    called only while a browser shows the page (PREVIEW_FPS). Returns (url, None) or (None, problem)."""
    from PIL import Image
    page = PAGE.format(title=title).encode()

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(page)))
                self.end_headers()
                self.wfile.write(page)
                return
            if self.path != "/stream":
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            try:
                while True:
                    img = get_frame()
                    if img is not None:
                        buf = io.BytesIO()
                        Image.fromarray(img).save(buf, "JPEG", quality=85)
                        jpg = buf.getvalue()
                        self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                                         + str(len(jpg)).encode() + b"\r\n\r\n" + jpg + b"\r\n")
                    time.sleep(1.0 / PREVIEW_FPS)
            except (BrokenPipeError, ConnectionResetError):
                return

    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as e:
        return None, f"layout preview not started (port {port}: {e})"
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, name="preview", daemon=True).start()
    return f"http://localhost:{server.server_address[1]}", None


# ---------- trial sheet ----------

def write_sheet(path=SHEET, layouts_file=LAYOUTS_FILE):
    """The empty sheet with the trial order. Never overwrites (it may hold results)."""
    layouts, rounds, _ = load_layouts(layouts_file)
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"{path} exists (it may hold results): not overwritten")
    path.parent.mkdir(parents=True, exist_ok=True)
    order = trial_order(list(layouts), rounds)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(SHEET_HEADER)
        for i, (r, name) in enumerate(order, 1):
            w.writerow([i, r, name] + [""] * (len(SHEET_HEADER) - 3))
    return len(order)


def read_sheet(path=SHEET):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def trial_row(n, path=SHEET):
    """The sheet's row of trial n (dict). ValueError when there is none or it already has a run file."""
    rows = [r for r in read_sheet(path) if r["trial"] == str(n)]
    if not rows:
        raise ValueError(f"no trial {n} in {path}")
    if rows[0]["run_file"]:
        raise ValueError(f"trial {n} already has run file {rows[0]['run_file']} in {path}")
    return rows[0]


def set_run_file(n, run_file, path=SHEET):
    """Writes run_file into trial n's row, keeping every other cell."""
    rows = read_sheet(path)
    for r in rows:
        if r["trial"] == str(n):
            r["run_file"] = run_file
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else SHEET_HEADER)
        w.writeheader()
        w.writerows(rows)
