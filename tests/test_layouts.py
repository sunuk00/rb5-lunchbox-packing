"""Tests for rb5_lerobot.layouts (t3-g): the layouts file, the trial order, drawing, the trial sheet, and the
layout preview served by the policy process (fake cameras). Run: python -m unittest discover tests"""
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from rb5_lerobot.layouts import (draw, load_layouts, read_sheet, set_run_file, trial_order, trial_row,  # noqa: E402
                                 write_sheet)
from rb5_lerobot.policy import PolicyClient  # noqa: E402


class TestLayouts(unittest.TestCase):
    def test_file_and_order(self):
        layouts, rounds, M = load_layouts()
        self.assertEqual(list(layouts), ["L1", "L2", "L3", "L4", "L5", "L6"])
        self.assertTrue(all(set(v) == {"C", "O", "R"} for v in layouts.values()))
        self.assertEqual(M.shape, (2, 3))
        order = trial_order(list(layouts), rounds)
        self.assertEqual(len(order), 30)
        self.assertEqual([n for _, n in order[:8]], ["L1", "L2", "L3", "L4", "L5", "L6", "L2", "L3"])
        for name in layouts:                                   # every layout 5 times, once per round
            self.assertEqual(sorted(r for r, n in order if n == name), [1, 2, 3, 4, 5])
        nearest_first = {"".join(sorted(v, key=lambda k: np.hypot(*v[k]))) for v in layouts.values()}
        self.assertEqual(nearest_first, {"COR", "CRO", "OCR", "ORC", "RCO", "ROC"})   # one layout per order
        for v in layouts.values():                             # every target inside the 640 x 480 top image
            for x, y in v.values():
                u, w = M @ [x, y, 1]
                self.assertTrue(0 <= u < 640 and 0 <= w < 480)

    def test_draw_keeps_the_input(self):
        layouts, _, M = load_layouts()
        img = np.full((480, 640, 3), 100, np.uint8)
        out = draw(img, layouts["L1"], M, "L1")
        self.assertTrue((img == 100).all())                    # drawn on a copy
        u, v = (int(round(c)) for c in M @ [*layouts["L1"]["C"], 1])
        self.assertFalse((out[v - 30:v + 30, u - 30:u + 30] == 100).all())
        photo = np.full_like(img, 200)
        self.assertEqual(draw(img, layouts["L1"], M, "L1", photo)[5, 5, 0], 150)   # blended at half strength


class TestSheet(unittest.TestCase):
    def test_write_read_and_run_file(self):
        path = Path(tempfile.mkdtemp()) / "sheet.csv"
        self.assertEqual(write_sheet(path), 30)
        with self.assertRaises(FileExistsError):
            write_sheet(path)
        self.assertEqual(trial_row(7, path)["layout"], "L2")
        rows = read_sheet(path)
        rows[6]["notes"] = "kept"
        import csv
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        set_run_file(6, "run_real_x", path)
        self.assertEqual(read_sheet(path)[5]["run_file"], "run_real_x")
        self.assertEqual(read_sheet(path)[6]["notes"], "kept")          # other cells unchanged
        with self.assertRaises(ValueError):
            trial_row(6, path)                                          # already run
        with self.assertRaises(ValueError):
            trial_row(99, path)


class TestPreviewInThePolicyProcess(unittest.TestCase):
    def test_preview_url_and_frame(self):
        layouts, _, M = load_layouts()
        acts = np.c_[np.zeros((300, 3)), np.ones(300)]
        pv = {"port": 0, "camera": "top", "layout": layouts["L3"], "layout_name": "no_such_layout",
              "M": M.tolist(), "title": "Trial 3"}
        client = PolicyClient({"kind": "replay", "actions": acts.tolist(), "fps": 30, "preview": pv},
                              [("front", "bright@50", None), ("top", "bright@100", None)], fake_cameras=True)
        self.addCleanup(client.close)
        self.assertEqual(client.open(), [])
        url = client.info["preview"]
        self.assertTrue(url.startswith("http://localhost:"), url)
        self.assertIn(b"Trial 3", urllib.request.urlopen(url + "/", timeout=3).read())
        data = urllib.request.urlopen(url + "/stream", timeout=3).read(80000)
        a = data.index(b"\xff\xd8")
        jpg = data[a:data.index(b"\xff\xd9", a) + 2]
        import cv2
        img = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
        self.assertEqual(img.shape, (480, 640, 3))
        self.assertAlmostEqual(float(np.median(img)), 100, delta=5)   # the top camera, not the front one

    def test_no_preview_without_the_spec(self):
        client = PolicyClient({"kind": "replay", "actions": [[0, 0, 0, 1]] * 300, "fps": 30},
                              [("top", "bright@100", None)], fake_cameras=True)
        self.addCleanup(client.close)
        self.assertEqual(client.open(), [])
        self.assertIsNone(client.info["preview"])
        time.sleep(0.1)


if __name__ == "__main__":
    unittest.main()
