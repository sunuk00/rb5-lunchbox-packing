# Task-Space Imitation Learning for Robotic Lunchbox Packing

A Rainbow Robotics RB5-850 learns to pack a lunchbox from demonstrations given with a kinematically different
leader arm (RB-Y1, seven joints). The policy puts a model carrot into a black box, then an Oreo into the large
hole and a RITZ into the small hole of a meal box, in that order, from three RGB cameras.


https://github.com/user-attachments/assets/425b3098-4494-44a5-b52f-3b8b0602c27f


*Autonomous runs at 2x speed: a successful trial; missed grasps of the carrot and the Oreo, each followed by a
re-grasp and placement; and a failure in which the fingertips flick the carrot away. The evaluation (30 trials over six item layouts) is reported in the paper.*

<a href="https://www.youtube.com/watch?v=fSTNVyvqDPw"><img src="https://img.youtube.com/vi/fSTNVyvqDPw/hqdefault.jpg" width="480" alt="All 30 evaluation trials (YouTube)"></a>

*All 30 evaluation trials in order, each from its start key, at 2x speed (YouTube).*


https://github.com/user-attachments/assets/e72469f6-33c4-4588-9682-cf0d848952c3


*Demonstration collection (time-lapse): the operator behind the table teleoperates the RB5 with the leader arm
while the three cameras record.*

## System

![System architecture](docs/images/architecture.png)

- **Teleoperation.** The leader arm is only read. Forward kinematics gives its wrist position, which is mapped,
  relative to a clutch press, to the RB5 tool position in cylindrical coordinates about the robot base axis
  (forward and back move along the arm, up and down change the height, a mode button turns the base). The
  gripper follows an analog trigger.
- **One command path.** Teleoperation targets and policy actions pass through the same command shaping
  (workspace, speed, singularity and joint limits, acceleration) and are streamed to the controller with
  `move_servo_l` at 50 Hz. The recorded action is the shaped target the robot executed.
- **Learning.** Robot states, targets, and the three camera streams share one clock; a converter builds a
  LeRobot dataset, and an ACT policy predicts Cartesian position targets and gripper commands. At run time,
  chunks are combined by time in a separate 50 Hz servo process.

## Hardware

| Part | Model | Role |
|---|---|---|
| Follower robot | Rainbow Robotics RB5-850 (control box 8.4.4) | Six-joint arm that packs the items |
| Leader arm | Rainbow Robotics RB-Y1 leader (Dynamixel, U2D2) | Read-only input for teleoperation: right arm and clutch, left handle for the mode button and trigger |
| Gripper | In-house 3D-printed parallel gripper, Dynamixel MX-106 | Grasps the items; follows the trigger or the policy |
| Front camera | Intel RealSense D435 (RGB only) | Fixed, oblique view of the workspace |
| Top camera | Logitech C270 | Fixed above the item area, looking down |
| Grip camera | Logitech Brio 101 | On the gripper, sees the fingers |
| Host PC | Linux laptop, Intel i7-13700H, NVIDIA RTX A1000 | Teleoperation, recording, training, policy runs |

## Usage

Two conda environments: `rb5` (teleoperation, recording; `environment.yml`) and `lerobot` (LeRobot 0.6.1;
`environment_lerobot.yml`). Linux only.

```bash
python -m teleop --real --record                       # env rb5: demonstrations -> data/demos/<session>/
python -m rb5_lerobot.convert SESSION ... --name NAME  # env lerobot: -> LeRobot dataset
python -m rb5_lerobot.train NAME                       # ACT training
python -m rb5_lerobot.check TRAINING                   # offline check on recorded episodes
python -m rb5_lerobot.run TRAINING [--real]            # the policy drives the robot
```

Without `--real`, the robot runs in the controller's simulation mode. Read
`docs/real_first_run_checklist.md` before any real-robot run; the command shaping is not collision avoidance.

Guides: `docs/pipeline_guide.md` (demonstrations to policy runs), `docs/teleop_guide.md`,
`docs/data_rules.md` (how demonstrations and the evaluation were done), `docs/hardware.md`.

## Repository

- `teleop/` leader arm to RB5 teleoperation, recording; `rb5_lerobot/` dataset, training, policy runs
- `configs/` teleoperation (`real.yaml`, `sim.yaml`), learning and policy runs (`policy.yaml`), evaluation layouts
- `scripts/` numbered test and analysis scripts (`scripts/README.md`); `tests/` unit tests with fake devices
- `assets/` leader arm URDF (from rby1-sdk, Apache 2.0, see its LICENSE and NOTICE) and udev rules

The robot and leader arm images in the architecture figure were generated with ChatGPT (OpenAI, gpt-image)
from photographs of our hardware.

## License

MIT (see `LICENSE`), except `assets/leader_arm/`, which keeps its Apache 2.0 license and NOTICE.
