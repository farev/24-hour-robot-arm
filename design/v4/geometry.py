"""v4 master geometry = v3 (serial arm: stepper elbow, HEM stepper wrist) + a parallel-jaw gripper
(gear cranks + idler links forming a parallelogram per jaw, so the jaws translate without rotating).

World frame (mm): z = 0 on the table, yaw axis through x = y = 0, +x = reach direction at yaw 0, y across.
Angles: th1 = lower shank pitch (absolute), th2 = upper shank pitch (absolute), wr = gripper axis pitch
(absolute, -90 = pointing down). Motors drive RELATIVE angles: elbow motor q2 = th2 - th1 (it rides on the
lower shank), wrist motor q3 = wr - th2 (it rides on the upper shank).
"""
import math

# --- kinematics -----------------------------------------------------------------------------
L1 = 150.0
L2 = 150.0
S_X, S_Z = 10.0, 116.0                 # same base/turret height as v2
TOOL = 89.0                            # wrist axis -> jaw pad centre along the gripper axis (closed):
                                       # servo spline 38 + crank 25.6 + pad centre 25
TH1_LIM = (20.0, 140.0)
Q2_LIM = (-135.0, 100.0)               # elbow relative angle th2 - th1; past +100 at th1 140 the wrist motor
                                       # meets the shoulder motor, folded past -135 the gripper meets the lower
                                       # shank (design review 2026-11-05-design-2, poses/*q2max)
Q3_LIM = (-95.0, 95.0)                 # wrist relative angle wr - th2: past ~100 the gripper linkage (world
                                       # y 0.8..18) swings into the upper shank and wrist motor (poses/wrist-limit-*)
# reach rule (firmware clearOk): wrist point W >= 45 above the table everywhere, >= 95 within 200 of the yaw
# axis (turret, base, Uno, yaw motor), fingertip >= 3 above the table (poses/fold-low, reach-low)
W_Z_MIN, W_Z_NEAR, NEAR_R, TIP_Z_MIN = 45.0, 95.0, 200.0, 3.0
DECK_SCREW_ANG = (30, 150, 210, 330)   # yaw pulley -> deck M3 screws at r 32: |y| 16, clear of the towers
                                       # (at 45 deg the +y nut traps sat 0.5 mm under the right tower)
HOME = {"yaw": 0.0, "th1": 90.0, "th2": 0.0, "wr": -90.0}

# --- drive ----------------------------------------------------------------------------------
MOTOR_T = 20
SH_T1, SH_T2, SH_T3 = 72, 36, 140      # shoulder: 20T -> 72T | 36T -> 140T = 14.0:1 (36T root r 10.7 leaves a
                                       # 3.9 mm wall around the F624 pocket; a 30T would leave 2.2)
ELBOW_T = 140                          # elbow 7:1
WRIST_T = 60                           # wrist 3:1
YAW_T = 120                            # yaw 6:1
BELT_LONG, BELT_SHORT = 320.0, 200.0   # GT2-6 closed loops: 320 (yaw, shoulder stage 2, elbow), 200 (shoulder 1, wrist)
BELT_W = 6.0


def pd(teeth):
    return teeth * 2.0 / math.pi


def centre_distance(t_small, t_big, loop):
    d, D = pd(t_small), pd(t_big)
    b = loop - math.pi * (D + d) / 2
    return (b + math.sqrt(b * b - 2 * (D - d) ** 2)) / 4


def polar(p, r, ang):
    return (p[0] + r * math.cos(math.radians(ang)), p[1] + r * math.sin(math.radians(ang)))


C_SH2 = centre_distance(SH_T2, SH_T3, BELT_LONG)      # S -> intermediate I
C_SH1 = centre_distance(MOTOR_T, SH_T1, BELT_SHORT)   # I -> shoulder motor
C_EL = centre_distance(MOTOR_T, ELBOW_T, BELT_LONG)   # elbow motor -> E (on the lower shank)
C_WR = centre_distance(MOTOR_T, WRIST_T, BELT_SHORT)  # wrist motor -> W (on the upper shank)
C_YAW = centre_distance(MOTOR_T, YAW_T, BELT_LONG)
I_DIR, M_DIR = 200.0, 160.0                            # S -> I and I -> shoulder motor directions (deg)
S = (S_X, S_Z)
I_PT = polar(S, C_SH2, I_DIR)
SH_MOTOR = polar(I_PT, C_SH1, M_DIR)
TENSION_SLOT = 3.0                                     # motor slots +-3 along their belt
I_SLOT = 2.5                                           # intermediate axle slot +-2.5 along S -> I (stage-2 tension)
PILOT_H = 2.0
HUB_REACH = PILOT_H + 11.5                             # motor face -> belt centre with hub gap g: + g

