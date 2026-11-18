"""v4 (v3 arm + parallel-jaw gripper) gravity-torque and reach check from the CAD: printed-part masses from print_list.csv,
centroids from the STEP files, bought masses from datasheets/estimates. Computed, not measured.

usage: python sim/v3_check.py [payload_kg] [xy42_holding_nm]
Shoulder capacity = holding x 14, elbow = holding x 7, wrist = HEM 0.28 x 3. Budget = 50 %.
"""
import csv
import importlib.util
import json
import math
import sys
from pathlib import Path

from build123d import import_step

ROOT = Path(__file__).resolve().parent.parent
V = ROOT / "design/v4"
spec = importlib.util.spec_from_file_location("geometry", V / "geometry.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)
payload = float(sys.argv[1]) if len(sys.argv) > 1 else 0.15
hold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.26
grams = {r["part"]: float(r["est_grams"]) / 1000 for r in csv.DictReader(open(V / "print_list.csv"))}


def centroid_x(step):
    """Centroid along the link (local x) of a printed part modelled with its pivot at the origin."""
    return import_step(str(V / "printed" / step)).center().X


XY42, HEM, SERVO, BRG, PULLEY, BOLT = 0.28, 0.22, 0.060, 0.0034, 0.008, 0.006   # kg [datasheet / est]
lower = [(grams["lower-shank"], centroid_x("lower_shank.step")), (XY42 + PULLEY + 4 * 0.001, G.L1 - G.C_EL),
         (2 * BRG + BOLT, G.L1)]                                        # (kg, distance from S along the lower shank)
upper = [(grams["upper-shank"], centroid_x("upper_shank.step")), (HEM + PULLEY + 4 * 0.001, G.L2 - G.C_WR),
         (BOLT, G.L2)]                                                  # from E along the upper shank
hand_fixed = [(grams["wrist-pulley"] + 2 * BRG + BOLT, 0.0), (grams["gripper-base"], 35.0),
              (SERVO, G.GRIP_SERVO_G + (10.35 if getattr(G, "GRIP_SERVO_BODY_FWD", False) else -10.35)),
              (grams["crank-gear-a"] + grams["crank-gear-b"] + 2 * grams["idler-link-a"] + 0.012, G.GRIP_SERVO_G + 12),  # + 7 M3 bolts/nuts
              (grams["jaw-a"] + grams["jaw-b"], G.TOOL - 10)]
GRAV = 9.81e-3                                                          # N per kg-mm -> N·m


def torques(th1, th2, wr, m_pay):
    c1, c2, cw = (math.cos(math.radians(a)) for a in (th1, th2, wr))
    hand = hand_fixed + [(m_pay, G.TOOL)]
    m_hand = sum(m for m, _ in hand)
    x_hand = sum(m * d for m, d in hand) * cw                           # hand moment about W (kg mm)
    m_up = sum(m for m, _ in upper)
    tau3 = abs(x_hand) * GRAV
    tau2 = abs(sum(m * d for m, d in upper) * c2 + m_hand * G.L2 * c2 + x_hand) * GRAV
    tau1 = abs(sum(m * d for m, d in lower) * c1 + (m_up + m_hand) * G.L1 * c1
               + sum(m * d for m, d in upper) * c2 + m_hand * G.L2 * c2 + x_hand) * GRAV
    return tau1, tau2, tau3


cap = (hold * 14, hold * 7, 0.28 * 3)
worst, where = [0, 0, 0], [None] * 3
best_reach = 0
for th1 in range(int(G.TH1_LIM[0]), int(G.TH1_LIM[1]) + 1, 2):
    for q2 in range(int(G.Q2_LIM[0]), int(G.Q2_LIM[1]) + 1, 2):
        th2 = th1 + q2
        for wr in (-90, th2):                                           # gripper down, or in line with the shank
            t = torques(th1, th2, wr, payload)
            for i in range(3):
                if t[i] > worst[i]:
                    worst[i], where[i] = t[i], (th1, th2, wr)
        wx = G.S_X + G.L1 * math.cos(math.radians(th1)) + G.L2 * math.cos(math.radians(th2))
        wz = G.S_Z + G.L1 * math.sin(math.radians(th1)) + G.L2 * math.sin(math.radians(th2))
        if abs(wz - G.TOOL - 15) < 3:                                    # fingertips 15 mm over the table, gripper down
            best_reach = max(best_reach, wx)


def max_payload(limit=0.5):
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = (lo + hi) / 2
        w = [0, 0, 0]
        for th1 in range(int(G.TH1_LIM[0]), int(G.TH1_LIM[1]) + 1, 4):
            for q2 in range(int(G.Q2_LIM[0]), int(G.Q2_LIM[1]) + 1, 4):
                for wr in (-90, th1 + q2):
                    t = torques(th1, th1 + q2, wr, mid)
                    w = [max(a, b) for a, b in zip(w, t)]
        if all(w[i] <= limit * cap[i] for i in range(3)):
            lo = mid
        else:
            hi = mid
    return lo


print(json.dumps({
    "payload_kg": payload, "holding_nm": hold, "capacity_nm": [round(c, 2) for c in cap],
    "worst_nm": [round(x, 3) for x in worst], "worst_frac": [round(w / c, 3) for w, c in zip(worst, cap)],
    "worst_pose_th1_th2_wr": where, "table_reach_mm_gripper_down": round(best_reach),
    "max_payload_kg_at_50pct_anywhere": round(max_payload(), 3),
    "max_payload_kg_at_100pct_holding": round(max_payload(1.0), 3),
    "masses_kg": {"lower_shank": grams["lower-shank"], "upper_shank": grams["upper-shank"]},
}, indent=1))
