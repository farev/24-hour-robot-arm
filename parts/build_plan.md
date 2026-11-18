# Build plan: 24-hour robot arm (v4)

Concept: Mechy-designed serial arm, 150 + 150 mm links, a stepper at every joint (yaw, shoulder, elbow, wrist),
GT2 belts with printed pulleys, parallel-jaw gripper driven by one MG996R, base flat on the table.
Targets: 300 g payload, ~30 cm reach, table pick-up, structure printed, buy on Amazon US / Invention Studio,
budget < $100. Computed (sim/v4_check.py, estimates): 287 mm table reach; inside the 50 % torque budget 48 g
at 1.0 A drive current or 129 g at 1.2 A with a fan; 300 g uses 81 % / 67 % of shoulder holding torque.
v2 (parallel linkage) and v3 are kept in design/ for reference.

| Function | Status | Part or target |
|---|---|---|
| Base yaw motor | owned | XY42STH40-1204A, 20T -> printed 120T (6:1), Z socket |
| Shoulder motor | owned | XY42STH40-1204A, two-stage 20T -> 72T / 36T -> 140T (14:1), Y socket, 1/8 step |
| Elbow motor | owned | XY42STH40-1204A on the lower shank, 20T -> 140T (7:1), X socket |
| Wrist motor | owned | HEM-17D2008-10 on the upper shank, 20T -> 60T (3:1), A socket |
| Gripper actuator | selected | MG996R (2-pack, 1 spare) + printed geared cranks, idler links, parallel jaws |
| Controller + drivers | owned | Uno R3 + CNC Shield V3, A4988 x4 (+1 spare); X/Y/Z/A used |
| Driver cooling | owned | heatsinks; 1.0 A (XY42) / 0.7 A (HEM); a fan only if running 1.2 A |
| Motor power | owned | 24 V 6 A supply |
| Power switch / e-stop | open | inline 5.5 x 2.1 DC switch is a candidate (current rating not listed); unplugging the supply is the fallback |
| Fuse | not bought | the brick supply is current-limited; add a 5 A inline fuse later if wanted |
| Servo supply | selected | XL4015 5 A buck set to 6.0 V with a meter (never the Uno 5 V pin) |
| Reduction | selected belts + pulleys, print pulleys | GT2 20T 5 mm (5-pack + 1 owned, 4 used); GT2-6 320 mm x3 (2 x 2-packs); GT2-6 200 mm x2 (10-pack) |
| Base thrust bearing | owned | AXK2035 + 2 AS2035 under the turret |
| Joint bearings | selected | F624ZZ x10 (10-pack, no spare) |
| Axles | selected | M4x70 (shoulder S and intermediate I), M4x60 (yaw) |
| Screws and nuts | owned | your M3/M4 socket heads 6-30 mm and nuts |
| Homing | selected | KW12-3 roller switch (yaw); shoulder/elbow/wrist from the rest pose |
| Motor cables | owned | 4 cables >= 0.6 m |
| Servo lead | owned | 30 cm servo lead extended with your jumpers (path ~73 cm) |
| Signal and low-voltage wiring | owned | jumpers for the switch and servo signal; 22 AWG+ hookup wire for 24 V and 6 V power |
| Programming cable | owned (assumed) | USB-B |
| Base fixing | print + clamp | corner holes / two C-clamps: needed at full reach (not in the parts list) |
| Printed parts | print | design/v4/print_list.csv (~497 g PLA) + fit coupon first |
| Tools | owned | hex keys 2.5 / 3 mm, multimeter (Vref, buck output); also a small screwdriver and a soldering iron or crimp for the switch leads |
