# Decisions

## 2026-11-04 Starting point
- Prior art (research/prior-art/summary.md): closest build is the 20sffactory Community Robot Arm (Dobot-style
  parallel linkage, NEMA 17 + GT2 4.5:1, Uno + CNC Shield V3 + A4988, MG90S gripper) — the same electronics as owned.
- v1 = that arm built from the vendored STLs (design/v1). Computed with the Mechy arm model (sim/torque_check.py):
  300 g → shoulder 48 % / elbow 40 % of holding x ratio (0.26 N·m conservative motor figure); tool reach 26.8 cm at
  3 cm above its socket plane, 31 cm at 8 cm.
- Found in the v1 assembly: the yaw motor hangs 38 mm below the socket, so on a flat table v1 needs a riser and then
  cannot reach the table plane (24 cm only at 6 cm height). This conflicts with "pick up from a table".
- Proposed v2: own geometry with the same linkage, ~160 mm shanks, yaw motor beside the turntable so the base sits
  flat, owned AXK2035 under the turntable, two-stage GT2 reduction on shoulder and elbow. Waiting for the user's pick.
- Licence: 20sffactory repo LICENSE is GPL-3.0, README says CAD CC BY 4.0, derived from Tobler's CC BY-NC → use for a
  personal/student build with attribution; Mechy firmware written from scratch.
- Motors: 34 mm HEM on base yaw, XY42STH40 on shoulder + elbow, 3rd XY42STH40 spare (assumption logged).

## 2026-11-04 User answers -> v2
- User picked v2 (Mechy-designed), budget < $100, designs own parts, owns a 24 V 6 A supply.
- v2 choices: 150 + 150 mm links; single-stage GT2 20T -> printed 140T (7:1) on shoulder/elbow (prior art's
  two-stage belt avoided: one stage with a big printed pulley gives 41 % torque use and lower belt tension);
  yaw 20T -> 120T (6:1); all three belts one stock length (320 mm, Amazon 2-packs; 300 mm was too short for
  140T wrap, 350 mm only sold singly).
- Wrist MG996R instead of the passive levelling links: fewer parts, and the gripper can tilt; gripper MG996R
  with 1:1 gear fingers (grip ~8 N per finger est vs 2.9 N for 300 g).
- All joints on F624ZZ with M4 bolts as axles (one bearing type, one 20-pack); printed race washers/spacers.
- Shoulder/elbow homing switches dropped (1 mm pulley-to-tower gap is too little lever travel): rest-pose
  zeroing; yaw keeps a KW12-3 switch with a half-moon cam.
- Firmware written from scratch (firmware/arm_v2), 20sffactory's GPL firmware used only as a reference.

## 2026-11-05 v3: stepper elbow + stepper wrist (user redlines on v2)
- User wants more elbow range than the parallelogram allows: elbow stepper instead of the linkage, and the
  34 mm HEM stepper at the wrist. Asked where the motors go; user chose "motors right at the elbow and
  wrist" knowing the estimate (payload drops to ~150 g or reach to ~22 cm).
- v3 = serial arm: elbow XY42 on the lower shank near E (20T -> 140T on the upper shank, 7:1), wrist HEM on
  the upper shank near W (20T -> 60T, 3:1), shoulder two-stage 20T -> 60T / 30T -> 140T (14:1) on the turret,
  yaw now the third XY42 (base floor cut-out so the 40 mm body stands on the table). Wrist servo dropped,
  socket A drives the wrist, gripper servo moves to A3. v2 stays unchanged.

## 2026-11-05 Prices re-read and the Invention Studio store
- Amazon pages now load with a plain request (research/amazon_prices.py): prices and stock read for every
  pick on 2026-11-05. Six earlier listings were out of stock and are replaced (F624ZZ, MG996R 2-pack, M4x60,
  1 m stepper cables, inline switch) or cheaper now (20T pulleys $4.49).
- Invention Studio store (TouchNet uStores, read via a session request; research/store_raw/store_items.json):
  ~100 items, but for this arm only super glue ($0.30) and an optional caliper ($11). Its belts are 300 mm
  closed (ours 320/200), its bearings are 606 / V-groove (ours F624), its screw kit is M3 only.
