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
| act_u4_20261030_054110 | u4 | 100k | rb5-lunchbox | 30k: 22.5 / 32.5 / 44.2; 60k: 15.4 / 21.1 / 31.7; 100k: 13.6 / 17.6 / 23.9 | t3-d |

## Real policy runs (`data/policy/run_real_<time>.csv / .json`)

| Run | Checkpoint | What happened | Step |
|---|---|---|---|
| run_real_20261029_023402, _024159 | act_t1 030000 | placed well, grasped poorly, no recovery after a miss | t2 |
| run_real_20261029_120825 | act_u3 030000 | three objects on the table: lost after the carrot; after a miss reopened and retried but 5-7 cm further each time (10 in a row) | t3-d |
| run_real_20261030_025146 | act_u4a 100000 | 2 x 180 s, objects reset inside a run (4 trials): order right in 2 of 3 finished trials (once RITZ before Oreo), holes always right; first-try grasps 6 of 11; after a miss retried at about the same spot (0.4-4 cm) and got it after 2-8 tries | t3-e |
| run_real_20261030_130515 | act_u4 100000 | 2 x 180 s, objects reset at random moments inside a run (not separable into trials); inference p50 39.6 ms (17 ms offline; run 8 min after training ended), no late cycles: some RITZ before Oreo, and RITZ put in the large hole; 3 sequences carrot -> Oreo -> RITZ seen in the log (one with all first-try grasps); after a miss moved 1-7 cm before retrying, but once 8 carrot misses in a row creeping 0.5-3 cm each; recovery judged still weak by the operator | t3-d |
| run_real_20261031_060058 .. _070729 (20 trials, `data/eval_t3g/eval_sheet.csv`; layout photos in `data/eval_t3g/layouts/`) | act_u4 100000 | **Evaluation (t3-g)**, 5 layouts x 4 rounds: complete success 12/20 = 60 % (Wilson 95 % 39-78 %), 11/20 also in order; by layout L1 4/4, L2 1/4, L3 1/4, L4 4/4, L5 2/4. Stages (conditional) grasp / transport / place / correct: carrot 19/20, 19/19, 19/19, 19/19; Oreo 19/20, 16/19, 16/16, 16/16; RITZ 15/19, 15/15, 14/15, 14/14 (1 not attempted); correct items 49/60; no wrong hole. First-try grasps 29/59; closes 181, of which 54 lifted an item (94 closes in the 4 stalled trials); recovery 24/30 items (carrot 11/12, Oreo 7/8, RITZ 6/10). Order errors 3 (Oreo before carrot, all L5); in L4 the first reach went to the nearest RITZ in 4/4 (missed, then carrot). Completion of the 12 successes: median 54.1 s, mean 56.9 s (40.4-82.6; teleoperation episodes 58.8 s). Failures: L3 Oreo nearest the base, grasped at the finger edge and dropped on the way beside the black box (2) or never grasped (1), then not grasped again, repeated closes at an empty spot until 180 s, RITZ not grasped either (3); L2 far RITZ never approached, stalled (2); RITZ on the rim (1); Oreo held barely and dropped on the way (1); intervention, carrot re-placed by hand (1). Inference p50 23.7 ms, p95 50.1 ms; servo p50 20.0 ms, max 40.3 ms, 30 late cycles of 95,913; no stale state, no holds. Six short starts left only a video (no run csv, not in the sheet): not trials | t3-g |

Comparisons planned for the paper: u1 vs u3 (recovery, one snack), u4a vs u4 (recovery, three objects).
From the next evaluation on: one `g` per trial (objects reset while holding), so each trial has its own
180 s limit and log.
