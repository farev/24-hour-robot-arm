"""Writes design/v2/assembly.yaml (home pose) and design/v2/poses/<name>/assembly.yaml from the joint
angles, placing every part by its datum (pivot axes, mating faces) from geometry.py.

usage: python design/v2/build_assembly.py
Rotations in assembly.yaml are extrinsic X, Y, Z (deg) about each model's origin, then position (mm).
"""
import importlib.util
import math
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("geometry", HERE / "geometry.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)
spec = importlib.util.spec_from_file_location("style", HERE / "printed/style.py")
ST = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ST)
C = ST.COLORS
PR = "design/v2/printed"
MD = "parts/models"


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
    """R = Rz(c) Ry(b) Rx(a) -> (a, b, c) degrees (extrinsic X then Y then Z)."""
    b = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    if abs(math.cos(b)) > 1e-9:
        a = math.atan2(R[2, 1], R[2, 2]); c = math.atan2(R[1, 0], R[0, 0])
    else:
        a = math.atan2(-R[1, 2], R[1, 1]); c = 0.0
    return [round(math.degrees(v), 4) for v in (a, b, c)]


def cols(x, y, z):
    return np.column_stack([x, y, z]).astype(float)


def build(pose):
    yaw, th1, th2, wr, grip = pose["yaw"], pose["th1"], pose["th2"], pose["wr"], pose.get("grip", 15.0)
    Y = Rz(yaw)
    u1 = np.array([math.cos(math.radians(th1)), 0, math.sin(math.radians(th1))])
    u2 = np.array([math.cos(math.radians(th2)), 0, math.sin(math.radians(th2))])
    S = np.array([G.S_X, 0, G.S_Z])
    E = S + G.L1 * u1
    W = E + G.L2 * u2
    L = S - G.LEVER * u2
    PU = E - G.LEVER * u2
    yv = np.array([0, 1.0, 0])
    at = lambda pt, y: np.array([pt[0], y, pt[2]])
    parts, allow = [], []

    def add(pid, model, kind, comp, color, R, p, turret=True, material=None):
        Rw, pw = (Y @ R, Y @ np.asarray(p, float)) if turret else (R, np.asarray(p, float))
        e = {"id": pid, "model": model, "kind": kind, "component": comp, "color": color,
             "position": [round(float(v), 4) for v in pw], "rotation": euler_xyz(Rw)}
        if material:
            e["material"] = material
        parts.append(e)

    I = np.eye(3)
    pla = "pla-filament"
    # ---------------- base (fixed) ----------------
    add("base", f"{PR}/base.step", "printed", pla, C["structure"], I, (0, 0, 0), turret=False)
    add("yaw-motor-plate", f"{PR}/yaw_motor_plate.step", "printed", pla, C["structure"], I,
        (-G.C_YAW, 0, G.YAW_MOTOR_FACE_Z), turret=False)
    add("yaw-motor", f"{MD}/hem-17d2008-10.step", "bought", "hem-17d2008-10", C["metal"], I,
        (-G.C_YAW, 0, G.YAW_MOTOR_FACE_Z), turret=False)
    add("yaw-motor-pulley", f"{MD}/gt2-20t-pulley.step", "bought", "gt2-20t-pulley", C["metal"], I,
        (-G.C_YAW, 0, G.YAW_MOTOR_FACE_Z + G.YAW_PLATE_T + G.PULLEY_HUB_GAP), turret=False)
    add("belt-yaw", "design/v2/bought/belt_yaw.step", "bought", "gt2-belt-320", C["belt"], I, (0, 0, 0), turret=False)
    add("axk2035", f"{MD}/axk2035-thrust-bearing.step", "bought", "axk2035-thrust-bearing", C["metal"], I,
        (0, 0, G.AXK_Z0), turret=False)
    add("yaw-bearing-top", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], I, (0, 0, G.AXK_Z0), turret=False)
    add("yaw-bearing-bottom", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(180), (0, 0, 8.0), turret=False)
    add("yaw-race-washer", f"{PR}/race_washer.step", "printed", pla, C["structure"], I, (0, 0, 7.0), turret=False)
    sw_body_top = (G.YAW_PULLEY_Z[0] - 1.2) + 1.0 - 6.0        # cam bottom + 1 mm press - roller height (base.py)
    add("yaw-switch", f"{MD}/kw12-3-switch.step", "bought", "kw12-3-switch", C["servo"], Rz(90),
        (26.0, 0, sw_body_top - 10.2), turret=False)
    add("uno-cnc-shield", f"{MD}/arduino-uno-r3.step", "bought", ["arduino-uno-r3", "cnc-shield-v3-a4988"], C["board"],
        I, (-118.0, 36.0, 9.0), turret=False)
    add("uno-usb-keepout", f"{MD}/arduino-uno-r3-keepout.step", "bought", "arduino-uno-r3", C["keepout"], I,
        (-118.0, 36.0, 9.0), turret=False)
    add("buck-converter", f"{MD}/xl4015-buck.step", "bought", "xl4015-buck", C["board"], I, (-90.0, -45.0, 9.0), turret=False)
    for i, (sx, sy) in enumerate([(-1, -1), (-1, 1), (1, -1), (1, 1)]):
        add(f"yaw-motor-screw-{i+1}", f"{MD}/m3x8-shcs.step", "bought", "m3-m4-kit", C["fastener"], I,
            (-G.C_YAW + sx * 15.5, sy * 15.5, G.YAW_MOTOR_FACE_Z + G.YAW_PLATE_T - 1.5), turret=False)   # 1.5 cb
        add(f"yaw-plate-screw-{i+1}", f"{MD}/m3x16-shcs.step", "bought", "m3-m4-kit", C["fastener"], I,
            (-G.C_YAW + sx * 26, sy * 26, G.YAW_MOTOR_FACE_Z + G.YAW_PLATE_T), turret=False)
        allow += [[f"yaw-motor-screw-{i+1}", "yaw-motor", "screw threads into the motor's M3 hole"],
                  [f"yaw-plate-screw-{i+1}", "base", "self-tapping screw in the post pilot"]]
    allow += [["yaw-motor-pulley", "yaw-motor", "pulley hub clamped on the motor shaft"],
              ["belt-yaw", "yaw-motor-pulley", "belt teeth mesh with the pulley"],
              ["belt-yaw", "yaw-pulley", "belt teeth mesh with the 120T ring"],
              ["axk2035", "base", "lower washer seated in the boss pocket, centred on the ring"],
              ["axk2035", "yaw-pulley", "upper washer on the hub spigot"],
              ["yaw-bearing-top", "base", "F624 press fit in the boss"],
              ["yaw-bearing-bottom", "base", "F624 press fit in the boss underside"],
              ["yaw-switch", "base", "switch glued in its pocket"],
              ["yaw-switch", "yaw-pulley", "spring lever pressed by the half-moon cam (home edge at yaw 0)"],
              ["uno-usb-keepout", "uno-cnc-shield", "USB plug keep-out belongs to the Uno"],
              ["yaw-motor", "yaw-motor-plate", "motor face screwed to the plate, pilot in the slot"]]
    # ---------------- turret (yaw) ----------------
    Z0 = G.DECK_Z[0]
    add("turret", f"{PR}/turret.step", "printed", pla, C["structure"], I, (0, 0, Z0))
    add("yaw-pulley", f"{PR}/yaw_pulley.step", "printed", pla, C["accent"], Rx(180), (0, 0, G.YAW_PULLEY_Z[1]))
    add("yaw-bolt", f"{MD}/m4x60-shcs.step", "bought", "m4x60-shcs", C["fastener"], I, (0, 0, Z0))   # head on the yaw pulley
    add("yaw-nut", f"{MD}/m4-nut.step", "bought", "m3-m4-kit", C["fastener"], I, (0, 0, 3.8))
    allow += [["yaw-bolt", "yaw-nut", "thread"], ["yaw-bolt", "yaw-bearing-top", "bolt in the bearing bore"],
              ["yaw-bolt", "yaw-bearing-bottom", "bolt in the bearing bore"], ["yaw-bolt", "yaw-race-washer", "washer on the bolt"],
              ["yaw-bolt", "axk2035", "bolt passes the thrust bearing bore"]]
    for i, t in enumerate((45, 135, 225, 315)):
        x, y = 32 * math.cos(math.radians(t)), 32 * math.sin(math.radians(t))
        add(f"deck-screw-{i+1}", f"{MD}/m3x10-shcs.step", "bought", "m3-m4-kit", C["fastener"], Rx(180),
            (x, y, G.YAW_PULLEY_Z[0] + 5.3))
        add(f"deck-nut-{i+1}", f"{MD}/m3-nut.step", "bought", "m3-m4-kit", C["fastener"], I, (x, y, G.DECK_Z[1] - 3.8))
        allow.append([f"deck-screw-{i+1}", f"deck-nut-{i+1}", "thread"])
    # arm motors on the towers + pulleys + belts + screws
    MX, MZ = G.ARM_MOTOR
    TL, TR = G.Y["tower_l"], G.Y["tower_r"]
    add("shoulder-motor", f"{MD}/xy42sth40-1204a.step", "bought", "xy42sth40-1204a", C["metal"], Rx(-90), (MX, TL[0], MZ))
    add("elbow-motor", f"{MD}/xy42sth40-1204a.step", "bought", "xy42sth40-1204a", C["metal"], Rx(90), (MX, TR[1], MZ))
    add("shoulder-motor-plug-keepout", f"{MD}/xy42sth40-1204a-keepout.step", "bought", "xy42sth40-1204a", C["keepout"],
        Rx(-90), (MX, TL[0], MZ))
    add("elbow-motor-plug-keepout", f"{MD}/xy42sth40-1204a-keepout.step", "bought", "xy42sth40-1204a", C["keepout"],
        Rx(90), (MX, TR[1], MZ))
    add("shoulder-motor-pulley", f"{MD}/gt2-20t-pulley.step", "bought", "gt2-20t-pulley", C["metal"], Rx(-90),
        (MX, TL[0] + G.PILOT_H + G.PULLEY_HUB_GAP, MZ))
    add("elbow-motor-pulley", f"{MD}/gt2-20t-pulley.step", "bought", "gt2-20t-pulley", C["metal"], Rx(90),
        (MX, TR[1] - G.PILOT_H - G.PULLEY_HUB_GAP, MZ))
    add("belt-shoulder", "design/v2/bought/belt_shoulder.step", "bought", "gt2-belt-320", C["belt"], I, (0, 0, 0))
    add("belt-elbow", "design/v2/bought/belt_elbow.step", "bought", "gt2-belt-320", C["belt"], I, (0, 0, 0))
    allow += [["shoulder-motor-pulley", "shoulder-motor", "hub on the shaft"], ["elbow-motor-pulley", "elbow-motor", "hub on the shaft"],
              ["belt-shoulder", "shoulder-motor-pulley", "belt mesh"], ["belt-shoulder", "lower-shank", "belt mesh with the 140T"],
              ["belt-elbow", "elbow-motor-pulley", "belt mesh"], ["belt-elbow", "lever-pulley", "belt mesh with the 140T"],
              ["shoulder-motor", "turret", "motor face bolted flat on the tower face"],
              ["elbow-motor", "turret", "motor face bolted flat on the tower face"],
              ["shoulder-motor-plug-keepout", "shoulder-motor", "plug keep-out belongs to the motor"],
              ["elbow-motor-plug-keepout", "elbow-motor", "plug keep-out belongs to the motor"]]
    k = 0
    for hx in (-15.5, 15.5):
        for hz in (-15.5, 15.5):
            k += 1
            add(f"shoulder-motor-screw-{k}", f"{MD}/m3x10-shcs.step", "bought", "m3-m4-kit", C["fastener"], Rx(-90),
                (MX + hx, TL[1] - 3.0, MZ + hz))
            add(f"elbow-motor-screw-{k}", f"{MD}/m3x10-shcs.step", "bought", "m3-m4-kit", C["fastener"], Rx(90),
                (MX + hx, TR[0] + 3.0, MZ + hz))
            allow += [[f"shoulder-motor-screw-{k}", "shoulder-motor", "screw threads into the motor"],
                      [f"elbow-motor-screw-{k}", "elbow-motor", "screw threads into the motor"]]
    # shoulder axle stack: head counterbored in the left tower, nut trapped in the right tower
    add("s-axle", f"{MD}/m4x70-shcs.step", "bought", "m4x70-shcs", C["fastener"], Rx(90), (G.S_X, TL[0] + 4.4, G.S_Z))
    add("s-nut", f"{MD}/m4-nut.step", "bought", "m3-m4-kit", C["fastener"], Rx(-90) @ Rz(30),   # vertex up, as the trap
        (G.S_X, TR[1] - 3.5, G.S_Z))
    add("s-washer-left", f"{PR}/race_washer.step", "printed", pla, C["structure"], Rx(-90), (G.S_X, TL[1], G.S_Z))
    add("s-washer-right", f"{PR}/race_washer.step", "printed", pla, C["structure"], Rx(-90), (G.S_X, TR[0] - 1.0, G.S_Z))
    add("spacer-s", f"{PR}/spacer_s.step", "printed", pla, C["structure"], Rx(-90), (G.S_X, G.Y["lower"][1], G.S_Z))
    add("spacer-ls", f"{PR}/spacer_ls.step", "printed", pla, C["structure"], Rx(-90), (G.S_X, G.Y["pulley_l"][0] + 5, G.S_Z))
    for a in ("s-nut", "s-washer-left", "s-washer-right", "spacer-s", "spacer-ls", "lower-bearing-1", "lower-bearing-2",
              "lever-bearing-1", "lever-bearing-2", "turret"):
        allow.append(["s-axle", a, "axle through its bore / thread" if a != "turret" else "axle snug in the tower holes"])
    # ---------------- arm ----------------
    R1 = Ry(-th1) @ Rx(90)
    R2 = Ry(-th2) @ Rx(90)
    add("lower-shank", f"{PR}/lower_shank.step", "printed", pla, C["accent"], R1, at(S, G.Y["lower"][1]))
    add("lever-pulley", f"{PR}/lever_pulley.step", "printed", pla, C["accent"], Ry(-th2) @ Rx(-90), at(S, G.Y["lever"][0]))
    add("pleuel", f"{PR}/pleuel.step", "printed", pla, C["structure"], R1, at(L, G.Y["pleuel"][1]))
    add("upper-shank", f"{PR}/upper_shank.step", "printed", pla, C["structure"], R2, at(E, G.Y["upper"][1]))
    # bearings: flange face on the part face, body inward
    add("lower-bearing-1", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(90), at(S, G.Y["pulley_l"][0]))
    add("lower-bearing-2", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(-90), at(S, G.Y["lower"][1]))
    add("lever-bearing-1", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(90), at(S, G.Y["lever"][0]))
    add("lever-bearing-2", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(-90), at(S, G.Y["lever"][1]))
    add("elbow-bearing-1", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(90), at(E, G.Y["upper"][0]))
    add("elbow-bearing-2", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(-90), at(E, G.Y["upper"][1]))
    add("pleuel-bearing-l", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(-90), at(L, G.Y["pleuel"][1]))
    add("pleuel-bearing-pu", f"{MD}/f624zz.step", "bought", "f624zz", C["metal"], Rx(-90), at(PU, G.Y["pleuel"][1]))
    allow += [["lower-bearing-1", "lower-shank", "F624 press fit"], ["lower-bearing-2", "lower-shank", "F624 press fit"],
              ["lever-bearing-1", "lever-pulley", "F624 press fit"], ["lever-bearing-2", "lever-pulley", "F624 press fit"],
              ["elbow-bearing-1", "upper-shank", "F624 press fit"], ["elbow-bearing-2", "upper-shank", "F624 press fit"],
              ["pleuel-bearing-l", "pleuel", "F624 press fit"], ["pleuel-bearing-pu", "pleuel", "F624 press fit"],
              ["spacer-ls", "lower-shank", "race tube inside the hub bore"]]
    # elbow bolt (head on the lower shank's -y face), washers, nut
    add("e-bolt", f"{MD}/m4x30-shcs.step", "bought", "m3-m4-kit", C["fastener"], Rx(90), at(E, G.Y["lower"][0]))
    add("e-washer-1", f"{PR}/race_washer.step", "printed", pla, C["structure"], Rx(-90), at(E, G.Y["lower"][1]))
    add("e-washer-2", f"{PR}/race_washer.step", "printed", pla, C["structure"], Rx(-90), at(E, G.Y["upper"][1]))
    add("e-nut", f"{MD}/m4-nut.step", "bought", "m3-m4-kit", C["fastener"], Rx(-90), at(E, G.Y["upper"][1] + 1.0))
    for a in ("lower-shank", "e-washer-1", "e-washer-2", "e-nut", "elbow-bearing-1", "elbow-bearing-2"):
        allow.append(["e-bolt", a, "bolt snug in the lower shank / through washers, bearings, nut"])
    # L pin (head counterbored in the lever pulley), washers, nut
    add("l-bolt", f"{MD}/m4x20-shcs.step", "bought", "m3-m4-kit", C["fastener"], Rx(-90), at(L, G.Y["lever"][1] - 4.4))
    add("l-washer-1", f"{PR}/race_washer.step", "printed", pla, C["structure"], Rx(-90), at(L, G.Y["pleuel"][1]))
    add("l-washer-2", f"{PR}/race_washer.step", "printed", pla, C["structure"], Rx(-90), at(L, G.Y["pleuel"][1] - 6.0))
    add("l-nut", f"{MD}/m4-nut.step", "bought", "m3-m4-kit", C["fastener"], Rx(90), at(L, G.Y["pleuel"][1] - 6.0))
    for a in ("lever-pulley", "l-washer-1", "l-washer-2", "l-nut", "pleuel-bearing-l"):
        allow.append(["l-bolt", a, "crank pin snug in the lever pulley / through washers, bearing, nut"])
    # PU pin (head on the pleuel side), washer, race spacer, nut trapped in the upper shank
    # M4 x 20 ends flush with the trapped nut (full 3.2 mm engagement); an x25 reached the lower shank at full stretch
    add("pu-bolt", f"{MD}/m4x20-shcs.step", "bought", "m3-m4-kit", C["fastener"], Rx(-90), at(PU, G.Y["lever"][0]))
    add("pu-washer", f"{PR}/race_washer.step", "printed", pla, C["structure"], Rx(-90), at(PU, G.Y["pleuel"][1]))
    add("spacer-pu", f"{PR}/spacer_pu.step", "printed", pla, C["structure"], Rx(-90), at(PU, G.Y["upper"][1]))
    add("pu-nut", f"{MD}/m4-nut.step", "bought", "m3-m4-kit", C["fastener"], Rx(-90), at(PU, G.Y["upper"][0]))
    for a in ("upper-shank", "pu-washer", "spacer-pu", "pu-nut", "pleuel-bearing-pu"):
        allow.append(["pu-bolt", a, "pin snug in the upper shank / through washer, bearing, spacer, nut"])
    allow += [["pu-nut", "upper-shank", "nut in its trap"]]
    # wrist servo (spline on W pointing +y, body toward E) + horn
    Rw = Ry(-th2 - 180) @ Rx(-90)
    wy = G.WRIST_SERVO_TAB_Y + 7.5
    add("wrist-servo", f"{MD}/mg996r-servo.step", "bought", "mg996r-servo", C["servo"], Rw, at(W, wy))
    add("wrist-horn", f"{MD}/mg996r-horn.step", "bought", "mg996r-servo", C["servo"], Rw, at(W, wy))
    allow += [["wrist-servo", "upper-shank", "servo tabs screwed on the frame, body in the window"],
              ["wrist-horn", "wrist-servo", "horn on the spline"]]
    # gripper frame
    g = np.array([math.cos(math.radians(wr)), 0, math.sin(math.radians(wr))])
    h = np.array([-math.sin(math.radians(wr)), 0, math.cos(math.radians(wr))])
    GS, GH = G.GRIP_SERVO_G, G.GEAR_M * G.GEAR_T / 2
    add("gripper-base", f"{PR}/gripper_base.step", "printed", pla, C["structure"], cols(g, h, -yv), at(W, G.GRIP_PLATE_Y[1]))
    sa = W + GS * g - GH * h
    sb = W + GS * g + GH * h
    Rgs = cols(-g, np.cross(yv, g), -yv)
    add("gripper-servo", f"{MD}/mg996r-servo.step", "bought", "mg996r-servo", C["servo"], Rgs, at(sa, G.GRIP_PLATE_Y[0] - 7.5))
    add("gripper-horn", f"{MD}/mg996r-horn.step", "bought", "mg996r-servo", C["servo"], Rgs, at(sa, G.GRIP_PLATE_Y[0] - 7.5))
    R0 = cols(g, -h, yv)
    add("finger-a", f"{PR}/finger_a.step", "printed", pla, C["accent"], R0 @ Rz(grip), at(sa, G.FINGER_Y[0]))
    add("finger-b", f"{PR}/finger_b.step", "printed", pla, C["accent"], R0 @ Rz(-grip), at(sb, G.FINGER_Y[0]))
    add("grip-pivot", f"{MD}/m3x30-shcs.step", "bought", "m3-m4-kit", C["fastener"], Rx(-90), at(sb, G.GRIP_PLATE_Y[1]))
    add("grip-pivot-nut", f"{MD}/m3-nut.step", "bought", "m3-m4-kit", C["fastener"], Rx(90), at(sb, G.FINGER_Y[0] - 0.2))
    allow += [["gripper-base", "wrist-horn", "plate screwed to the horn"],
              ["gripper-servo", "gripper-base", "servo tabs screwed on the plate, body in the window"],
              ["gripper-horn", "gripper-servo", "horn on the spline"], ["finger-a", "gripper-horn", "gear A screwed to the horn"],
              ["finger-a", "finger-b", "1:1 spur gears in mesh"],
              ["grip-pivot", "gripper-base", "pivot bolt snug in the boss"], ["grip-pivot", "finger-b", "finger B turns on the bolt"],
              ["grip-pivot", "grip-pivot-nut", "thread"]]
    ids = {p["id"] for p in parts}
    allow = [[a, b] for a, b, *_ in allow if a in ids and b in ids]
    return parts, allow, {"S": S, "E": E, "W": W, "L": L, "PU": PU}


