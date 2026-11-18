"""v2 reach and gravity-torque check (computed from design/v2/geometry.py; masses are estimates).

usage: python sim/v2_check.py [payload_kg] [holding_nm]
Parallel linkage: the shoulder motor holds the lower shank's absolute pitch th1, the elbow motor the
upper shank's absolute pitch th2, so each motor only carries its own shank's lever arm:
  tau1 = g cos(th1) L1 (m_lower/2 + m_upper + m_tip + m_pleuel/2)
  tau2 = g cos(th2) (L2 (m_upper_cg_frac m_upper + m_tip) - LEVER m_pleuel/2)
"""
import importlib.util
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("geometry", ROOT / "design/v2/geometry.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

payload = float(sys.argv[1]) if len(sys.argv) > 1 else 0.3
hold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.26
g = 9.81
# masses, kg: printed parts from design/v2/print_list.csv (20 % infill estimate) + bearings/bolts,
# servos from the MG996R datasheet (55 g)
M = {"lower": 0.081 + 0.012, "upper": 0.023 + 0.015, "pleuel": 0.011 + 0.008,
     "wrist_servo": 0.060, "wrist_bracket": 0.009, "grip_servo": 0.060, "gripper": 0.005 + 0.005}
m_tip = payload + M["wrist_servo"] + M["wrist_bracket"] + M["grip_servo"] + M["gripper"]
L1, L2 = G.L1 / 1000, G.L2 / 1000


def ok(th1, th2):
    inter = 180 - (th1 - th2)
    return (G.TH1_LIM[0] <= th1 <= G.TH1_LIM[1] and G.TH2_LIM[0] <= th2 <= G.TH2_LIM[1]
            and G.INTERIOR_LIM[0] <= inter <= G.INTERIOR_LIM[1])


def wrist(th1, th2):
    a, b = math.radians(th1), math.radians(th2)
    return (G.S_X + G.L1 * math.cos(a) + G.L2 * math.cos(b), G.S_Z + G.L1 * math.sin(a) + G.L2 * math.sin(b))


def torques(th1, th2):
    a, b = math.radians(th1), math.radians(th2)
    t1 = g * math.cos(a) * L1 * (M["lower"] / 2 + M["upper"] + m_tip + M["pleuel"] / 2)
    t2 = g * math.cos(b) * (L2 * (0.4 * M["upper"] + m_tip) - G.LEVER / 1000 * M["pleuel"] / 2)
    return abs(t1), abs(t2)


best = {"down": 0.0, "fwd": 0.0}
worst = [0.0, 0.0]
grid = [(t1 / 2, t2 / 2) for t1 in range(2 * int(G.TH1_LIM[0]), 2 * int(G.TH1_LIM[1]) + 1)
        for t2 in range(2 * int(G.TH2_LIM[0]), 2 * int(G.TH2_LIM[1]) + 1)]
for th1, th2 in grid:
    if not ok(th1, th2):
        continue
    wx, wz = wrist(th1, th2)
    t = torques(th1, th2)
    worst = [max(worst[0], t[0]), max(worst[1], t[1])]
    # fingertip centre 15 mm above the table (object picked by its middle) [est]
    if abs((wz - G.TOOL_DOWN) - 15) < 2:
        best["down"] = max(best["down"], wx)
    if abs(wz - 15) < 2:
        best["fwd"] = max(best["fwd"], wx + G.TOOL_FWD)
cap = hold * G.ARM_T / G.MOTOR_T
print(json.dumps({
    "payload_kg": payload, "tip_mass_kg": round(m_tip, 3), "holding_nm": hold,
    "ratio": G.ARM_T / G.MOTOR_T, "capacity_nm": round(cap, 2),
    "table_reach_mm": {"gripper_down": round(best["down"]), "gripper_forward": round(best["fwd"])},
    "worst_gravity_nm": [round(x, 3) for x in worst],
    "worst_frac_of_capacity": [round(x / cap, 3) for x in worst],
    "belt": {"C_arm_mm": round(G.C_ARM, 1), "C_yaw_mm": round(G.C_YAW, 1),
             "small_pulley_tension_at_holding_N": round(hold / (G.pd(G.MOTOR_T) / 2000), 1)},
}, indent=1))