- v4 Amazon cart $107.86 before tax and third-party shipping: ~$8 over the $100 budget.

## 2026-11-05 Faster bearings
- The youguxianji F624ZZ listing ($9.78) would arrive Nov 13 to 30. 32 Amazon listings for 4 x 13 x 5 bearings were read
  (research/bearing_options.json). The new pick is the M METERXITY F624ZZ 10-pack (B0F4QXCS6R, $6.49, shipped and sold by
  Amazon, arrives Nov 10). The listing gives the flange as 15 x 1, so the CAD is unchanged. The backup is the uxcell
  F624ZZ (B07Z3DB93B, $8.99).
- Plain 624ZZ bearings fit the 8 hub pockets as they are. The base needs its Ø4.8 centre hole opened to Ø7.6 first;
  this was not changed. The Invention Studio 606-2RS and V-groove bearings would need M6 axles and new pockets, so
  they were not used.

## 2026-11-05 User picks and pre-order review
- The user selected F624ZZ (METERXITY), GT2 320 and 200 belts, 20T pulleys, MG996R, XL4015, KW12-3, M4x70 and M4x60
  ($79.89). The M3/M4 kit, servo extension and glue stay preferred because they were not in the pick.
- Reviewer (.mechy/reviews/2026-11-05-pre-order.md): not ready. Blocking: nothing owned or selected supplies screws,
  nuts or wiring. It also found compatibility.yaml, build_plan.md and bring-up.md still described v2/v3. These were
  rewritten for v4, and belt, fastener, servo-signal and torque checks were added.
- The drivers run at 1.0 A, which gives about 0.217 N·m of holding torque. At that current v4 holds 48 g inside the
  50 % budget (sim/v4_check.py). Asked the user how to handle payload, and which hardware and wiring they own.

## 2026-11-05 Owned hardware, payload decision, print release
- User owns the M3/M4 screws and nuts, the stepper cables, jumpers (used for the servo lead too), a multimeter
  and hex keys. The servo extension is rejected. The cart is 9 Amazon items, $79.89 + $7 seller shipping, about
  $94.6 with tax (est).
- Payload: build as is and test on the bench (requirements.yaml payload_decision).
- Servo power runs over doubled jumpers with the buck at 6.3 V, which covers the ~0.4 V drop (est).
- Pre-order re-review (pre-order-2): its blocking item was the servo horn and tab screws. Tab screws are M3 x 10
  from the user's stock. The horn screws are expected in the servo box (unverified: Amazon blocked the listing
  read), with M2 self-tappers as the fallback.
- Design reviews 1-2 found and fixed:
  - gripper pivot nut engagement;
  - deck and motor screw engagement;
  - base inner-ring rub;
  - yaw plug keep-out;
  - buck/clamp-hole wall;
  - gear backlash;
  - jaw recess;
  - nut-slot spin;
  - deck traps under the tower;
  - joint limits (q3 +-95, q2 <= 100, reach rule in the firmware).
- Gripper parts are held until the MG996R horn height is measured: the drawing says 3.2 mm higher than the model.

## 2026-11-16 Shoulder too weak with the arm stretched (bench test)
- On the bench the shoulder lifted the arm folded but not stretched. Ratio as built: 20T -> 72T (3.6) x 36T -> 140T
  (3.889) = 14:1.
- The sizing used holding torque x ratio (0.26 x 14 = 3.64 N·m) and a 50 % budget. It left out:
  - the 1.0 A drive current (x0.83);
  - two belt stages' losses (~0.81, est);
  - torque lost while moving versus holding (~0.6, est);
  - an unverified 0.26 N·m holding torque for the -1204A.
- With those included, moving capacity is ~1.47 N·m (est). Gravity torque on the shoulder (sim/shoulder_fix.py) is
  1.06-1.42 N·m stretched and 0.5-0.76 N·m folded, which matches what the user saw. The arm's own weight (elbow and
  wrist motors) uses almost all of the shoulder.
