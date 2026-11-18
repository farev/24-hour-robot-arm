"""v3 master geometry (serial arm: stepper elbow at the elbow, HEM stepper at the wrist).

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
TOOL = 108.0                           # wrist axis -> fingertip centre along the gripper axis
TH1_LIM = (20.0, 140.0)
Q2_LIM = (-135.0, 150.0)               # elbow relative angle th2 - th1 (v2's linkage allowed -140..-30);
                                       # folded past -135 the gripper meets the lower shank (CAD pose check)
Q3_LIM = (-150.0, 150.0)               # wrist relative angle wr - th2
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
    "wrist_pulley": (-17.0, -1.0),    # wrist pulley + bearing hub (teeth on the -1 side)
    "grip_plate": (-22.0, -17.0),
}
BELT_SH2 = Y["lower"][1] - 13.25                             # -21.25: lower shank teeth z 10..16.5 above its -8 bed
BELT_SH1 = Y["tower_r"][1] - (HUB_REACH + 0.5)              # 20.0
BELT_EL = (Y["upper_teeth"][0] + Y["upper_teeth"][1]) / 2 + 0.4   # -3.1 (teeth 0..-6.2, cone -6.2..-7)
EL_HUB_GAP = BELT_EL - (Y["lower"][0] + HUB_REACH)          # 1.4: elbow motor pulley hub gap
BELT_WR = -4.1                                               # wrist pulley teeth -1.0..-7.2
WR_HUB_GAP = (Y["upper"][1] - HUB_REACH) - BELT_WR           # 0.6

# --- base / yaw (as v2, but the yaw motor is a 40 mm XY42 standing in a floor cut-out) --------
FLOOR = 4.0
YAW_MOTOR_FACE_Z = 40.0                 # body 40 on the table through the cut-out
YAW_PLATE_T = 3.0                       # plate 40..43 -> belt plane stays at 55
YAW_BELT_Z = YAW_MOTOR_FACE_Z + YAW_PLATE_T + 0.5 + 11.5
AXK_Z0, AXK_H = 46.5, 4.0
YAW_PULLEY_Z = (AXK_Z0 + AXK_H, 62.5)
DECK_Z = (62.5, 67.5)

# --- gripper (frame at W: +g along the gripper, +h across) -----------------------------------
GRIP_SERVO_G = 53.0                    # servo body starts 22 mm from W: clears the wrist pulley rim (r 21)
GEAR_M, GEAR_T = 1.5, 16
GRIP_SERVO_TOP_Y = Y["grip_plate"][1] + 7.5             # -9.5: servo spline points +y
GRIP_HORN_Y = (GRIP_SERVO_TOP_Y + 2.3, GRIP_SERVO_TOP_Y + 2.3 + 5.5)   # -7.2 .. -1.7
FINGER_Y0 = GRIP_HORN_Y[1]                               # finger A bed face on the horn

if __name__ == "__main__":
    print(f"C_SH2 {C_SH2:.2f} C_SH1 {C_SH1:.2f} C_EL {C_EL:.2f} C_WR {C_WR:.2f} C_YAW {C_YAW:.2f}")
    print(f"I {I_PT[0]:.1f},{I_PT[1]:.1f}  shoulder motor {SH_MOTOR[0]:.1f},{SH_MOTOR[1]:.1f}")
    print(f"belt y: sh2 {BELT_SH2} sh1 {BELT_SH1} el {BELT_EL} (hub gap {EL_HUB_GAP:.2f}) wr {BELT_WR} (gap {WR_HUB_GAP:.2f})")
