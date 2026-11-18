# GitHub - 20sffactory/community_robot_arm: Repository of Community Robot Arm Documents (web page)

Source: https://github.com/20sffactory/community_robot_arm · GitHub · licence: CC BY 4.0

| What | Where |
|---|---|
| Source metadata | inspiration/github-20sffactory-community-robot-arm/source.json |
| Page text (html.parser) | inspiration/github-20sffactory-community-robot-arm/page.txt |
| Images (6, EXIF-free) | inspiration/github-20sffactory-community-robot-arm/images/ |

Description: Repository of Community Robot Arm Documents. Contribute to 20sffactory/community_robot_arm development by creating an account on GitHub.

## Images
| # | Image | Alt text | Shows |
|---|---|---|---|
| 1 | inspiration/github-20sffactory-community-robot-arm/images/01.jpg | og:image | TODO(research) |
| 2 | inspiration/github-20sffactory-community-robot-arm/images/02.jpg |  | TODO(research) |
| 3 | inspiration/github-20sffactory-community-robot-arm/images/03.jpg |  | TODO(research) |
| 4 | inspiration/github-20sffactory-community-robot-arm/images/04.jpg |  | TODO(research) |
| 5 | inspiration/github-20sffactory-community-robot-arm/images/05.jpg |  | TODO(research) |
| 6 | inspiration/github-20sffactory-community-robot-arm/images/06.jpg |  | TODO(research) |

## Mechanism mentions (page text)
Counts: servo 1.
- "arduino_firmware Version V0.51 (03Apr2021) Servo Gripper Option arduino_firmware Version V0.41 (24Feb2021)"

## Embedded videos (digest each with `mechy intake add <url>`)
- https://www.youtube.com/watch?v=yh1NoQ2Z36A

## Research notes
- Mechanism and layout: Dobot-style palletizer; lower shank + lever/pleuel drive both on the turret, two levelling links + triplate keep the tool level; 140 + 140 mm shanks (config.h).
- Actuators, transmission, bearings, specs (cite timestamps/frames): 3x NEMA 17, GT2 20T → printed 90T (4.5:1), 51105 base thrust bearing, F624/F686 flanged bearings, Uno + CNC Shield V3 + A4988, 3 microswitch endstops, MG90S servo gripper. No payload published. Repo LICENSE GPL-3.0; README says CAD CC BY 4.0 (derived from Tobler's CC BY-NC).
- Copy / avoid for this project: copy the linkage layout, gripper and electronics mapping (v1 is built from its STLs). Avoid: yaw motor hanging 38 mm below the socket (needs a riser → can't reach its own table plane), thin torque margin at 300 g, 16-bit step counter overflow (PR #8).

Not verified: machine-made digest; page text is extracted automatically and claims on it are unchecked.
