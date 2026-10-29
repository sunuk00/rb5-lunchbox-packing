# Experiments: datasets, trainings, policy runs

One line per dataset, training and evaluation run, with the names on disk (`data/` is not committed: these
names are the only link between the paper and the files). Add a line whenever one is made. Details of how
each was decided: `docs/decisions.md` (step id in the last column).

## Datasets (`data/lerobot/<name>`)

All 30 fps, images 320x240; state = 6 joints + gripper position, action = x, y, z (mm) + gripper open.
Dataset episode numbers count kept episodes in order; `notes.txt` in each session uses attempt (folder) numbers.

| Name | Episodes | Frames | Made from | Content | Step |
|---|---|---|---|---|---|
| p1 | 51 | 27527 | real_20261021_154730 | first pipeline round, block task; cameras front, wrist, grip | p1 |
| p2 | 72 | 48256 | p1 session + real_20261022_102657 | p1 + 21 more (fine-tune test) | p3-e |
| t1 | 51 | 76342 | real_20261028_125422, real_20261028_132815 | pilot: carrot + Nutter Butter; cameras front, top, grip (since t2-a) | t2 |
| u1 | 49 | 70550 | real_20261029_042055 (51 kept; 51, 52 left out) | normal, carrot + one snack (25 Oreo, 24 RITZ), 9 natural re-grasps (= t3n) | t3-c |
| u2 | 16 | 24862 | real_20261029_063325 | recovery, carrot + one snack, misses 9-23 cm mostly to the right | t3-c |
| u3 | 65 | 95412 | merge u1 + u2 | u1 (eps 0-48) + u2 (49-64) (= t3r) | t3-c |
| u4n | 51 | 89899 | real_20261029_123638 | normal, three objects (carrot -> Oreo -> RITZ), 7 natural re-grasps | t3-d |
| u4a | 116 | 185311 | merge u3 + u4n | u3 (eps 0-64) + u4n (65-115): three-object normal, no three-object recovery | t3-e |
| u4r | 24 | 43272 | real_20261030_040425 | recovery, three objects: one miss each, 8 per object, all four directions, lift 8-15 cm | t3-d |
| u4 | 140 | 228583 | merge u4a + u4r | u4a (eps 0-115) + u4r (116-139) | t3-d |

## Trainings (`data/train/act_<dataset>_<time>`)

ACT, batch 8, constant learning rate 1e-5, chunk 100, resnet18, dim 512, VAE (kl_weight 10) unless noted.
Prediction error = `rb5_lerobot.check` on 200 training frames, median position error at +1 / +30 / +99 steps.

| Run folder | Dataset | Steps | WandB | Prediction error (mm) | Step |
|---|---|---|---|---|---|
| act_p1_20261022_021540 | p1 | 50k (20k, resumed) | no | | p2-c |
| act_p2_20261022_111930 | p2 | 10k of 30k, fine-tuned from act_p1 050000 | no | | p3-e |
| act_t1_20261028_160120 | t1 | 30k | no | 30k: 22.3 / 28.4 / 38.2 | t2 |
| act_u3_20261029_073415 | u3 | 30k | no | 30k: 23.5 / 25.6 / 30.9 | t3-c |
| act_u1_20261029_094524 | u1 | 30k | no | not checked | t3-c |
| act_u4a_20261029_161728 | u4a | 100k | rb5-lunchbox | 30k: 24.0 / 34.2 / 42.3; 60k: 15.8 / 23.0 / 29.0; 100k: 11.9 / 16.0 / 26.4 | t3-e |
| act_u4_20261030_054110 | u4 | 100k (running) | rb5-lunchbox | | t3-d |

## Real policy runs (`data/policy/run_real_<time>.csv / .json`)

| Run | Checkpoint | What happened | Step |
|---|---|---|---|
| run_real_20261029_023402, _024159 | act_t1 030000 | placed well, grasped poorly, no recovery after a miss | t2 |
| run_real_20261029_120825 | act_u3 030000 | three objects on the table: lost after the carrot; after a miss reopened and retried but 5-7 cm further each time (10 in a row) | t3-d |
| run_real_20261030_025146 | act_u4a 100000 | 2 x 180 s, objects reset inside a run (4 trials): order right in 2 of 3 finished trials (once RITZ before Oreo), holes always right; first-try grasps 6 of 11; after a miss retried at about the same spot (0.4-4 cm) and got it after 2-8 tries | t3-e |

Comparisons planned for the paper: u1 vs u3 (recovery, one snack), u4a vs u4 (recovery, three objects).
From the next evaluation on: one `g` per trial (objects reset while holding), so each trial has its own
180 s limit and log.
