# docs

| File / folder | What it is | Read it when |
|---|---|---|
| `teleop_guide.md` | How to run the teleop: setup (Python, network, udev rule), before a run, run, controls (normal / rotate mode), speeds and range, stopping, error messages | running the teleop |
| `real_first_run_checklist.md` | Required items before every Real run, and the open items with the lab (tool mass, TCP, base +x, z floor) | before every Real run |
| `pipeline_guide.md` | Commands for one round of the learning pipeline: collect (Real teleop), check and convert, train ACT, offline check, Simulation run | every round of collect -> train -> run |
| `data_rules.md` | Rules of the demonstrations: task, placement, how to demonstrate, cameras, sessions, evaluation | before every collection session |
| `hardware.md` | Lab hardware facts: RB5, PC, leader arm, cameras, gripper (MX-106T), with sources and TBD items | checking a device fact |
| `experiments.md` | Every dataset, training run and Real policy run by its name on disk, with what it contains and its results | naming or comparing runs, writing the paper |
| `decisions.md` | Every decision with date, reason, measurements and rejected options; topic list at the top, open items (PENDING) at the end | "why is this value like this?" |
| `measurements/` | CSV + plot of the measurements from scripts 09 (data channel read rate), 10 (servo streaming rate) and 11 (leader arm read rate) | comparing timing |
| `patches/` | Diff of script 15 against rby1-sdk example 35 | updating script 15 |
| `logs/` | Task logs in Korean, one per step (`YYYY-MM-DD_<step>_<name>.md`). **Not committed** (only on this PC) | reviewing what was done and why |
