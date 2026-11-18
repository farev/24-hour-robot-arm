# Prior art: 24-hour robot arm
Searched 2026-11-04: Mechy reference catalogue (Moveo, Thor, PAROL6, Faze4, Arctos, AR4, SO-101, Aaed Musa capstan/cycloidal); GitHub (pages + API for licence/stars/issues/file trees); Thingiverse via mirrors (harktech.co.uk; thingiverse.com returned 403), Printables/MakerWorld/stlfinder; Hackaday.io/Hackaday.com, Hackster, Instructables (bodies returned 403/empty); arXiv; Reddit r/robotics (mirror); commercial resellers (RobotShop, OpenELAB, Elektor, Mouser, RoboDK).
Phrases: "EEZYbotArm MK2 stepper NEMA17 conversion", "MK2 Plus stepper remix", "Dobot clone 3D printed NEMA17 parallelogram", "uArm Swift clone open source stepper", "robot arm CNC shield A4988 Arduino Uno NEMA17 palletizing", "20sffactory community robot arm", "Florin Tobler robot arm", "GT2 belt reduction robot arm joint NEMA17 payload", "capstan drive robot arm 3D printed stepper", "3D printed cycloidal NEMA17 shoulder torque backlash", "hackaday 4 DOF stepper parallelogram belt", "reddit 3D printed arm NEMA17 300g payload", commercial spec searches.
Legend: [read] = read from linked page/file; [est] = our estimate; [computed] = Mechy arm model.

## Recommendation
The closest build is the **20sffactory Community Robot Arm** (Tobler lineage): 3x NEMA 17, Dobot-style palletizer
parallelogram with both arm motors on the turret, GT2 20T->90T belts, Uno + CNC Shield V3 + A4988, servo gripper —
our exact electronics. Mechy has its STLs vendored (v1 is built from them).

Two problems for this brief [computed, `sim/torque_check.py`]:
1. Table reach: the yaw motor hangs 38 mm below the socket, so the arm needs a riser; with a 45 mm riser the tool can
   only reach the table plane at ~6 cm height and 24 cm radius. Without a riser it reaches 26.8 cm at 3 cm height.
