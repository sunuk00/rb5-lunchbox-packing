---
license: mit
library_name: lerobot
pipeline_tag: robotics
tags:
- LeRobot
- act
- imitation-learning
- rb5
- lunchbox-packing
datasets:
- sunuk000/rb5-lunchbox-packing
---

# ACT Policy for RB5 Lunchbox Packing

An Action Chunking with Transformers (ACT) policy, trained with LeRobot 0.6.1 on the
[RB5 lunchbox packing dataset](https://huggingface.co/datasets/sunuk000/rb5-lunchbox-packing) (140 demonstrations).
It is the policy evaluated in our paper: the final checkpoint (100,000 steps), not selected by test results.

Code, videos of all 30 evaluation trials, and the robot interface: https://github.com/sunuk00/rb5-lunchbox-packing

## Inputs and outputs

- Inputs: three RGB images (front, top, grip; 320×240) and the robot state (RB5 joint angles J1–J6 in degrees,
  gripper opening 0–1)
- Output: a chunk of 100 actions (3.3 s at 30 Hz); each action is the TCP position x, y, z [mm] in the robot
  base frame and a gripper command (0 closed, 1 open). The tool orientation is fixed by a rule (gripper pointing
  down, yaw following the base azimuth) and is not predicted.

## Training

- ResNet-18 backbone (ImageNet), transformer with a 512-dimensional model, conditional VAE (KL weight 10)
- Chunk size 100, batch size 8, constant learning rate 1e-5, 100,000 steps (about 3.5 passes over the dataset)
- Normalization by the dataset mean and standard deviation

## Use

The policy is specific to the RB5-850, its cameras, and our workspace: its state input is the RB5 joint angles
and the images come from fixed camera positions. At run time we combine overlapping chunks by time (temporal
ensembling, m = 0.01) in a 50 Hz servo process and pass the result through the same command shaping as during
teleoperation; see the GitHub repository (`rb5_lerobot/run.py`).

## License

MIT
