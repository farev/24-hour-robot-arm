"""Writes design/v3/assembly.yaml (home) and design/v3/poses/<name>/assembly.yaml from the joint angles.
Serial arm: elbow stepper rides on the lower shank, wrist stepper on the upper shank.
usage: python design/v3/build_assembly.py
"""
import importlib.util
import math
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


G = load("geometry", HERE / "geometry.py")
C = load("style", HERE / "printed/style.py").COLORS
PR, MD, BT = "design/v3/printed", "parts/models", "design/v3/bought"


def Rx(a):
    a = math.radians(a); c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def Ry(a):
    a = math.radians(a); c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def Rz(a):
    a = math.radians(a); c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def euler_xyz(R):
    b = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    if abs(math.cos(b)) > 1e-9:
        a = math.atan2(R[2, 1], R[2, 2]); c = math.atan2(R[1, 0], R[0, 0])
    else:
        a = math.atan2(-R[1, 2], R[1, 1]); c = 0.0
    return [round(math.degrees(v), 4) for v in (a, b, c)]


cols = lambda x, y, z: np.column_stack([x, y, z]).astype(float)


def build(pose):
    yaw, th1, th2, wr, grip = pose["yaw"], pose["th1"], pose["th2"], pose["wr"], pose.get("grip", 15.0)
    Yw = Rz(yaw)
    ang = lambda a: np.array([math.cos(math.radians(a)), 0, math.sin(math.radians(a))])
    u1, u2, g = ang(th1), ang(th2), ang(wr)
    n1, n2 = ang(th1 + 90), ang(th2 + 90)
    h = ang(wr + 90)
    yv = np.array([0, 1.0, 0])
    S = np.array([G.S_X, 0, G.S_Z]); E = S + G.L1 * u1; W = E + G.L2 * u2
    at = lambda p, y: np.array([p[0], y, p[2]])
    parts, allow = [], []

    def add(pid, model, kind, comp, color, R, p, turret=True):
        Rw, pw = (Yw @ R, Yw @ np.asarray(p, float)) if turret else (R, np.asarray(p, float))
        parts.append({"id": pid, "model": model, "kind": kind, "component": comp, "color": color,
                      "position": [round(float(v), 4) for v in pw], "rotation": euler_xyz(Rw)})

    def ok(a, b, why):
        allow.append([a, b, why])

    I3 = np.eye(3)
    pla = "pla-filament"
    Yy = G.Y
    # ---------------- base (fixed) ----------------
    YMZ = G.YAW_MOTOR_FACE_Z
    add("base", f"{PR}/base.step", "printed", pla, C["structure"], I3, (0, 0, 0), turret=False)
    add("yaw-motor-plate", f"{PR}/yaw_motor_plate.step", "printed", pla, C["structure"], I3, (-G.C_YAW, 0, YMZ), turret=False)
    add("yaw-motor", f"{MD}/xy42sth40-1204a.step", "bought", "xy42sth40-1204a", C["metal"], I3, (-G.C_YAW, 0, YMZ), turret=False)
    add("yaw-motor-pulley", f"{MD}/gt2-20t-pulley.step", "bought", "gt2-20t-pulley", C["metal"], I3,
        (-G.C_YAW, 0, YMZ + G.YAW_PLATE_T + 0.5), turret=False)
    add("belt-yaw", f"{BT}/belt_yaw.step", "bought", "gt2-belt-320", C["belt"], I3, (0, 0, 0), turret=False)
    add("axk2035", f"{MD}/axk2035-thrust-bearing.step", "bought", "axk2035-thrust-bearing", C["metal"], I3, (0, 0, G.AXK_Z0), turret=False)
    add("yaw-bearing-top", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], I3, (0, 0, G.AXK_Z0), turret=False)
    add("yaw-bearing-bottom", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(180), (0, 0, 8.0), turret=False)
    add("yaw-race-washer", f"{PR}/race_washer.step", "printed", pla, C["structure"], I3, (0, 0, 7.0), turret=False)
    add("yaw-switch", f"{MD}/kw12-3-switch.step", "bought", "kw12-3-switch", C["servo"], Rz(90),
        (26.0, 0, (G.YAW_PULLEY_Z[0] - 1.2) + 1.0 - 6.0 - 10.2), turret=False)
    add("uno-cnc-shield", f"{MD}/arduino-uno-r3.step", "bought", ["arduino-uno-r3", "cnc-shield-v3-a4988"], C["board"], I3,
        (-118.0, 36.0, 9.0), turret=False)
    add("uno-usb-keepout", f"{MD}/arduino-uno-r3-keepout.step", "bought", "arduino-uno-r3", C["keepout"], I3, (-118.0, 36.0, 9.0), turret=False)
    add("buck-converter", f"{MD}/xl4015-buck.step", "bought", "xl4015-buck", C["board"], I3, (-90.0, -45.0, 9.0), turret=False)
    for i, (sx, sy) in enumerate([(-1, -1), (-1, 1), (1, -1), (1, 1)]):
        add(f"yaw-motor-screw-{i+1}", f"{MD}/m3x6-shcs.step", "bought", "m3-m4-kit", C["fastener"], I3,
            (-G.C_YAW + sx * 15.5, sy * 15.5, YMZ + G.YAW_PLATE_T), turret=False)
        add(f"yaw-plate-screw-{i+1}", f"{MD}/m3x16-shcs.step", "bought", "m3-m4-kit", C["fastener"], I3,
            (-G.C_YAW + sx * 26, sy * 26, YMZ + G.YAW_PLATE_T), turret=False)
        ok(f"yaw-motor-screw-{i+1}", "yaw-motor", "thread"); ok(f"yaw-plate-screw-{i+1}", "base", "self-tap in post pilot")
    for a, b, why in (("yaw-motor-pulley", "yaw-motor", "hub on shaft"), ("belt-yaw", "yaw-motor-pulley", "belt mesh"),
                      ("belt-yaw", "yaw-pulley", "belt mesh"), ("axk2035", "base", "washer in its seat"),
                      ("axk2035", "yaw-pulley", "washer on the spigot"), ("yaw-bearing-top", "base", "press fit"),
                      ("yaw-bearing-bottom", "base", "press fit"), ("yaw-switch", "base", "glued in its pocket"),
                      ("yaw-switch", "yaw-pulley", "roller pressed by the cam"), ("uno-usb-keepout", "uno-cnc-shield", "keep-out"),
                      ("yaw-motor", "yaw-motor-plate", "face on the plate, pilot in the slot"),
                      ("yaw-motor", "base", "motor stands in the floor cut-out")):
        ok(a, b, why)
    # ---------------- turret ----------------
    Z0 = G.DECK_Z[0]
    add("turret", f"{PR}/turret.step", "printed", pla, C["structure"], I3, (0, 0, Z0))
    add("yaw-pulley", f"{PR}/yaw_pulley.step", "printed", pla, C["accent"], Rx(180), (0, 0, G.YAW_PULLEY_Z[1]))
    add("yaw-bolt", f"{MD}/m4x60-shcs.step", "bought", "m4x60-shcs", C["fastener"], I3, (0, 0, Z0))
    add("yaw-nut", f"{MD}/m4-nut.step", "bought", "m3-m4-kit", C["fastener"], I3, (0, 0, 3.8))
    for a in ("yaw-nut", "yaw-bearing-top", "yaw-bearing-bottom", "yaw-race-washer", "axk2035"):
        ok("yaw-bolt", a, "bolt through bores / thread")
    for i, t in enumerate((45, 135, 225, 315)):
        x, y = 32 * math.cos(math.radians(t)), 32 * math.sin(math.radians(t))
        add(f"deck-screw-{i+1}", f"{MD}/m3x10-shcs.step", "bought", "m3-m4-kit", C["fastener"], Rx(180), (x, y, G.YAW_PULLEY_Z[0] + 5.3))
        add(f"deck-nut-{i+1}", f"{MD}/m3-nut.step", "bought", "m3-m4-kit", C["fastener"], I3, (x, y, G.DECK_Z[1] - 3.8))
        ok(f"deck-screw-{i+1}", f"deck-nut-{i+1}", "thread")
    TL, TR = Yy["tower_l"], Yy["tower_r"]
    M, Ip = G.SH_MOTOR, G.I_PT
    add("shoulder-motor", f"{MD}/xy42sth40-1204a.step", "bought", "xy42sth40-1204a", C["metal"], Rx(90), (M[0], TR[1], M[1]))
    add("shoulder-motor-plug-keepout", f"{MD}/xy42sth40-1204a-keepout.step", "bought", "xy42sth40-1204a", C["keepout"],
        Rx(90), (M[0], TR[1], M[1]))
    add("shoulder-motor-pulley", f"{MD}/gt2-20t-pulley.step", "bought", "gt2-20t-pulley", C["metal"], Rx(90), (M[0], TR[1] - 2.5, M[1]))
    add("belt-sh1", f"{BT}/belt_sh1.step", "bought", "gt2-belt-200", C["belt"], I3, (0, 0, 0))
    add("belt-sh2", f"{BT}/belt_sh2.step", "bought", "gt2-belt-320", C["belt"], I3, (0, 0, 0))
    k = 0
    for hx in (-15.5, 15.5):
        for hz in (-15.5, 15.5):
            k += 1
            add(f"shoulder-motor-screw-{k}", f"{MD}/m3x10-shcs.step", "bought", "m3-m4-kit", C["fastener"], Rx(90),
                (M[0] + hx, TR[0] + 3.0, M[1] + hz))
            ok(f"shoulder-motor-screw-{k}", "shoulder-motor", "thread")
    for a, b, why in (("shoulder-motor", "turret", "face on the tower"), ("shoulder-motor-plug-keepout", "shoulder-motor", "keep-out"),
                      ("shoulder-motor-pulley", "shoulder-motor", "hub on shaft"), ("belt-sh1", "shoulder-motor-pulley", "mesh"),
                      ("belt-sh1", "sh-compound", "mesh with the 72T"), ("belt-sh2", "sh-compound", "mesh with the 36T"),
                      ("belt-sh2", "lower-shank", "mesh with the 140T")):
        ok(a, b, why)
    # S axle and I axle stacks (head counterbored in the left tower, nut in the right tower)
    for tag, P, extra in (("s", (G.S_X, G.S_Z), []), ("i", Ip, [])):
        add(f"{tag}-axle", f"{MD}/m4x70-shcs.step", "bought", "m4x70-shcs", C["fastener"], Rx(90), (P[0], TL[0] + 4.4, P[1]))
        add(f"{tag}-nut", f"{MD}/m4-nut.step", "bought", "m3-m4-kit", C["fastener"], Rx(-90) @ Rz(30), (P[0], TR[1] - 3.5, P[1]))
        add(f"{tag}-washer-left", f"{PR}/race_washer.step", "printed", pla, C["structure"], Rx(-90), (P[0], TL[1], P[1]))
        add(f"{tag}-washer-right", f"{PR}/race_washer.step", "printed", pla, C["structure"], Rx(-90), (P[0], TR[0] - 1.0, P[1]))
        for a in (f"{tag}-nut", f"{tag}-washer-left", f"{tag}-washer-right", "turret"):
            ok(f"{tag}-axle", a, "axle in its bores / thread")
    add("sh-compound", f"{PR}/shoulder_compound.step", "printed", pla, C["accent"], Rx(90), (Ip[0], TR[0] - 1.0, Ip[1]))
    add("i-bearing-1", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(-90), (Ip[0], TR[0] - 1.0, Ip[1]))
    add("i-bearing-2", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(90), (Ip[0], Yy["pulley_l"][0], Ip[1]))
    add("spacer-i", f"{PR}/spacer_i.step", "printed", pla, C["structure"], Rx(-90), (Ip[0], Yy["pulley_l"][0] + 5, Ip[1]))
    add("spacer-i-2", f"{PR}/spacer_i.step", "printed", pla, C["structure"], Rx(-90), (Ip[0], Yy["pulley_l"][0] + 25, Ip[1]))
    ok("i-axle", "spacer-i-2", "axle through the bore"); ok("spacer-i-2", "sh-compound", "inside the tube")
    add("spacer-s", f"{PR}/spacer_s.step", "printed", pla, C["structure"], Rx(-90), (G.S_X, Yy["lower"][1], G.S_Z))
    add("spacer-ls", f"{PR}/spacer_ls.step", "printed", pla, C["structure"], Rx(-90), (G.S_X, Yy["pulley_l"][0] + 5, G.S_Z))
    for a in ("i-bearing-1", "i-bearing-2", "spacer-i"):
        ok("i-axle", a, "axle through the bore")
        ok(a, "sh-compound", "press fit / inside the tube")
    for a in ("spacer-s", "spacer-ls", "lower-bearing-1", "lower-bearing-2"):
        ok("s-axle", a, "axle through the bore")
    # ---------------- arm ----------------
    R1, R2 = Ry(-th1) @ Rx(90), Ry(-th2) @ Rx(90)
    add("lower-shank", f"{PR}/lower_shank.step", "printed", pla, C["accent"], R1, at(S, Yy["lower"][1]))
    add("lower-bearing-1", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(90), at(S, Yy["pulley_l"][0]))
    add("lower-bearing-2", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(-90), at(S, Yy["lower"][1]))
    ok("lower-bearing-1", "lower-shank", "press fit"); ok("lower-bearing-2", "lower-shank", "press fit")
    ok("spacer-ls", "lower-shank", "race tube in the hub bore")
    EM = S + (G.L1 - G.C_EL) * u1
    Rem = Ry(-th1) @ Rx(-90)
    add("elbow-motor", f"{MD}/xy42sth40-1204a.step", "bought", "xy42sth40-1204a", C["metal"], Rem, at(EM, Yy["lower"][0]))
    add("elbow-motor-plug-keepout", f"{MD}/xy42sth40-1204a-keepout.step", "bought", "xy42sth40-1204a", C["keepout"], Rem,
        at(EM, Yy["lower"][0]))
    add("elbow-motor-pulley", f"{MD}/gt2-20t-pulley.step", "bought", "gt2-20t-pulley", C["metal"], Rem,
        at(EM, Yy["lower"][0] + G.PILOT_H + G.EL_HUB_GAP))
    add("belt-elbow", f"{BT}/belt_elbow.step", "bought", "gt2-belt-320", C["belt"], Ry(-th1), at(S, 0))
    k = 0
    for a in (-15.5, 15.5):
        for b in (-15.5, 15.5):
            k += 1
            add(f"elbow-motor-screw-{k}", f"{MD}/m3x8-shcs.step", "bought", "m3-m4-kit", C["fastener"], Rem,
                at(EM + a * u1 + b * n1, Yy["lower"][1] - 6.0))
            ok(f"elbow-motor-screw-{k}", "elbow-motor", "thread")
    for a, b, why in (("elbow-motor", "lower-shank", "face on the plate, pilot in the slot"),
                      ("elbow-motor-plug-keepout", "elbow-motor", "keep-out"), ("elbow-motor-pulley", "elbow-motor", "hub on shaft"),
                      ("belt-elbow", "elbow-motor-pulley", "mesh"), ("belt-elbow", "upper-shank", "mesh with the 140T")):
        ok(a, b, why)
    # elbow joint
    add("upper-shank", f"{PR}/upper_shank.step", "printed", pla, C["structure"], R2, at(E, Yy["upper"][1]))
    add("elbow-bearing-1", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(-90), at(E, Yy["upper"][1]))
    add("elbow-bearing-2", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(90), at(E, Yy["upper_teeth"][0]))
    add("spacer-e", f"{PR}/spacer_e.step", "printed", pla, C["structure"], Rx(-90), at(E, Yy["upper_teeth"][0] + 5))
    add("e-bolt", f"{MD}/m4x30-shcs.step", "bought", "m3-m4-kit", C["fastener"], Rx(90), at(E, Yy["lower"][0] + 4.4))
    add("e-washer-1", f"{PR}/race_washer.step", "printed", pla, C["structure"], Rx(-90), at(E, Yy["lower"][1]))
    add("e-washer-2", f"{PR}/race_washer.step", "printed", pla, C["structure"], Rx(-90), at(E, Yy["upper"][1]))
    add("e-nut", f"{MD}/m4-nut.step", "bought", "m3-m4-kit", C["fastener"], Rx(-90), at(E, Yy["upper"][1] + 1.0))
    ok("elbow-bearing-1", "upper-shank", "press fit"); ok("elbow-bearing-2", "upper-shank", "press fit")
    ok("spacer-e", "upper-shank", "race tube in the hub bore")
    for a in ("lower-shank", "e-washer-1", "e-washer-2", "e-nut", "elbow-bearing-1", "elbow-bearing-2", "spacer-e"):
        ok("e-bolt", a, "bolt snug in the lower shank / through the stack")
    # wrist motor on the upper shank, wrist belt, wrist joint
    WM = E + (G.L2 - G.C_WR) * u2
    Rwm = Ry(-th2) @ Rx(90)
    add("wrist-motor", f"{MD}/hem-17d2008-10.step", "bought", "hem-17d2008-10", C["metal"], Rwm, at(WM, Yy["upper"][1]))
    add("wrist-motor-pulley", f"{MD}/gt2-20t-pulley.step", "bought", "gt2-20t-pulley", C["metal"], Rwm,
        at(WM, Yy["upper"][1] - G.PILOT_H - G.WR_HUB_GAP))
    add("belt-wrist", f"{BT}/belt_wrist.step", "bought", "gt2-belt-200", C["belt"], Ry(-th2), at(E, 0))
    k = 0
    for a in (-15.5, 15.5):
        for b in (-15.5, 15.5):
            k += 1
            add(f"wrist-motor-screw-{k}", f"{MD}/m3x8-shcs.step", "bought", "m3-m4-kit", C["fastener"], Rwm,
                at(WM + a * u2 + b * n2, Yy["upper"][0] + 6.0))
            ok(f"wrist-motor-screw-{k}", "wrist-motor", "thread")
    Rg = cols(g, -h, yv)
    add("wrist-axle", f"{MD}/m4x30-shcs.step", "bought", "m3-m4-kit", C["fastener"], Rx(-90), at(W, Yy["upper"][1] - 4.4))
    add("wrist-washer", f"{PR}/race_washer.step", "printed", pla, C["structure"], Rx(-90), at(W, Yy["wrist_pulley"][1]))
    add("wrist-pulley", f"{PR}/wrist_pulley.step", "printed", pla, C["accent"], Rg, at(W, Yy["wrist_pulley"][0]))
    add("wrist-bearing-1", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(-90), at(W, Yy["wrist_pulley"][1]))
    add("wrist-bearing-2", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(90), at(W, Yy["wrist_pulley"][0]))
    add("spacer-w", f"{PR}/spacer_w.step", "printed", pla, C["structure"], Rx(-90), at(W, Yy["wrist_pulley"][0] + 5))
    add("wrist-nut", f"{MD}/m4-nut.step", "bought", "m3-m4-kit", C["fastener"], Rx(90), at(W, Yy["wrist_pulley"][0]))
    for a, b, why in (("wrist-motor", "upper-shank", "face on the beam, pilot in the slot"), ("wrist-motor-pulley", "wrist-motor", "hub on shaft"),
                      ("belt-wrist", "wrist-motor-pulley", "mesh"), ("belt-wrist", "wrist-pulley", "mesh with the 60T"),
                      ("wrist-bearing-1", "wrist-pulley", "press fit"), ("wrist-bearing-2", "wrist-pulley", "press fit"),
                      ("spacer-w", "wrist-pulley", "race tube in the hub bore")):
        ok(a, b, why)
    for a in ("upper-shank", "wrist-washer", "wrist-bearing-1", "wrist-bearing-2", "spacer-w", "wrist-nut", "gripper-base"):
        ok("wrist-axle", a, "axle snug in the beam / through the stack")
    ok("wrist-nut", "gripper-base", "nut inside the plate's Ø10 hole")
    # gripper
    GS, GH = G.GRIP_SERVO_G, G.GEAR_M * G.GEAR_T / 2
    sa, sb = W + GS * g - GH * h, W + GS * g + GH * h
    add("gripper-base", f"{PR}/gripper_base.step", "printed", pla, C["structure"], Rg, at(W, Yy["grip_plate"][0]))
    Rgs = cols(-g, h, yv)
    add("gripper-servo", f"{MD}/mg996r-servo.step", "bought", "mg996r-servo", C["servo"], Rgs, at(sa, G.GRIP_SERVO_TOP_Y))
    add("gripper-horn", f"{MD}/mg996r-horn.step", "bought", "mg996r-servo", C["servo"], Rgs, at(sa, G.GRIP_SERVO_TOP_Y))
    add("finger-a", f"{PR}/finger_a.step", "printed", pla, C["accent"], Rg @ Rz(grip), at(sa, G.FINGER_Y0))
    add("finger-b", f"{PR}/finger_b.step", "printed", pla, C["accent"], Rg @ Rz(-grip), at(sb, G.FINGER_Y0 + 0.6))
    add("grip-pivot", f"{MD}/m3x30-shcs.step", "bought", "m3-m4-kit", C["fastener"], Rx(90), at(sb, Yy["grip_plate"][0]))
    add("grip-pivot-nut", f"{MD}/m3-nut.step", "bought", "m3-m4-kit", C["fastener"], Rx(-90), at(sb, G.FINGER_Y0 + 0.6 + 5.4 + 0.2))
    for i, a in enumerate((45, 135, 225, 315)):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        add(f"grip-mount-screw-{i+1}", f"{MD}/m3x16-shcs.step", "bought", "m3-m4-kit", C["fastener"], Rx(90),
            at(W + 15 * c * g - 15 * s * h, Yy["grip_plate"][0]))
        ok(f"grip-mount-screw-{i+1}", "wrist-pulley", "self-tapping screw in its pilot")
    for a, b, why in (("gripper-servo", "gripper-base", "tabs on the plate, body in the window"), ("gripper-horn", "gripper-servo", "horn on spline"),
                      ("finger-a", "gripper-horn", "gear A screwed to the horn"), ("finger-a", "finger-b", "gears in mesh"),
                      ("grip-pivot", "gripper-base", "snug in the boss"), ("grip-pivot", "finger-b", "finger turns on it"),
                      ("grip-pivot", "grip-pivot-nut", "thread"), ("gripper-base", "wrist-pulley", "plate screwed to the pulley face")):
        ok(a, b, why)
    ids = {p["id"] for p in parts}
    return parts, [[a, b] for a, b, _ in allow if a in ids and b in ids], {"W": W, "E": E}


