"""t3-h: draft scoring of the evaluation runs from their logs. Reads only; never writes the trial sheet.

For every trial in data/eval/eval_sheet.csv that has a run file, reads data/policy/<run>.csv (+ .json, _video.csv)
and finds, while the policy runs (from the start key):
- closes: the gripper command crossing below 0.5; "lifted" when the target rises more than 50 mm within 3 s
  (the gripper value cannot tell a held item from an empty grasp, so a lift is not a grasp: check the video)
- releases: the command crossing above 0.5 after a lifted close, labelled by the container whose mean
  demonstrated release point (configs: docs/data_rules.md, session real_20261029_123638) is within 120 mm,
  else "elsewhere"; the container gives the item it is meant for (black box C, large hole O, small hole R)
- order: the items in the order of their first release over a container; an order error candidate when it is
  not a prefix of C, O, R
- the last release over a container (completion time candidate), the time limit, holds, the stop reason
- execution: inference time per prediction, servo interval, late and stale cycles
Times are given from the start key and as the position in the run video (mm:ss), to find them quickly.

Writes data/eval/eval_draft.csv (one row per trial) and data/eval/eval_draft_events.txt (the events per trial),
and prints the execution totals. The operator still judges every trial from the video and fills the sheet.
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "data" / "eval"
POLICY = ROOT / "data" / "policy"
# mean release positions of the three-item demonstrations [mm] (paper Section III comment, docs/data_rules.md)
CONTAINERS = {"C": ("black box", (394.0, -359.0)), "O": ("large hole", (468.0, -196.0)),
              "R": ("small hole", (370.0, -178.0))}
RELEASE_RADIUS_MM = 120.0
LIFT_MM = 50.0
LIFT_WINDOW_S = 3.0
TIME_LIMIT_S = 180.0


def load_run(stem):
    with open(POLICY / f"{stem}.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    cols = {k: np.array([float(r[k]) if r[k] not in ("", "None") else np.nan for r in rows])
            for k in ("t_s", "running", "grip_action", "target_x", "target_y", "target_z", "late", "stale_state",
                      "cycle_interval_ms", "infer_ms", "chunk_n")}
    cols["hold_reason"] = [r["hold_reason"] for r in rows]
    meta = json.loads((POLICY / f"{stem}.json").read_text())
    video = POLICY / f"{stem}_video.csv"
    vt = None
    if video.exists():
        with open(video, newline="") as f:
            vt = np.array([float(r["t_s"]) for r in csv.DictReader(f)])
    return cols, meta, vt


def video_time(vt, t):
    """mm:ss of the video frame nearest to run time t (30 fps), or '-' without a video."""
    if vt is None or not len(vt):
        return "-"
    s = int(np.argmin(np.abs(vt - t))) / 30.0
    return f"{int(s // 60):02d}:{s % 60:04.1f}"


def container_of(x, y):
    best, dist = None, None
    for item, (_, (cx, cy)) in CONTAINERS.items():
        d = np.hypot(x - cx, y - cy)
        if dist is None or d < dist:
            best, dist = item, d
    return best if dist <= RELEASE_RADIUS_MM else None


def analyse(stem):
    c, meta, vt = load_run(stem)
    run = c["running"] == 1
    if not run.any():
        return None, ["never running"], {}
    idx = np.flatnonzero(run)
    t0 = c["t_s"][idx[0]]
    t_end = c["t_s"][idx[-1]]
    t = c["t_s"]
    g = c["grip_action"]
    opened = g > 0.5
    events, closes, lifts, releases = [], 0, 0, []
    held = False                                   # a lifted close not yet released
    for i in idx[1:]:
        if opened[i - 1] and not opened[i]:
            closes += 1
            win = run & (t > t[i]) & (t < t[i] + LIFT_WINDOW_S)
            lifted = bool(win.any() and np.nanmax(c["target_z"][win]) - c["target_z"][i] > LIFT_MM)
            lifts += lifted
            held = held or lifted
            events.append((t[i], f"close {'(lifted)' if lifted else '(no lift)'} at "
                                 f"({c['target_x'][i]:.0f}, {c['target_y'][i]:.0f}, {c['target_z'][i]:.0f})"))
        elif not opened[i - 1] and opened[i] and held:
            held = False
            item = container_of(c["target_x"][i], c["target_y"][i])
            where = CONTAINERS[item][0] if item else "elsewhere"
            releases.append((t[i], item))
            events.append((t[i], f"release over {where} at ({c['target_x'][i]:.0f}, {c['target_y'][i]:.0f}, "
                                 f"{c['target_z'][i]:.0f})"))
    order = []
    for _, item in releases:
        if item and item not in order:
            order.append(item)
    over = [tr for tr, item in releases if item]
    holds = sorted({h for h, r in zip(c["hold_reason"], run) if r and h not in ("", "None")})
    row = {
        "closes": closes, "lifted": lifts,
        "releases_container": len(over), "releases_elsewhere": sum(1 for _, it in releases if not it),
        "order": "".join(order), "order_error_candidate": int("".join(order) != "COR"[:len(order)]),
        "all_three_released": int(set(order) == set("COR")),
        "last_release_s": round(over[-1] - t0, 1) if over else "",
        "last_release_video": video_time(vt, over[-1]) if over else "",
        "running_s": round(t_end - t0, 1), "time_limit": int(t_end - t0 >= TIME_LIMIT_S - 0.5),
        "holds": " ".join(holds), "stop": meta.get("stop"), "error": meta.get("error") or "",
    }
    lines = [f"  {tt - t0:6.1f} s  video {video_time(vt, tt)}  {text}" for tt, text in events]
    # execution: one prediction per new chunk number while running
    chunk = c["chunk_n"][run]
    new = np.r_[False, np.diff(chunk) > 0] & ~np.isnan(c["infer_ms"][run])
    ex = {"infer_ms": c["infer_ms"][run][new], "interval_ms": c["cycle_interval_ms"][run],
          "late": c["late"][run], "stale": c["stale_state"][run], "run_s": t_end - t0}
    return row, lines, ex


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sheet", default=str(EVAL / "eval_sheet.csv"))
    args = ap.parse_args()
    with open(args.sheet, newline="") as f:
        trials = list(csv.DictReader(f))
    rows, text, ex_all = [], [], []
    for tr in trials:
        stem = tr["run_file"]
        if not stem:
            text.append(f"trial {tr['trial']} ({tr['layout']}): no run file")
            continue
        row, lines, ex = analyse(stem)
        text.append(f"trial {tr['trial']} ({tr['layout']}), {stem}")
        text.extend(lines)
        if row is None:
            continue
        rows.append({"trial": tr["trial"], "round": tr["round"], "layout": tr["layout"], "run_file": stem, **row})
        ex_all.append(ex)
    out = EVAL / "eval_draft.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (EVAL / "eval_draft_events.txt").write_text("\n".join(text) + "\n")
    inf = np.concatenate([e["infer_ms"] for e in ex_all])
    itv = np.concatenate([e["interval_ms"] for e in ex_all])
    itv = itv[~np.isnan(itv)]
    late = int(sum(np.nansum(e["late"]) for e in ex_all))
    stale = int(sum(np.nansum(e["stale"]) for e in ex_all))
    run_s = sum(e["run_s"] for e in ex_all)
    print(f"{len(rows)} trials -> {out.relative_to(ROOT)}, events -> data/eval/eval_draft_events.txt")
    print(f"all three released over their containers: {sum(r['all_three_released'] for r in rows)}; "
          f"order error candidates: {sum(r['order_error_candidate'] for r in rows)}; "
          f"time limit: {sum(r['time_limit'] for r in rows)}")
    print(f"closes {sum(r['closes'] for r in rows)}, lifted {sum(r['lifted'] for r in rows)}")
    print(f"predictions {len(inf)} ({len(inf) / run_s:.1f}/s); inference p50 {np.percentile(inf, 50):.1f} ms, "
          f"p95 {np.percentile(inf, 95):.1f} ms; servo interval p50 {np.percentile(itv, 50):.1f} ms, "
          f"max {itv.max():.1f} ms; late {late} of {len(itv)} cycles; stale {stale}")


if __name__ == "__main__":
    main()