2. Torque: 300 g puts the shoulder at 48 % of holding x 4.5 (budget 50 %) with the conservative 0.26 N·m motor figure.
   The parallel linkage helps a lot (each motor carries only its own shank's lever arm), but the margin is thin.

So: **borrow the layout and firmware design, draw our own geometry** (v2): same parallel linkage, ~160 mm shanks,
yaw motor beside the turntable so the base sits flat on the table (the owned AXK2035 carries the turntable), and a
two-stage GT2 belt reduction (~10-13:1) on shoulder and elbow. Keep v1 (stock) as the quick fallback.

## Closest builds
| Build | Link | Licence / reuse | Key numbers | Main parts | Published files | Maturity |
|---|---|---|---|---|---|---|
| 20sffactory Community Robot Arm | [GitHub](https://github.com/20sffactory/community_robot_arm), [docs](https://nguyenle15325.github.io/Community-Robot-Arm/hardware.html) | Repo LICENSE GPL-3.0 [read, GitHub API]; README: CAD CC BY 4.0, firmware GPL-3.0 [read]; CAD derives from Tobler's CC BY-NC original → treat as non-commercial (fine for a student build) | GT2 20T→90T = 4.5:1 [read, [config.h](https://raw.githubusercontent.com/20sffactory/community_robot_arm/master/arduino_firmware/config.h_samples/config_sample_V0.61/20sffactory_rail/config.h)]; links 140+140 mm [read]; 1/16 microstep; payload not stated | 3x NEMA17, A4988/DRV8825, Uno/Nano + CNC shield V3/V4, 3 microswitch endstops, servo gripper [read] | STL + robot_arm.step, BOM image, firmware V0.31-V0.81 [read] | 215 stars, 93 forks, last push 2022-05-26 [read] |
| Florin Tobler RobotArm | [Thingiverse 1718984 (mirror)](https://harktech.co.uk/m/thingiverse/1718984), [GitHub](https://github.com/ftobler/robotArm) | CC BY-NC [read] | Printed gears 9T→32T = 3.56:1; links 120+120 mm [read] | NEMA17, Mega + RAMPS 1.4 + A4988, 12 V [read] | STL, firmware, GUI [read] | 61k downloads; repo pushed 2025-07-12 [read] |
| Forte (Chebly et al. 2025) | [arXiv 2507.15693](https://arxiv.org/html/2507.15693v1) | Paper CC BY 4.0; hardware not released → reference only | 0.63 kg measured, reach 467 mm, $212 [read] | J2 NEMA23 belt 2.5:1 x capstan = 18.75:1; base NEMA17 capstan 8:1; Uno + A4988/TB6600, 24 V [read] | Paper only | 2025 preprint |
| EEZYbotARM MK2 / MK2 Plus | [MK2 (mirror)](https://harktech.co.uk/m/thingiverse/1454048), [MK2 Plus](https://www.mfgrobots.com/Article/mfg/mpm/16952.html) | MK2 CC BY-NC [read]; Plus licence not read | ABB IRB460 linkage at 1:7 [read] | Plus: 3x NEMA17, Uno + CNC shield + A4988, 3 limit switches, 12 V [read] | STL + [code](https://github.com/yasaspeiris/MK2-Robot-Arm-Controller) | 191k downloads (MK2) [read] |
| Marginally Clever Arm3 palletizer | [blog](https://www.marginallyclever.com/2014/03/building-an-open-source-3dof-palletizing-robot/), [Tindie](https://www.tindie.com/products/i-make-robots/3dof-robot-arm-50cm-reach-125g-payload/) | No licence → reference only | 125 g at 50 cm [read, vendor claim] | 3x NEMA17 0.3 A, double parallelogram [read] | Firmware, plywood DXF | Retired kit |
| Open6X | [Hackaday.io](https://www.hackaday.io/project/181875-open6x-robot-arm/details) | Not named | 0.5 kg near full extension; a driver burned [read] | J2 NEMA23 20:1 [read] | Not checked | Rev 1 |
| Catalogue: Moveo / Thor / PAROL6 / Musa capstan | designs.csv | MIT / CC BY-SA / GPL-3.0 / none | Thor 750 g stretched (5:1 geared + belts) | | | |

## What to reuse
- 20sffactory layout: coaxial turret motors, elbow push rod (pleuel) + parallelogram, levelling plate (also Tobler, MK2, Arm3).
- Its servo gripper (MG90S) and the GT2 20T motor pulleys (owned) → printed GT2 pulleys.
- Firmware ideas only (V0.81 is GPL-3.0): G-code-ish serial commands, palletizer IK, Uno pinout for CNC Shield V3, 3-switch homing. Mechy's firmware is written from scratch.
- Wiring: endstops COM→GND, NO→pin with INPUT_PULLUP; shared ENABLE for cut-off; set VREF before connecting motors ([docs](https://nguyenle15325.github.io/Community-Robot-Arm/hardware.html)).
- Forte's belt + capstan shoulder as the fallback if belts fall short (reference only).

## Problems others hit
- Printed spur gears give slack (Tobler) → belts, not printed spur gears.
- 4.5:1 on 140 mm links publishes no payload; our computed shoulder load is 48 % of holding x 4.5 → second belt stage in v2.
- Driver burned out at 0.5 kg ([Open6X](https://www.hackaday.io/project/181875-open6x-robot-arm/details)) → A4988 VREF for ≤1.0 A, heatsinks + a fan.
- Missed steps above 0.63 kg, worse with speed ([Forte](https://arxiv.org/html/2507.15693v1)) → conservative acceleration, home on every power-up.
- PLA forearm needed torsional support (Forte) → box-section links, load along layers.
- Printed pulleys skip under torque ([michaelteeuw](https://michaelteeuw.nl/post/pulley-belt-transmission)) → ≥ 60T outputs, tensioner, ≥ 6 teeth in mesh.
- Reversed A4988 is destroyed; motors homing the wrong way ([MK2 Plus](https://www.mfgrobots.com/Article/mfg/mpm/16952.html)) → soft limits, homing timeout, first power-up unloaded.
- 16-bit step-counter overflow (20sffactory PR #8) → 32-bit step positions.
- Yaw motor below the socket (found in Mechy's v1 assembly: 38 mm below) → base that sits flat on the table.

## Benchmarks
| Product | Price | Reach | Payload |
|---|---|---|---|
| Dobot Magician | $1,427-1,784 ([OpenELAB](https://openelab.io/a/s/products/dobot-magician-education-robot-arm)) | 320 mm | 500 g |
| Dobot Magician Lite | $732 ([OpenELAB](https://openelab.io/a/s/products/dobot-magician-lite-education-robot)) | 340 mm | 250 g |
| uArm Swift Pro | €939 ([Elektor](https://www.elektor.com/products/ufactory-uarm-swift-pro)) | 50-320 mm | 500 g |
| Rotrics DexArm | ~£837-1,032 ([RobotShop](https://uk.robotshop.com/products/rotrics-dexarm-luxury-edition-multi-functional-4-axis-desktop-robotic-arm-uk)) | 380 mm | 500 g |

Our target (300 g at ~300 mm) is Dobot/uArm class.