def write(path, pose, note):
    parts, allow, pts = build(pose)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {"min_clearance_mm": 0.5, "pose": pose, "note": note, "parts": parts, "allow_contact": allow}
    path.write_text(yaml.safe_dump(doc, sort_keys=False, width=140))
    tip = pts["W"] + G.TOOL_DOWN * np.array([math.cos(math.radians(pose["wr"])), 0, math.sin(math.radians(pose["wr"]))])
    print(path.relative_to(HERE.parent.parent), len(parts), "parts; W", pts["W"].round(1), "tip", tip.round(1))


POSES = {
    None: ({"yaw": 0, "th1": 90, "th2": 0, "wr": -90, "grip": 15}, "home / rest pose: lower shank vertical, upper level, gripper down"),
    "reach-table": ({"yaw": 0, "th1": 25, "th2": -23, "wr": -90, "grip": 25}, "gripper down, fingertips 15 mm above the table, near max reach"),
    "folded-high": ({"yaw": 0, "th1": 135, "th2": 55, "wr": -30, "grip": 0},
                    "shoulder back, upper shank raised; gripper tilted forward (gripper-down needs th2 <= 30)"),
    "stretched": ({"yaw": 0, "th1": 30, "th2": 0, "wr": 0, "grip": 15}, "arm stretched forward, gripper horizontal"),
    "yaw-limit": ({"yaw": 150, "th1": 60, "th2": -20, "wr": -90, "grip": 15}, "base at +150 deg"),
}
if __name__ == "__main__":
    for name, (pose, note) in POSES.items():
        write(HERE / ("assembly.yaml" if name is None else f"poses/{name}/assembly.yaml"), pose, note)
