# CAD v2: Mechy-designed parallel-linkage arm

| What | Where |
|---|---|
| Assembly (home pose) | assembly.yaml, assembly.glb, views/{iso,front,side,top}.png |
| Extreme poses | poses/{reach-table,folded-high,stretched,yaw-limit}/assembly.yaml |
| Geometry source of truth | geometry.py (all printed parts and build_assembly.py read it) |
| Printed parts | printed/*.py -> *.step, exported printed/*.stl + print_list.csv |
| Fit coupon (print first) | printed/fit_coupon.stl |
| Belts as installed | belts.py -> bought/belt_*.step |
| Firmware | ../../firmware/arm_v2/arm_v2.ino (Uno, builds: 25 % RAM, 44 % flash) |

## Concept
Dobot / 20sffactory-style parallel linkage: the shoulder motor drives the lower shank (140T pulley in
the same print), the elbow motor drives a 140T lever pulley on the same axle whose crank pin L pushes the
pleuel, so the upper shank's absolute pitch equals the lever angle (parallelogram S-E-PU-L, lever 35 mm,
links 150 + 150 mm). Both arm motors sit on the turret behind the axle (counterweight). Wrist: MG996R on
the upper shank keeps the gripper pointing down (or tilts it); gripper: MG996R + two 16T m1.5 gear fingers.
Yaw: HEM 34 mm motor beside the base, 20T -> 120T ring under the turret, turret on the owned AXK2035 with
two F624 on an M4 x 60 centre bolt. Base sits flat on the table (the v1 problem is gone).

Numbers (computed from geometry.py and the CAD masses; `sim/v2_check.py`, estimates, not measured):
- Table reach, gripper down, fingertips 15 mm above the table: 294 mm from the yaw axis (reach-table pose: tip at x 284, z 16).
- Worst gravity load with 300 g: shoulder 0.74 N·m (41 % of 0.26 N·m x 7), elbow 0.67 N·m (37 %).
- Belt tension at the 20T at full holding torque: 41 N.
- Printed PLA about 434 g at 20 % infill (print_list.csv); print the shanks, pulleys and turret with 4 walls, 30 % gyroid.

## Assembly check (python -m mechy.design_tools check)
All five poses: **0 interferences**, BOM links clean (linked, no unknown/missing/drift).
Remaining clearance reports, all expected:
- base / yaw-pulley vs yaw-bolt 0.45 mm, turret vs deck screws 0.35 mm: centred screws in clearance holes ((hole - screw)/2).
- pleuel vs l-washer-2 0.5 mm: washer in the Ø10 relief, at the limit.
- finger-b vs grip-pivot-nut 0.2 mm: deliberate gap so finger B turns freely (lock the nut with a second nut or thread glue).

Poses checked: home (lower shank vertical, upper level, gripper down), reach-table (th1 25, th2 -23),
folded-high (th1 135, th2 55, gripper tilted to -30), stretched (th1 30, th2 0, interior 150 deg, gripper
forward), yaw-limit (+150 deg). Found and fixed along the way: gripper-down collides with the upper shank
when th2 > 30 (firmware refuses it); an M4 x 25 at PU reached the lower shank at full stretch (now M4 x 20,
flush with its nut); Uno/buck overlapped the yaw motor posts (moved); teardrop helper had its roof upside
down (fixed in lib.py).

Allowed contacts (assembly.yaml `allow_contact`, each with its reason): bearings in their press pockets,
bolts in their snug holes / bearing bores / nuts / spacers, screws in the parts they thread into, belts
meshing with their pulleys, pulleys on motor shafts, motor faces on the tower faces, servos in their frames
and horns on splines, the gear fingers in mesh, the yaw switch roller under the cam, keep-outs on their parts.

Views looked at (views/*.png, home pose): iso, front, side, top. Checked: the pleuel runs parallel to the
lower shank behind it; both 140T pulleys sit inside the towers with the belts going back to the motor
pulleys; the deck clears the pulleys; the gripper hangs on the wrist with the fingers near the arm plane
(y about 1 mm); Uno + shield and the buck sit on the base under the turret's sweep; nothing floats.
Not checked in CAD: cable routing (route the arm motor cables with slack through the back; yaw +-150 deg),
assembly order (towers are one print: put the lower shank, spacers and lever pulley between them, then
slide the M4 x 70 through).

## Print check (python -m mechy.design_tools printcheck), accepted warnings
- All parts fit the 256 mm bed as modelled (xyz). No small holes, no floating bodies.
- GT2 tooth tips (~0.8 mm) and gear tooth tips are below the 1.2 mm wall rule: inherent to the profiles; print at 0.2 mm layers, 0.4 nozzle.
- Overhang areas are bridges of 1-4 mm at the bearing-pocket steps and nut traps, 45 deg cone flanges on the pulleys, the 45 deg conical roof of the base boss cavity, the 5 mm wire-exit roof in the base and the teardrop roofs of the horizontal tower holes. None needs support.
- lever_pulley: "Ø8 insert pocket" warning is the M4 head counterbore of the crank pin, not an insert.
- race_washer: 1.0 mm thick part (flagged thin by design; 5 layers).
- fit_coupon: thin walls are the 0.6 mm debossed size labels; the test features themselves have >= 2 mm walls.
- Turret: the tower holes (axle, motor pilot slots, M3 slots and counterbores) are horizontal and teardropped.
- PLA touches the stepper faces on the towers and the yaw plate: keep driver current at 1.0 A / 0.7 A and check the motor case temperature after 10 min, or print the turret and yaw plate in PETG.

## Homing
Yaw: KW12-3 roller switch in the base boss, half-moon cam under the yaw pulley; the edge is yaw 0 and
HOME finds it from either side. Shoulder and elbow: no switches (a lever switch has too little travel in the
1 mm pulley-to-tower gap). Put the arm in the rest pose by hand with the motors off (lower shank vertical,
upper shank level) and send HOME. Steppers with 41 % torque use should not skip at the default speeds.

## Design language
Soft desktop instrument: ivory structure (turret, shanks, base), orange moving drive parts (pulleys,
fingers), black servos; one M3/M4 hex drive; tapered links (hull of the hub and end circles). style.py
holds the palette; fits come first.

## Not verified
Holding torque of the XY42STH40-1204A (0.26 N·m used), every MG996R mounting dimension except the
envelope, horn screw circle (7 mm est), XL4015 hole positions, KW12-3 roller height, printed bearing
press fit (coupon), GT2 printed tooth profile with the real belt (print the lever pulley first and try a
belt), masses (weigh the parts), tipping without clamps.
