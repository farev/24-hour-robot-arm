# v4 wiring and bring-up

## Wiring (CNC Shield V3 on the Uno)
| What | Where on the shield | Note |
|---|---|---|
| Yaw motor (XY42, base) | Z socket | 1.0 A |
| Shoulder motor (XY42, turret right tower) | Y socket | 1.0 A, **1/8 microstep** |
| Elbow motor (XY42, on the lower shank) | X socket | 1.0 A |
| Wrist motor (HEM 34 mm, on the upper shank) | A socket | 0.7 A; fit the two A-axis jumpers so A step/dir = D12/D13 |
| Microstep jumpers (2.54 mm caps, the shield came without them) | X, Z, A: M0 + M1 + M2 (1/16). Y: M0 + M1 only (1/8). The pins sit under each driver at its trimpot end | firmware MICRO = {16, 8, 16, 16}; photo guide in windows/microstep-jumpers |
| Yaw switch KW12-3 | Z limit header: C -> GND pin, NO -> signal pin (D11) | firmware uses INPUT_PULLUP |
| Gripper servo signal | CoolEn pin (A3) | extend the 30 cm lead with M-F jumpers (power pair doubled, see the buck row) |
| 24 V supply | to the shield's blue power terminal | check polarity: + to + |
| XL4015 buck | input from the 24 V terminal; output set to **6.3 V with a meter before** connecting the servo | servo red/brown to the buck over two jumpers in parallel each; servo ground also to an Uno GND pin |

Never power the servo from the Uno 5 V pin. Route the elbow and wrist motor cables along the shanks with slack
at each joint (about 0.6 m from the shield to the wrist motor, estimate).

## Before power
1. Read the shield's big electrolytic capacitor: it must say 35 V or more for the 24 V supply (if it says 25 V, use a 12 V supply or replace the cap).
2. Read the tiny resistors next to each A4988 chip (R100 or R050) and set Vref with a meter on the trimpot (motor unplugged, 24 V on):
   - R100 (0.1 ohm): Vref = I x 0.8 -> X, Y, Z (1.0 A): **0.80 V**; A (0.7 A): **0.56 V**
   - R050: Vref = I x 0.4 -> 0.40 V and 0.28 V
   - 1.2 A on Y and X (Vref 0.96 V / 0.48 V) gives ~20 % more lifting torque but needs a fan on the drivers.
3. Insert drivers the right way round (EN pin to EN). A reversed A4988 is destroyed.

## Flash and first moves
Flash `firmware/arm_v4` for **Arduino Uno** from the Electronics panel. On boot it prints `READY arm_v4 proto=1`; motors stay disabled.
1. `PING` -> `OK PONG`; `STATUS` (check `yaw_sw` changes when you rotate the turret by hand past straight ahead).
2. With power off, put the arm in the rest pose: lower shank vertical, upper shank level, gripper pointing down, turret roughly straight.
3. Power on, `ENABLE 1`, `HOME` (zeroes the arm at the rest pose, yaw seeks the cam edge at 15 deg/s).
4. `SPEED 10`, then a small joint move (yaw th1 th2 wrist): `J 0 85 0 -90`. If an axis moves the wrong way, `ENABLE 0`, flip its
   `DIR_INVERT` in the sketch, rebuild, reflash.
5. Gripper: `GRIP 100` (open), `GRIP 0` (closed); adjust `GRIP_US_OPEN/CLOSED` so the jaws close without stalling the servo.
6. Cartesian: `P 200 0 60`, then lower toward the table. `ERR LIMIT` / `ERR UNREACHABLE` / `ERR PATH` mean the
   target or the straight joint-space path to it breaks a joint limit (wrist +-95, elbow -135..+100) or the reach
   rule (wrist point >= 45 mm up, >= 95 mm within 200 mm of the base axis, fingertip >= 3 mm): go via a higher pose.
7. Payload test: start with 50 g at 20 cm, then raise it while watching for skipped steps; check motor and driver
   temperatures after 10 minutes. At 1.0 A the estimate is ~50 g inside the 50 % torque budget and ~450 g at full holding torque.
Clamp the base to the table before reaching out with a load.
Nothing self-locks: before cutting power (or ENABLE 0), move it to the rest pose (`J 0 90 0 -90`) or lower it onto the table, or it falls.