- Fix with no reprints:
  - a 16T motor pulley (17.5:1, +25 %): the motor moves 1.67 mm in its slot and the 200 mm belt fits, with 6.3 teeth
    in mesh;
  - shoulder driver at 1.2 A with a fan (+20 %), together about +50 %;
  - firmware SHOULDER_PULLEY_T switch.
- Check the shoulder driver's Vref first.

## 2026-11-16 Missing microstep jumpers
- The yaw was loud because the shield has no microstep caps: all four drivers run full steps, so every move is 16x
  too big (8x on the shoulder) and rough. This may also explain the weak shoulder; retest it once the caps are in.
- The user's photo shows a Protoneer V3.00 clone, turned 180 deg (X bottom-right, Y bottom-left, Z top-right, A top-left).
  The M0/M1/M2 pins sit under each driver at its trimpot end. The A-axis D12/D13 row is bridged with looped Dupont wires,
  which is fine.
- 11 caps needed (X 3, Y 2, Z 3, A 3). The user is using their own jumper wires: the housings are too tall to fit under
  a driver, so they use the bare wire wrapped around the pins (all 6 for 1/16; only M0 and M1 on Y). Caps
  (jumper-caps, B0BRK36G33, $4.97) stay in the BOM as optional. Guide: windows/microstep-jumpers.

## 2026-11-12 Screws bought, M4 x 60 dropped
- There were no screws at the Invention Studio. No single Amazon kit covers the list, so the order is an M3 kit
  (6-30 mm + nuts), an M4 kit (6-30 mm + nuts) and M4 x 70 (30 pcs), all sold by Amazon.
- The M4 x 70 listing replaced the H&H pack, which was showing Nov 30.
- User didn't want a whole pack for one M4 x 60. The yaw axle is now an M4 x 70 on a printed 8 x 10 mm spacer under
  its head (yaw_bolt_spacer, on arm plate 1), with the same tip height.
- Imperial screws don't fit: #8 is too big for the 4 mm bearing bore, and the #6 nut doesn't fit the M4 trap.
- Checks after the change: all 16 poses have 0 interferences, the yaw sweep has 0 collisions, and the plates pass the
  bed-clearance check.
- The cart is $88.38, about $96 with tax (estimate).

## 2026-11-07 Servo dimensions
- The TowerPro datasheet and the Components101 drawing give only the outline (36.6 body, tab underside 10 below the
  top, 47.6 overall with a cross horn, 53.6 over the tabs).
- Neither gives the tab-hole spacing, shaft offset, horn screw circle or round-horn height. Miuzei (the selected
  listing) publishes no drawing.
- User chose to measure the servo when it arrives (about Nov 10, guide in docs/servo-measure.md). The gripper plate
  stays on hold until then.

## 2026-11-06 Print files and pre-print fixes
- Sliced for the Invention Studio's Bambu Lab X1E. Bambu's auto-arrange needed 3 plates for the arm; a custom outline
  packer (design/v4/pack_plates.py) fits the arm onto 2 plates.
- The pre-print review (2026-11-06-design) blocked only the gripper plate, which was already on hold.
- The user chose to fix the 5 arm items, keep PLA and re-slice:
  - turret slot roofs changed to 45 deg gables;
  - a glued wrist belt flange ring (wrist belt plane moved 0.7 mm);
  - two screw circles moved for wall thickness;
  - a yaw motor plate counterbore;
  - cable route: the Uno lowered 2 mm, a plug and bundle keep-out (verified by the yaw sweep), and a base zip-tie block
    outside the sweep, with a hand-checked service loop.
- `python` on PATH lost Mechy's engine environment this session, so scripts run through tools/mpy.py (engine venv).

## 2026-11-05 v4: parallel-jaw gripper (user reference picture)
- User asked for a gripper like inspiration/pasted-image-1.png (gear cranks + idler links, parallel jaws).
  v4 = v3 + that gripper. Kept the MG996R (in the cart, ~17 N per jaw est) instead of the picture's MG90S
  (assumption logged: MG90S would save 42 g at the wrist but grip only ~3-4 N per jaw).
- Parallelogram offset points outward from each gear (20 mm) so the bars never go collinear over the
  crank travel. Payload within the 50 % budget drops from ~145 g (v3) to ~127 g (gripper +20 g).
