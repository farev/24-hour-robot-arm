# CAD v4: v3 arm + parallel-jaw gripper (from the user's reference picture)

Everything except the gripper is v3 (see ../v3/summary.md). Reference: inspiration/pasted-image-1.png.

| What | Where |
|---|---|
| Assembly | assembly.yaml (jaws half open), assembly.glb, views/*.png |
| Poses | poses/{gripper-closed, gripper-open, reach-table, elbow-up, elbow-folded, stretched, yaw-limit} |
| New printed parts | printed/crank_gear.py (A, B), idler_link.py (x2), jaw.py (A, B), gripper_base.py |
| Firmware | ../../firmware/arm_v4 (as v3, tool 104 mm, gripper servo range 1250-1920 us est) |
| Torque check | ../../sim/v4_check.py |

## Gripper mechanism
- MG996R (kept from the cart) turns crank gear A; 16T m1.5 gears mesh 1:1 so B counter-rotates.
- Each 26 mm crank and a 26 mm idler link form a parallelogram with a 20 mm offset (pivot beside each
  gear, pointing outward), so each jaw **translates without rotating**, like the reference. The offset
  points outward (not along the gripper axis) so crank and idler never line up over the -10 to +50 deg
  crank travel: a first try with the offset along the axis went flat mid-travel and the bars collided.
- Jaws: back ear carrying both pins, forward pad with a serrated face (1.6 mm pitch) and triangular truss
  pockets on top. They ride 5 mm above the links on pin bosses so they clear the idler-pivot nuts.
- Travel: pads 2 mm apart closed, about 51 mm open (60 deg of servo).
- Grip force (estimate): about 17 N per jaw with the MG996R at 4.8 V; holds 127 g with a large margin.

## Numbers (computed from the CAD, sim/v4_check.py; estimates)
- Payload inside the 50 % torque budget at the worst pose: **~127 g** (v3: 145 g; the new gripper and
  its pins add about 20 g at the wrist). 300 g holds statically at ~69 % shoulder.
- Table reach with the gripper down: 293 mm.

## Assembly check
8 poses (home half open, closed, open, reach-table, elbow-up, elbow-folded, stretched, yaw +150):
**0 interferences, 0 clearance issues** (screws in clearance holes excluded), BOM links clean.
Fixed on the way: parallelogram offset changed from along the gripper axis to outward (collision when
the bars lined up); idler pivot moved from 19 to 20 mm from the gear (0.35 mm to the gear teeth closed).
Views looked at (iso, front, side): crank gears in the middle, black idler links outside, yellow jaws
below with serrated pads facing each other, the parallelogram visible on each side.

## Turret fix: yaw motor shaft (user redline, 2026-11-05)
The 40 mm yaw motor's shaft tip (z 64) stood 1.5 mm above the deck underside (z 62.5), so the turret's
rear tail hit it whenever it swung over the motor (yaw ~20 deg; none of the pose files had that angle).
Fix: a ring groove on the turret underside along the shaft's path (r 84 +- 6.5, covers the +-3 mm belt
tension travel), 3 mm deep, 2 mm of deck left under the tower foot; its ceiling is a 13 mm bridge on the
bed face (prints without support). New check `sim/yaw_sweep.py`: every turning part against every fixed
part from -150 to +150 deg in 10 deg steps: v4 0 collisions (v3, without the groove, hits at yaw 20).

## Gripper servo fix (user redline, 2026-11-05)
The MG996R tabs were placed with their top face on the gripper base, so the 2.5 mm tabs sat inside the
plate; an allow_contact between servo and plate hid it from the check. Fixed: servo top face 10 mm above
the plate (tab underside on the plate face) and the allow_contact removed, so the check now sees this
interface. Raising the servo put its wrist-side tab into the wrist pulley (61 mm³), so the servo is turned
round: body pointing away from the wrist, spline 38 mm from W (was 53). The gripper is 15 mm shorter
(tool 104 -> 89 mm), payload inside the 50 % budget ~132 g (was ~127 g), table reach 287 mm (was 293:
the wrist has to come lower). All 8 poses: 0 interferences, no clearance reports apart from screws in
their clearance holes and the deliberate 0.2 mm under the pivot nuts. Firmware tool length updated.
The same tab error is in v2 (wrist and gripper servos) and v3 (gripper servo).

## Upper shank disc windows (user redline, 2026-11-05)
The 5 lightening slots in the elbow disc were 60 deg apart but each spanned ~62 deg, so neighbouring slots
left no printable web between them (printcheck missed it: the gaps vanished rather than going thin).
Now 4 slots at 72 deg (13 x 11 mm, r 25.5), narrowest web ~8.5 mm at the slot ends (computed by hand from
the slot geometry). Upper shank +6 g; payload inside the 50 % budget ~128 g. Lower shank windows checked
the same way: ~9.9 mm webs. printcheck on upper_shank: min wall 3.4 mm, no warnings.
Final (user 2026-11-05: five cut-outs, the same on both shanks): both discs have 5 slots 13 x 11 at r 25.5,
evenly 72 deg apart and symmetric about the beam (36, 108, 180, 252, 324 deg); narrowest web ~8.5 mm, and
~4.6 mm from the slots beside the beam to the lower shank's first beam window (design review 2026-11-05). Upper shank 129 cm³, lower
133 cm³; printcheck on both: min wall 3.4 mm, no warnings; home pose 0 interferences, BOM links clean.

## Print check (print release 2026-11-05)
All 20 printed models regenerated from source (design/v4/release_run.py -> printcheck.json). Every part fits
the 256 mm bed in the modelled orientation ("xyz"), no small holes, no floating or non-solid bodies.
Overhangs, located with design/v4/overhang_faces.py; each is accepted for the reason given:
- Bearing pockets (base, lower/upper shank, shoulder compound, wrist pulley): the Ø15.4 -> Ø13.1 flange step
  (1.15 mm ring) and the Ø13.1 -> Ø7.6 / Ø4.8 step (2.75-4.2 mm ring) are short ring overhangs anchored on the
  outer wall; the widest roof is the base's Ø13.1 ceiling at z 13 (13 mm bridge).
- Counterbore floors around M3 slots and the M4 head (lower shank z 6, upper shank z 4.4): 1.5-2 mm rings.
- Lower shank beam window ceiling at z 10: 10 mm bridge. Turret: shaft-groove ceiling 13 mm bridge (see the
  turret fix above), tower slot roofs 8-12 mm flat bridges and teardrop steps <= 6 mm.
- Base switch support (6 x 5 mm) and Uno/buck post step (2.2 x 3.4 mm): short bridges.
- 45 deg cones (shank flanges, compound 72T taper and 36T flange, yaw pulley flange, base cones) are 45 deg.
- Wrist pulley: the blind ends of the 4 Ø2.6 pilots. Gripper base: the 3 pivot head counterbores on the bed
  face (1.65 mm rings around the Ø3.2 holes). Fit coupon: the bed-face bearing pocket ceilings (same rings as
  the parts, which is the point of the test).
Thin walls: race washer (x8) is flagged because the part is a 1.0 mm flat disc (Ø9 x Ø4.3 bore, radial wall
2.35 mm). Printed flat it is 5 solid layers at 0.2 mm, which meets the floor/roof rule (fdm_pla_rules §4,
1.0 mm), but printcheck counts the thickness as a wall. Kept: the 1.0 mm sets the clamp stack of every joint.
Print them with 0.2 mm layers (or 0.1 mm for a flatter washer). If a washer breaks, an M4 DIN 125 washer
(0.8 mm) plus a 0.2 mm shim works.
Fit coupon: 2 mm floor under the pockets, column dimples instead of debossed digits (which left 0.5-0.65 mm
ribs), a Ø5.6 push-out hole, and the bearing pockets now open on the bed face like the parts' pockets.

## Design review fixes (.mechy/reviews/2026-11-05-design.md)
- Gripper pivots (blocking 1): Ø6.5 x 3.3 head counterbores on the gripper base bed face, so the M3 x 30
  reaches 1.9 mm past its nut (was 1.0 mm of a 2.4 mm nut).
- Deck screws: yaw pulley counterbores 5.3 -> 6.3 deep, so the M3 x 10 runs 0.7 mm past the deck nut.
- Motor screws: counterbores 0.5 mm deeper (turret 3.5, shanks 6.5) -> 4.5 mm (1.5 d) into each motor. The
  yaw motor keeps M3 x 6 under the 3 mm plate (3 mm = 6 threads in the motor's aluminium; it only hangs the
  motor and takes belt tension sideways).
- Base: Ø7.6 relief between the two yaw bearings (z 13 to 41.5), so only the outer rings touch PLA; Uno and
  buck pilots run down through the floor (8-9 mm for M3 x 8-10 through a 1.6 mm PCB); the buck moved 6 mm in
  +x so its post no longer hangs over a corner clamp hole (0.33 mm wall otherwise); floor opened from the yaw
  motor cut-out to the base edge under the motor plug, with the yaw motor's plug keep-out added.
- Turret: horizontal M4 axle holes +0.1 (4.3, rules §1 for horizontal holes).
- Crank gears: backlash 0.15 -> 0.35 (FDM teeth print fat); crank A horn holes Ø2.2 -> Ø2.6 (M2 clearance,
  the screw threads into the horn only).
- Jaws: boss-seat recess removed (it was smaller than the Ø7.2 bosses; a larger one left a 1.2 mm ear wall).
- Print list: fit coupon row added (re-add it if print_list.csv is regenerated).
Not changed, with the reason: race washers stay PLA (1.0 mm sets every joint's stack; steel DIN 125 is
0.8 mm); allow_contact pairs measured clean by the reviewer, pruning left for a later pass; idler link and jaw
colours, -a/-b names and the shank disc windows (finger-trap band) are cosmetic or by the user's choice.

## Design re-review fixes (.mechy/reviews/2026-11-05-design-2.md)
- Joint limits (blocking 1-2): Q3 +-150 -> +-95 (past ~100 the gripper linkage swings into the upper shank and
  wrist motor), Q2 max 150 -> 100, and a reach rule in geometry.py and firmware/arm_v4 (`clearOk`): wrist point
  >= 45 mm above the table everywhere and >= 95 mm within 200 mm of the yaw axis, fingertip >= 3 mm. `J` and `P`
  also check 16 points along the joint-space path (`ERR PATH`). 8 limit poses added (wrist-limit-pos/neg,
  reach-wrist-pos/neg, elbow-back-q2max, elbow-up-q2max, fold-low, reach-low); firmware builds for the Uno
  (26 % RAM, 44 % flash).
- Deck screws moved from 45/135/225/315 deg to 30/150/210/330 deg (geometry.DECK_SCREW_ANG): the +y nut traps
  sat 0.5 mm under the right tower.
- I-axle nut slot: across flats + 0.35 (was as wide as the corners, so the nut could spin).
- Shoulder compound: flange cone under the 36T now 45 deg (was 1.0 mm tall, 60 deg).
- Turret slot roofs (motor pilot and screw slots, I-axle slot): measured as flat roofs (overhang_faces.py), the
  widest 8-12 mm across the slot, open at both tower faces; printed as bridges.

## Assembly check (print release 2026-11-05, after the fixes)
Home pose and all 15 other poses: 0 interferences. 7 clearance notes in every pose are intended fits, not
collisions: 4 M3 deck screws in Ø3.6 clearance holes 0.35 mm; the gear-B and idler pivot nuts set 0.2 mm
above gear B / the idler links (left just loose with thread glue so the parts turn). yaw-limit also reports two
"unverified contacts": the J2 nut faces rest on the idler link faces (reviewer measured 0.001 mm³, distance 0).
Views re-rendered (views/*.png) and looked at: no floating or crossing parts; yaw plug keep-out runs out
through the new floor opening.

## Gripper motion check (user redline 2026-11-06: "components collide on the rigged sim")
The rig (joints.yaml, written by the rigging agent) predates the servo flip that moved the gripper 15 mm along the
gripper axis: its crank/idler/jaw origins sit at z 213 while the parts are at z 228, so the sim swings them about
the wrong points (`rig-check v4`: gripper parts 7.8-29 mm off the snapshots; 8 newer poses unrigged). The CAD
itself, swept closed -> open in 7 steps with every gripper whole-part allow_contact removed (sim/grip_sweep.py ->
sim/grip_sweep.json): 0 overlaps apart from the horn on its spline; gear flank gap 0.20-0.28 mm, links/jaws/base
0.5 mm apart as designed. Fix: Re-rig v4 from Simulate.

## Pre-print fixes (.mechy/reviews/2026-11-06-design.md; user: fix them, keep PLA, re-slice)
- Turret slot roofs: every inclined slot (motor pilot, motor M3 slots and counterbores, I-axle slot, counterbore
  and nut slot) now has a 45 deg gable roof over the whole slot instead of per-end teardrops; the old roofs were
  70 deg sloped overhangs (summary entry above was wrong). Turret overhang area 522 -> 162 mm2 (the rest is the
  13 mm shaft-groove bridge and short counterbore rings); it slices on the X1E preset.
- Wrist belt flange: the +y side of the 60T had no flange. A printed-in flange would overhang, so the wrist belt
  plane moved 0.7 mm (BELT_WR -4.1 -> -4.8, the motor pulley slides 0.7 further out on its shaft: hub gap 1.3),
  the pulley is 0.7 shorter (spacer_w 5.3, wrist washer 1.7) and a separate ring (Ø44 x Ø16 x 1.2,
  wrist_flange) is glued on the pulley's top face, 0.5 mm from the upper shank.
- Thin walls: gripper-base -> wrist-pulley screw circle r 15 -> 14 (pilot to tooth groove 1.8 -> 2.9 mm); yaw
  pulley -> deck screw circle r 32 -> 31.8 (counterbore to groove 1.94 -> 2.14 mm).
- Yaw motor screws: 1 mm head counterbores in the yaw motor plate, so the M3 x 6 reaches 4 mm into the motor.
- Cable route: the Uno sits on 3 mm posts (PCB z 7, stack top 52); the Uno keep-out now includes the plugs, cable
  bends and bundle 2 mm over the stack (z 54) and the bundle leaving toward -x. The turret deck underside is at
  z 62.5, so 8.5 mm stays clear (checked with sim/yaw_sweep.py over -150..150). The cables are tied to a zip-tie
  block on the base's -x edge (x -121.5, y 56; r 134, outside the turret's 127 sweep) and leave the base as a free
  service loop of ~0.5 m that rises outside r ~150 (clear of the shoulder motor's 144 sweep) to a tie on the
  shoulder motor's screw slots / the left tower. The loop is flexible and not modelled: before powering, turn the
  yaw by hand through -150..150 with the cables fitted and check nothing snags.

## Print files (2026-11-06)
Sliced for a Bambu Lab X1E with the Bambu Studio CLI (design/v4/gcode/README.md). Bambu Studio's own arrange
needed 3 plates for the arm. design/v4/pack_plates.py nests the real outlines (24 angles, 5 mm spacing, X1E
exclusion area kept clear) onto 2 plates: plate 1 is the base + all small parts (8 h 28 m, 250 g after the
pre-print fixes), plate 2 is the turret + both shanks (9 h 06 m, 267 g). G-code extents match the layout and no plate is outside the bed.
Also sliced: the coupon (58 m, 27 g, print first) and the gripper plate (1 h 41 m, 40 g, held for the servo
measurement).

Re-slice 2026-11-06 (user: parts sat on the calibration lines and too close to the edges):
- The first files used only the generic start G-code from the preset's `inherits` chain. That was home, level and
  one purge line, with no flow calibration, nozzle wipe or AMS load. Bambu's X1E template G-code is now merged in.
- The real start G-code draws at x 18-240, y 1-12. Parts now stay 8 mm behind it (y >= 20, which allows for the
  2 mm Bambu Studio shifts loaded plates toward the front) and 10 mm from the other edges.
- Brim and skirt are off, so the toolpaths stay inside the packed outlines.
- The tighter bed area (236 x 224 mm) needs 3 arm plates: base + small parts 7 h 16 m / 220 g; both shanks + yaw
  pulley 6 h 56 m / 186 g; turret 3 h 32 m / 112 g. The coupon is 1 h 05 m and the gripper (hold) 1 h 47 m.
- design/v4/verify_plates.py: ALL OK.

## Gripper parts wait for the servo (design review blocking 2)
The horn top is modelled 7.8 mm above the case top (44.4 mm over the case bottom); the TowerPro drawing gives
47.6 overall with the horn, i.e. 11.0 mm. Crank A sits on the horn, so the gear mesh and jaw A depend on it.
Do not print gripper_base, crank gears, idler links or jaws until the servo is measured: horn top above the
case top, horn screw circle, tab hole spacing and the case-top-to-tab distance. Then set the horn height in
parts/models/mg996r-servo.yaml and regenerate.

## Hardware for the gripper
M3 x 20 x4 (jaw pins, nut under each crank/idler end, set just loose with thread glue), M3 x 30 x3 (gear B
pivot, two idler pivots, nuts on top), M3 nuts x7, M3 x 16 x4 (gripper base to the wrist pulley),
from your M3/M4 stock. Servo: 4 x M3 x 10 self-tapping into the Ø2.6 tab pilots (your stock); crank gear A
to the horn with the servo's own horn screws (Ø2.6 clearance holes; M2 x 6-8 self-tapping if the box has none).

## Not verified
MG996R horn height, horn screw circle (7 mm est) and tab holes (measure before printing the gripper); printed
gear backlash 0.35 mm (print the two crank gears first and check they mesh freely); grip force is a
calculation; motor case temperature against PLA (see assumptions/motor-mount-material.yaml).