def write(path, pose, note):
    parts, allow, pts = build(pose)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {"min_clearance_mm": 0.5, "pose": pose, "note": note, "parts": parts, "allow_contact": allow}
    path.write_text(yaml.safe_dump(doc, sort_keys=False, width=140))
    gdir = np.array([math.cos(math.radians(pose["wr"])), 0, math.sin(math.radians(pose["wr"]))])
    tip = pts["W"] + G.TOOL * gdir
    print(path.relative_to(HERE.parent.parent), len(parts), "parts; W", pts["W"].round(1), "tip", tip.round(1))


POSES = {
    None: ({"yaw": 0, "th1": 90, "th2": 0, "wr": -90, "grip": 15}, "home / rest pose"),
    "reach-table": ({"yaw": 0, "th1": 20, "th2": -18.4, "wr": -90, "grip": 25}, "gripper down, fingertips ~15 mm above the table"),
    "elbow-up": ({"yaw": 0, "th1": 70, "th2": 150, "wr": 60, "grip": 15}, "elbow bent up and back (q2 = +80), past what the linkage allowed"),
    "elbow-folded": ({"yaw": 0, "th1": 110, "th2": -25, "wr": 20, "grip": 0},
                     "elbow folded down to the -135 limit, gripper tilted away from the lower shank"),
    "stretched": ({"yaw": 0, "th1": 20, "th2": 20, "wr": 20, "grip": 15}, "arm straight, gripper in line"),
    "yaw-limit": ({"yaw": 150, "th1": 60, "th2": -20, "wr": -90, "grip": 15}, "base at +150 deg"),
}
if __name__ == "__main__":
    for name, (pose, note) in POSES.items():
        write(HERE / ("assembly.yaml" if name is None else f"poses/{name}/assembly.yaml"), pose, note)
