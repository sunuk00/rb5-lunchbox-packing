---
license: cc-by-4.0
task_categories:
- robotics
tags:
- LeRobot
- imitation-learning
- teleoperation
- rb5
- lunchbox-packing
pretty_name: RB5 Lunchbox Packing Demonstrations
size_categories:
- 100K<n<1M
---

# RB5 Lunchbox Packing Demonstrations

140 teleoperated demonstrations of a lunchbox-packing task on a Rainbow Robotics RB5-850, recorded with a
kinematically different leader arm (RB-Y1, seven joints) and three RGB cameras. In LeRobot format (v3.0), 30 Hz.

**Task:** put the carrot (a model) in the black box, then the Oreo in the large hole and the RITZ in the small
hole of the meal box, always in that order.

Code, videos, and the policy trained on this dataset: https://github.com/sunuk00/rb5-lunchbox-packing

## Contents

| Episodes | Content |
|---|---|
| 0–48 | Carrot and one snack (Oreo or RITZ), normal demonstrations |
| 49–64 | Carrot and one snack, recovery demonstrations (one deliberate missed grasp, then a re-grasp) |
| 65–115 | All three items, normal demonstrations |
| 116–139 | All three items, recovery demonstrations (each item missed 8 times, in four directions) |

228,583 frames in total. In the episodes with one snack, the other snack is absent; the same rule applies (the
task string says "the snack").

## Features

| Key | Shape | Meaning |
|---|---|---|
| `observation.state` | 7 | RB5 joint angles J1–J6 [deg] (encoders), gripper opening (0 closed, 1 open) |
| `action` | 4 | Commanded TCP position x, y, z [mm] in the robot base frame, gripper command (0 closed, 1 open) |
| `observation.images.front` | 240×320×3 | Fixed camera, oblique view from the front (RealSense D435, RGB only) |
| `observation.images.top` | 240×320×3 | Fixed camera above the item area, looking down (Logitech C270) |
| `observation.images.grip` | 240×320×3 | Camera on the gripper, sees the fingers (Logitech Brio 101) |

- The action is the target the robot was commanded to reach after command shaping (workspace, speed,
  singularity and joint limits, acceleration), not its measured motion.
- The tool orientation is not part of the action: roll and pitch keep the ready pose (gripper pointing down),
  and the yaw follows the azimuth of the target about the base axis.
- Images were recorded at 640×480 with fixed exposure, gain, and white balance and reduced to 320×240.
- Targets and joint states were recorded at 50 Hz and interpolated to the 30 Hz grid; for each camera, the frame
  nearest to each grid time is used.

## Setup

- Robot: Rainbow Robotics RB5-850 with an in-house 3D-printed parallel gripper (Dynamixel MX-106)
- Leader: Rainbow Robotics RB-Y1 leader arm, read only; the wrist position is mapped, relative to a clutch press,
  to the RB5 tool position in cylindrical coordinates about the base axis
- Containers fixed on the table; items placed at random positions within the view of the top camera,
  oriented so that the fingers close across them without wrist rotation

## License

CC BY 4.0
