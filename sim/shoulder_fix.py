"""Shoulder torque post-mortem and fix options for v4 (user test 2026-11-16: the shoulder lifts the arm folded but
not stretched). Same CAD mass model as sim/v4_check.py; prints the gravity torque at the shoulder for the poses the
user tried, what the motor can give through the belts, and what each fix changes. Computed, not measured.
usage: python tools/mpy.py sim/shoulder_fix.py
"""
import csv
import importlib.util
import json
import math
from pathlib import Path

from build123d import import_step

ROOT = Path(__file__).resolve().parent.parent
V = ROOT / "design/v4"
spec = importlib.util.spec_from_file_location("geometry", V / "geometry.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)
grams = {r["part"]: float(r["est_grams"]) / 1000 for r in csv.DictReader(open(V / "print_list.csv"))}
cx = lambda step: import_step(str(V / "printed" / step)).center().X

XY42, HEM, SERVO, BRG, PULLEY, BOLT = 0.28, 0.22, 0.060, 0.0034, 0.008, 0.006
CABLE = 0.035                       # est: motor + servo cables along the arm, kg, about mid-arm
lower = [(grams["lower-shank"], cx("lower_shank.step")), (XY42 + PULLEY + 0.004, G.L1 - G.C_EL), (2 * BRG + BOLT, G.L1)]
upper = [(grams["upper-shank"], cx("upper_shank.step")), (HEM + PULLEY + 0.004, G.L2 - G.C_WR), (BOLT, G.L2)]
hand_grip = [(grams["wrist-pulley"] + 2 * BRG + BOLT, 0.0), (grams["gripper-base"], 35.0),
             (SERVO, G.GRIP_SERVO_G + 10.35),
             (grams["crank-gear-a"] + grams["crank-gear-b"] + 2 * grams["idler-link-a"] + 0.012, G.GRIP_SERVO_G + 12),
             (grams["jaw-a"] + grams["jaw-b"], G.TOOL - 10)]
hand_bare = [(grams["wrist-pulley"] + 2 * BRG + BOLT, 0.0)]
GRAV = 9.81e-3


def shoulder_torque(th1, th2, wr, hand, payload=0.0):
    c1, c2, cw = (math.cos(math.radians(a)) for a in (th1, th2, wr))
    hand = hand + ([(payload, G.TOOL)] if payload else [])
    m_hand = sum(m for m, _ in hand)
    x_hand = sum(m * d for m, d in hand) * cw
    m_up = sum(m for m, _ in upper)
    t = (sum(m * d for m, d in lower) * c1 + (m_up + m_hand) * G.L1 * c1 + sum(m * d for m, d in upper) * c2
         + m_hand * G.L2 * c2 + x_hand + CABLE * (G.L1 + G.L2 * 0.5) * c1) * GRAV
    return abs(t)


RATIO = (G.SH_T1 / G.MOTOR_T) * (G.SH_T3 / G.SH_T2)     # 72/20 x 140/36
HOLD_RATED = 0.26                    # N·m at 1.2 A: the series' 6-lead figure (the -1204A row is unpublished)
I_SET = 1.0                          # A, Vref 0.80 V (docs/bring-up.md)
ETA = 0.90 * 0.90                    # two belt stages with printed pulleys and bearings (est)
DYN = 0.60                           # pull-out torque at the low jog speed and 1/8 microstepping vs holding (est)


def capacity(ratio=RATIO, i=I_SET, hold=HOLD_RATED):
    static = hold * (i / 1.2) * ratio * ETA
    return static, static * DYN


poses = {
    "stretched, lower shank 20 deg up, gripper down": (20, 20, -90),
    "stretched horizontal (th1 = th2 = 0, outside the limits but reachable by hand)": (0, 0, -90),
    "elbow folded (q2 -135), th1 20": (20, -115, -90),
    "elbow folded, th1 60": (60, -75, -90),
}
out = {"ratio": round(RATIO, 3), "stage1": f"{G.MOTOR_T}T -> {G.SH_T1}T = {G.SH_T1 / G.MOTOR_T:.2f}",
       "stage2": f"{G.SH_T2}T -> {G.SH_T3}T = {G.SH_T3 / G.SH_T2:.3f}", "torque_nm": {}}
for name, (a, b, w) in poses.items():
    out["torque_nm"][name] = {"bare wrist": round(shoulder_torque(a, b, w, hand_bare), 3),
                              "with gripper": round(shoulder_torque(a, b, w, hand_grip), 3),
                              "gripper + 100 g": round(shoulder_torque(a, b, w, hand_grip, 0.1), 3)}
s, d = capacity()
out["capacity_design_nm"] = {"holding x ratio (what the sizing used, 0.26 x 14)": round(HOLD_RATED * RATIO, 2),
                             "at 1.0 A, after belt losses (static)": round(s, 2), "moving, estimate": round(d, 2)}
fixes = {}
for label, kw in {"current 1.2 A (Vref 0.96 V) + fan": dict(i=1.2),
                  "16T motor pulley (ratio 17.5)": dict(ratio=(72 / 16) * (140 / 36)),
                  "16T pulley + 1.2 A": dict(ratio=(72 / 16) * (140 / 36), i=1.2)}.items():
    s2, d2 = capacity(**kw)
    fixes[label] = {"static_nm": round(s2, 2), "moving_nm": round(d2, 2), "gain": f"{d2 / d - 1:+.0%}"}
out["fixes_capacity"] = fixes
# counterbalance: an extension spring from a fixed point on the turret to the lower shank, sized to cancel the arm's
# own weight at the stretched pose
need = shoulder_torque(20, 20, -90, hand_grip)
out["spring_to_cancel_arm_weight_nm"] = round(need * 0.8, 2)
print(json.dumps(out, indent=1))
