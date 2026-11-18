# CAD v3: serial arm with a stepper elbow and a stepper wrist

From your v2 redlines (1: replace the wrist servo with the small stepper, 2: drive the elbow with a stepper
instead of the linkage). v2 is unchanged; v3 is a separate variant.

| What | Where |
|---|---|
| Assembly (home pose) | assembly.yaml, assembly.glb, views/*.png |
| Poses | poses/{reach-table, elbow-up, elbow-folded, stretched, yaw-limit}/assembly.yaml |
| Geometry | geometry.py (read by every part and by build_assembly.py) |
| Printed parts | printed/*.py -> *.step, printed/*.stl + print_list.csv |
| Belts as installed | belts.py -> bought/belt_*.step |
| Torque check | ../../sim/v3_check.py |
| Firmware | ../../firmware/arm_v3/arm_v3.ino (Uno: 26 % RAM, 42 % flash) |

## What changed from v2
- **Elbow:** XY42 stepper on the lower shank, 69.5 mm behind the elbow, belt (320 mm) to a 140T pulley
  printed into the upper shank: 7:1. The motor rides on the lower shank, so it drives the *relative*
  elbow angle. Range: elbow -135 to +150 deg relative (v2's linkage: about -140 to -30).
- **Wrist:** the 34 mm HEM stepper on the upper shank, 58.6 mm behind the wrist, belt (200 mm) to a 60T
  wrist pulley on two F624: 3:1. The gripper base screws to the wrist pulley. The wrist servo is gone.
- **Shoulder:** two-stage 14:1. Motor (right tower) 20T -> 72T, then a 36T on the same printed tube ->
  the 140T on the lower shank. The intermediate axle is slotted for stage-2 belt tension.
- **Yaw:** now the third XY42 (40 mm). The base has a floor cut-out so it stands on the table, and the motor
  plate is 3 mm, so the yaw belt stays at z 55 (yaw pulley, AXK2035 seat, turret height as v2).
- **Pins:** socket A drives the wrist (shield A jumpers to D12/D13), gripper servo on A3.

## Numbers (computed from the CAD, sim/v3_check.py; estimates, not measured)
- Table reach, gripper down, fingertips 15 mm up: 294 mm.
- Payload at the worst pose (arm straight out at shoulder 20 deg) within the 50 % torque budget: **~145 g**.
  With 300 g the shoulder and elbow use 67 % and 65 % of holding torque there (static OK, little margin
  for acceleration). XY42 holding torque 0.26 N·m (conservative, unpublished for the -1204A).
- Wrist: 23 % of the HEM's 0.84 N·m (3:1) with 150 g, 42 % with 300 g.
- PLA about 500 g (print_list.csv, 20 % infill estimate). Upper shank 77 g, lower shank 86 g.

## Assembly check
6 poses (home, reach-table, elbow-up q2 +80, elbow-folded q2 -135 with the gripper tilted away,
stretched, yaw +150): **0 interferences**, BOM links clean. Clearance reports: screws in clearance holes
(0.35-0.45), the deliberate 0.2 mm gap under finger B's pivot nut, 0.5 mm finger B to gripper base.
Found and fixed: gripper servo clipped the wrist pulley rim (servo moved 3 mm out, tool 105 -> 108 mm);
elbow folded to -150 with the gripper down hits the lower shank (limit now -135; firmware enforces it).

Views (iso, front, side, top, home pose) looked at: elbow motor on the lower shank with its belt to the
140T disc at the elbow; wrist motor on the upper shank with its belt to the wrist pulley; shoulder motor
at the back of the right tower with the 72T/36T compound and both belts; gripper level under the wrist;
nothing floating or crossing.

## Print check
All 17 printed parts fit the bed as modelled. Accepted: GT2/gear tooth tips (inherent), race washer 1 mm
(by design), short bridges at bearing-pocket steps and counterbore slot floors (1.5-4 mm), 45 deg cones and
teardrop roofs on the horizontal tower holes. Fixes made: compound pulley bed flange (0.9 mm) removed;
the 40 mm intermediate spacer is two 20 mm tubes.

## Hardware (all from the existing kit/packs plus one belt pack)
M4 x 70 x2 (S and I axles), M4 x 60 (yaw), M4 x 30 x2 (elbow, wrist), M3 x 8 x8 (elbow and wrist motors,
counterbored), M3 x 10 x8 (shoulder motor, deck), M3 x 6 x4 (yaw motor), M3 x 16 x8 (yaw plate, gripper
base to wrist pulley), M3 x 30 (finger pivot), F624 x14, GT2 20T x4 (pack of 5: shoulder, elbow, wrist, yaw),
belts: 320 mm x3 (yaw, shoulder stage 2, elbow), 200 mm x2 (shoulder stage 1, wrist).

## Not verified
Same as v2 (motor holding torque, MG996R mount, printed GT2 tooth fit, bearing press fit -> fit coupon),
plus: HEM wrist motor shaft (5 mm x 24 assumed), Uno step rate with 4 axes (about 4 k steps/s at the
default 20 deg/s; 1/8 microstep on the shoulder), cable routing over the moving elbow and wrist motors.
