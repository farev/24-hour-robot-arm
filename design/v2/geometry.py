"""v2 master geometry: every printed part and the assembly read their numbers from here.

World frame (mm): z = 0 on the table, yaw axis through x = y = 0, +x = reach direction at yaw 0,
y across the arm. Arm angles are absolute pitches from +x in the arm plane (degrees):
  th1 = lower shank pitch (shoulder motor, 140T pulley on the lower shank)
  th2 = upper shank pitch (elbow motor, 140T lever pulley + pleuel parallelogram)
  wr  = gripper axis direction in the arm plane (wrist servo), -90 = pointing straight down
[est] = design estimate, [model] = parts/models/*.yaml.
"""
import math

# --- kinematics -----------------------------------------------------------------------------
L1 = 150.0            # S -> E, lower shank between pivots
L2 = 150.0            # E -> W, upper shank between pivots
LEVER = 35.0          # S -> L on the lever pulley = E -> PU on the upper shank rear arm (parallelogram);
                      # 35 keeps the L bolt counterbore (r 39) inside the 140T tooth root (r 43.8)
S_X, S_Z = 10.0, 116.0   # shoulder axis: pulley rim (r 46) clears the deck top (67.5) by 2.5
TOOL_DOWN = 105.0     # wrist axis -> fingertip centre along the gripper axis (gripper geometry below)
TOOL_FWD = TOOL_DOWN
TH1_LIM = (20.0, 140.0)        # lower shank pitch limits
INTERIOR_LIM = (40.0, 150.0)   # elbow interior angle (keeps the pleuel parallelogram off its dead points)
TH2_LIM = (-80.0, 60.0)        # upper shank pitch limits
HOME = {"th1": 90.0, "th2": 0.0, "wr": -90.0, "yaw": 0.0}   # assembly pose: lower shank up, upper level, gripper down

# --- drive ----------------------------------------------------------------------------------
GT2_PITCH = 2.0
MOTOR_T = 20          # GT2 20T aluminium, 5 mm bore [model gt2-20t-pulley]
ARM_T = 140           # printed output pulleys, shoulder and elbow: 7:1
YAW_T = 120           # printed yaw ring pulley: 6:1
BELT_LOOP = 320.0     # GT2-6 closed loop, all three joints (Amazon 2-packs)
BELT_W = 6.0


def pd(teeth):
    """GT2 pitch diameter."""
    return teeth * GT2_PITCH / math.pi


def centre_distance(t_small, t_big, loop=BELT_LOOP):
    """Open-belt centre distance for a closed loop of length `loop`."""
    d, D = pd(t_small), pd(t_big)
    b = loop - math.pi * (D + d) / 2
    return (b + math.sqrt(b * b - 2 * (D - d) ** 2)) / 4


C_ARM = centre_distance(MOTOR_T, ARM_T)      # ~69.5
C_YAW = centre_distance(MOTOR_T, YAW_T)      # ~84.0
ARM_MOTOR_DIR = 195.0                         # direction S -> arm motor axis, deg from +x
TENSION_SLOT = 3.0                            # +- slot travel of every motor along its belt
ARM_MOTOR = (S_X + C_ARM * math.cos(math.radians(ARM_MOTOR_DIR)),
             S_Z + C_ARM * math.sin(math.radians(ARM_MOTOR_DIR)))
PULLEY_HUB_GAP = 0.5        # motor pulley hub end above the pilot boss top
PILOT_H = 2.0               # [model] NEMA 17 pilot height
BELT_FROM_FACE = PILOT_H + PULLEY_HUB_GAP + 11.5   # motor face -> belt centre (hub toward motor) [model]

# --- y layout (across the arm), mm ----------------------------------------------------------
Y = {
    "tower_l": (-35.0, -26.0),      # left tower plate (shoulder motor face on its -y face)
    "pulley_l": (-25.0, -17.0),     # 140T teeth zone of the lower shank
    "lower": (-17.0, -7.0),         # lower shank plate (+ disc r 46 at S)
    "upper": (-6.0, 4.0),           # upper shank (10 thick: two F624 back to back at E); servo tabs on +4 face
    "pleuel": (5.0, 13.0),          # push rod
    "lever": (14.0, 24.0),          # 140T lever pulley (10 thick: two F624 back to back), flat face to the pleuel
    "tower_r": (25.0, 34.0),        # right tower plate (elbow motor face on its +y face)
}
BELT_Y_L = Y["tower_l"][0] + BELT_FROM_FACE    # -21.0
BELT_Y_R = Y["tower_r"][1] - BELT_FROM_FACE    # +20.0

# --- base / yaw stack, z (mm) ---------------------------------------------------------------
FLOOR = 4.0
YAW_MOTOR_FACE_Z = 38.0                   # HEM 34 mm body standing on the floor (4 + 34) [model]
YAW_PLATE_T = 5.0                         # motor plate above the face (z 38..43)
YAW_BELT_Z = YAW_MOTOR_FACE_Z + YAW_PLATE_T + PULLEY_HUB_GAP + 11.5   # 55.0
AXK_Z0 = 46.5                             # AXK2035 stack bottom (lower washer in the boss pocket)
AXK_H = 4.0                               # [model]
YAW_PULLEY_Z = (AXK_Z0 + AXK_H, 62.5)     # yaw ring pulley: hub face on the upper washer .. top (hub above
                                          # the teeth lifts the deck 3 mm over the yaw motor pulley top, z 59.5)
DECK_Z = (62.5, 67.5)                     # turret deck (and the tower feet strips)
DECK_R = 70.0                             # round part of the deck; tower strips reach back to x = -88

# --- wrist and gripper (gripper frame: origin at W, +g along the gripper axis, +h across) ------
WRIST_SERVO_TAB_Y = Y["upper"][1]         # wrist servo tabs on the upper shank +y face (4)
WRIST_HORN_TOP_Y = WRIST_SERVO_TAB_Y + 7.5 + 2.3 + 5.5   # tab->top 7.5, boss 2.3, horn 5.5 [model mg996r] = 19.3
GRIP_PLATE_Y = (WRIST_HORN_TOP_Y, WRIST_HORN_TOP_Y + 5.0)  # gripper base plate on the wrist horn
GRIP_SERVO_G = 50.0                       # gripper servo spline axis along g, at h = -12
GEAR_M, GEAR_T = 1.5, 16                  # finger gears: PD 24, centres 24 apart (h = -12 / +12)
GRIP_HORN_Y = GRIP_PLATE_Y[0] - 7.5 - 2.3 - 5.5          # gripper servo horn face (toward -y) = 4.0
FINGER_Y = (GRIP_HORN_Y - 6.0, GRIP_HORN_Y)              # finger gears plane -2 .. 4

if __name__ == "__main__":
    print(f"C_ARM {C_ARM:.2f}, C_YAW {C_YAW:.2f}, motor {ARM_MOTOR[0]:.1f},{ARM_MOTOR[1]:.1f}, "
          f"belt y {BELT_Y_L} / {BELT_Y_R}, yaw belt z {YAW_BELT_Z}")