# --- y layout -------------------------------------------------------------------------------
Y = {
    "tower_l": (-36.0, -27.0),
    "pulley_l": (-26.0, -18.0),       # shoulder 140T teeth (lower shank print); 30T of the compound pulley
    "lower": (-18.0, -8.0),           # lower shank plate; elbow motor face on its -y face (-18)
    "upper_teeth": (-7.0, 0.0),       # upper shank E 140T teeth + cone flange; wrist pulley plane
    "upper": (0.0, 10.0),             # upper shank beam; wrist motor face on its +y face (10)
    "tower_r": (25.0, 34.0),          # shoulder motor face on its +y face (34)
    "wrist_pulley": (-17.0, -1.7),    # wrist pulley + bearing hub (teeth on the -1.7 side; flange ring -1.7..-0.5)
    "grip_plate": (-22.0, -17.0),
}
BELT_SH2 = Y["lower"][1] - 13.25                             # -21.25: lower shank teeth z 10..16.5 above its -8 bed
BELT_SH1 = Y["tower_r"][1] - (HUB_REACH + 0.5)              # 20.0
BELT_EL = (Y["upper_teeth"][0] + Y["upper_teeth"][1]) / 2 + 0.4   # -3.1 (teeth 0..-6.2, cone -6.2..-7)
EL_HUB_GAP = BELT_EL - (Y["lower"][0] + HUB_REACH)          # 1.4: elbow motor pulley hub gap
BELT_WR = -4.8                                               # wrist pulley teeth -1.7..-7.9 (was -4.1: moved
                                                             # 0.7 so a glued flange ring fits on the +y side)
WR_HUB_GAP = (Y["upper"][1] - HUB_REACH) - BELT_WR           # 1.3
WRIST_FLANGE = (16.0, 44.0, 1.2)                             # ring ID, OD, thickness: y -1.7..-0.5, 0.5 to the shank
WRIST_SCREW_R = 14.0                                         # gripper base -> wrist pulley M3 pilots (2.8 mm to the
                                                             # tooth grooves; was 15 -> 1.8)
DECK_SCREW_R = 31.8                                          # yaw pulley -> deck M3 circle (CB 2.1 mm from the 120T
                                                             # grooves; was 32 -> 1.94)

# --- base / yaw (as v2, but the yaw motor is a 40 mm XY42 standing in a floor cut-out) --------
FLOOR = 4.0
YAW_MOTOR_FACE_Z = 40.0                 # body 40 on the table through the cut-out
YAW_PLATE_T = 3.0                       # plate 40..43 -> belt plane stays at 55
YAW_BELT_Z = YAW_MOTOR_FACE_Z + YAW_PLATE_T + 0.5 + 11.5
AXK_Z0, AXK_H = 46.5, 4.0
YAW_PULLEY_Z = (AXK_Z0 + AXK_H, 62.5)
DECK_Z = (62.5, 67.5)

# --- gripper (frame at W: +g along the gripper, +h across) -----------------------------------
GRIP_SERVO_G = 38.0                    # v4: servo turned so its body points AWAY from W (toward the jaws); its near
                                       # tab end is then 21.5 mm from W, clear of the wrist pulley (r 21)
GRIP_SERVO_BODY_FWD = True
GEAR_M, GEAR_T = 1.5, 16
GRIP_SERVO_TOP_Y = Y["grip_plate"][1] + 7.5 + 2.5       # -7.0: the tab's UNDERSIDE (7.5 + 2.5 tab below the top
                                                          # face) rests on the plate; spline points +y (user redline:
                                                          # with + 7.5 only the tabs sat 2.5 mm inside the plate)
GRIP_HORN_Y = (GRIP_SERVO_TOP_Y + 2.3, GRIP_SERVO_TOP_Y + 2.3 + 5.5)   # -7.2 .. -1.7
FINGER_Y0 = GRIP_HORN_Y[1]                               # crank gear A bed face on the horn (-1.7)
# parallel-jaw gripper (gripper frame: g from W along the gripper, h across; gear A at h = -12, B at +12)
CRANK_L = 26.0                       # gear centre -> jaw pin J1
IDLER_D = 20.0                       # gear centre -> idler base pivot (= J1 -> J2 on the jaw); 19 left 0.35 mm
                                     # between the idler and the gear teeth when closed
IDLER_DIR = -95.0                    # its direction in the (g, h) plane for jaw A (outward; B mirrored): stays >= 45 deg
                                     # from the crank (closed +10 .. open -50), so the parallelogram never goes flat
CRANK_CLOSED, CRANK_OPEN = -10.0, 50.0   # crank angle from +g, positive = outward (deg): jaws closed / open (~51 mm)
LINK_T = 5.4                         # crank B and idler links: y -1.1 .. 4.3; crank A is 6.0 thick from the horn (-1.7)
LINK_Y = (FINGER_Y0 + 0.6, FINGER_Y0 + 0.6 + LINK_T)
PIN_BOSS_TOP = LINK_Y[1] + 4.7       # bosses on the crank / idler ends carry the jaws above the idler-pivot nuts
JAW_Y = (PIN_BOSS_TOP + 0.5, PIN_BOSS_TOP + 0.5 + 6.0)   # 9.5 .. 15.5
J1_H_CLOSED = GEAR_M * GEAR_T / 2 - CRANK_L * math.sin(math.radians(-CRANK_CLOSED))   # 7.49: pin line from the centre line
PAD = (14.0, 36.0)                   # jaw pad along the jaw from J1 (local x)
PAD_FACE = J1_H_CLOSED - 1.0         # pad face this far inward of the pin line: closed pads 2 mm apart

if __name__ == "__main__":
    print(f"C_SH2 {C_SH2:.2f} C_SH1 {C_SH1:.2f} C_EL {C_EL:.2f} C_WR {C_WR:.2f} C_YAW {C_YAW:.2f}")
    print(f"I {I_PT[0]:.1f},{I_PT[1]:.1f}  shoulder motor {SH_MOTOR[0]:.1f},{SH_MOTOR[1]:.1f}")
    print(f"belt y: sh2 {BELT_SH2} sh1 {BELT_SH1} el {BELT_EL} (hub gap {EL_HUB_GAP:.2f}) wr {BELT_WR} (gap {WR_HUB_GAP:.2f})")
