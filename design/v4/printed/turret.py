"""v3 turret: deck + two towers in one print. Both towers carry the shoulder axle S and the slotted
intermediate axle I (stage-2 tension); the right tower carries the shoulder motor (stage 1, slotted).
Printed deck down, towers up, as modelled; horizontal holes have teardrop roofs.

Frame: world at yaw 0 shifted down so the deck underside is z = 0 (world z = 62.5).
Assembly: rotation [0, 0, yaw], position (0, 0, 62.5).
"""
import math

from build123d import Align, Axis, BuildPart, BuildSketch, Circle, Cylinder, Locations, Mode, Plane, Pos, RectangleRounded, extrude

from lib import (G, M3_CLEAR, M3_NUT, M4_CB, M4_NUT, M4_SNUG, circle_pts, dims, hex_prism, hull_pts, polygon, save,
                 teardrop_pts)

Z0 = G.DECK_Z[0]
DECK_T = G.DECK_Z[1] - G.DECK_Z[0]
S = (G.S_X, G.S_Z - Z0)
I = (G.I_PT[0], G.I_PT[1] - Z0)
M = (G.SH_MOTOR[0], G.SH_MOTOR[1] - Z0)
u_i = (math.cos(math.radians(G.I_DIR)), math.sin(math.radians(G.I_DIR)))
u_m = ((M[0] - I[0]) / G.C_SH1, (M[1] - I[1]) / G.C_SH1)
NEMA = dims("xy42sth40-1204a")
PITCH = NEMA["hole pitch"]
PILOT_D = NEMA["pilot diameter"] + 1.0
SLOT, ISLOT = G.TENSION_SLOT, G.I_SLOT
TL, TR = G.Y["tower_l"], G.Y["tower_r"]
DECK_NUT_DEPTH = 3.8
SHAFT_GROOVE = 3.0                           # yaw motor shaft tip 64 - deck underside 62.5 = 1.5, + 1.5 clearance
MOTOR_CB = (6.5, 3.5)                                         # M3 x 10 -> 4.5 mm (1.5 d) into the motor
FRONT_X = 22.0
TAIL_L = I[0] - 18.0                         # left tower: S + I only
TAIL_R = M[0] - 29.0                         # right tower: also the shoulder motor


def on_y(y0, y1):
    return Plane.XZ.offset(-y1), y1 - y0


def rr_pts(cx, cy, w, h, r, n=8):
    pts = []
    for qx, qy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        pts += circle_pts(cx + qx * (w / 2 - r), cy + qy * (h / 2 - r), r, 4 * n)
    return pts


def slot_pts(c, u, half, r, tear=True):
    """Slot along u (both towers' slots run 20 deg off horizontal). With tear, the roof is a 45 deg gable over the
    whole slot (design review 2026-11-06: a per-end teardrop hull left a 70 deg sloped roof)."""
    ends = [(c[0] - half * u[0], c[1] - half * u[1]), (c[0] + half * u[0], c[1] + half * u[1])]
    pts = circle_pts(*ends[0], r, 24) + circle_pts(*ends[1], r, 24)
    if tear:
        b1 = max(y - x for x, y in ends) + r * math.sqrt(2)          # 45 deg line y = x + b1 over the slot
        b2 = max(y + x for x, y in ends) + r * math.sqrt(2)          # 135 deg line y = -x + b2
        pts.append(((b2 - b1) / 2, (b1 + b2) / 2))
    return hull_pts(pts)


foot = lambda x0: [(x0, DECK_T), (FRONT_X, DECK_T), (FRONT_X, DECK_T + 5), (x0, DECK_T + 5)]
left_pts = hull_pts(foot(TAIL_L) + circle_pts(*S, 14.0) + circle_pts(*I, 16.0))
right_pts = hull_pts(foot(TAIL_R) + circle_pts(*S, 14.0) + circle_pts(*I, 16.0) + rr_pts(*M, 54.0, 54.0, 6.0))

with BuildPart() as p:
    with BuildSketch():
        Circle(45.0)
        with Locations(((FRONT_X - 58) / 2, (TL[0] + TR[1]) / 2)):
            RectangleRounded(FRONT_X + 58, TR[1] - TL[0], 6.0)
        for (y0, y1), tail in ((TL, TAIL_L), (TR, TAIL_R)):
            with Locations(((tail - 50) / 2, (y0 + y1) / 2)):
                RectangleRounded(-50 - tail, y1 - y0, 3.0)
    extrude(amount=DECK_T)
    for (y0, y1), pts in ((TL, left_pts), (TR, right_pts)):
        pl, d = on_y(y0, y1)
        with BuildSketch(pl):
            polygon(pts)
        extrude(amount=d)
    # yaw motor shaft clearance (user redline 2026-11-05): the 40 mm yaw motor's shaft tip (z 64) is above the
    # deck underside (z 62.5), so the deck tail would hit it as the turret yaws. A ring groove on the underside
    # along the shaft's path: r = C_YAW +- (3 tension travel + 2.5 shaft radius + 1), 3 mm deep (2 mm left).
    with BuildSketch():
        Circle(G.C_YAW + G.TENSION_SLOT + 2.5 + 1.0)
        Circle(G.C_YAW - G.TENSION_SLOT - 2.5 - 1.0, mode=Mode.SUBTRACT)
    extrude(amount=SHAFT_GROOVE, mode=Mode.SUBTRACT)
    # shoulder motor on the right tower: teardrop pilot slot, M3 slots + head counterbores on the inner face
    pl, d = on_y(*TR)
    with BuildSketch(pl):
        polygon(slot_pts(M, u_m, SLOT, PILOT_D / 2))
    extrude(amount=d, mode=Mode.SUBTRACT)
    pl_cb, d_cb = on_y(TR[0], TR[0] + MOTOR_CB[1])
    for hx in (-PITCH / 2, PITCH / 2):
        for hz in (-PITCH / 2, PITCH / 2):
            c = (M[0] + hx, M[1] + hz)
            for plane, dd, dia in ((pl, d, M3_CLEAR), (pl_cb, d_cb, MOTOR_CB[0])):
                with BuildSketch(plane):
                    polygon(slot_pts(c, u_m, SLOT, dia / 2))
                extrude(amount=dd, mode=Mode.SUBTRACT)
    # S axle (round) and I axle (slotted along S -> I) through both towers; heads counterbored left, nuts trapped right
    for y0, y1 in (TL, TR):
        pl, d = on_y(y0, y1)
        with BuildSketch(pl):                                  # horizontal holes print small: +0.1 (rules §1)
            polygon(teardrop_pts(*S, (M4_SNUG + 0.1) / 2))
        extrude(amount=d, mode=Mode.SUBTRACT)
        with BuildSketch(pl):
            polygon(slot_pts(I, u_i, ISLOT, (M4_SNUG + 0.1) / 2))
        extrude(amount=d, mode=Mode.SUBTRACT)
    pl, d = on_y(TL[0], TL[0] + M4_CB[1])
    for c, half in ((S, 0.0), (I, ISLOT)):
        with BuildSketch(pl):
            polygon(slot_pts(c, u_i, half, M4_CB[0] / 2))
        extrude(amount=d, mode=Mode.SUBTRACT)
    nut = hex_prism(*M4_NUT).rotate(Axis.Z, 30).rotate(Axis.X, 90)       # along -y, a vertex up
    p.part = p.part - nut.moved(Pos(S[0], TR[1], S[1]))
    pl, d = on_y(TR[1] - M4_NUT[1], TR[1])                               # I nut: slot across flats + 0.35, so the
    with BuildSketch(pl):                                                # flats bear on the sides (no spinning)
        polygon(slot_pts(I, u_i, ISLOT, M4_NUT[0] / 2 + 0.05))
    extrude(amount=d, mode=Mode.SUBTRACT)
    # centre bolt clearance and the yaw pulley screw nut traps (as v2)
    Cylinder(M4_CB[0] / 2 + 0.2, DECK_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    scr = [(G.DECK_SCREW_R * math.cos(math.radians(t)), G.DECK_SCREW_R * math.sin(math.radians(t))) for t in G.DECK_SCREW_ANG]
    with Locations(*[(x, y, 0) for x, y in scr]):
        Cylinder(M3_CLEAR / 2, DECK_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    for x, y in scr:
        p.part = p.part - hex_prism(M3_NUT[0], DECK_NUT_DEPTH).moved(Pos(x, y, DECK_T - DECK_NUT_DEPTH))

part = p.part
save(part, "turret")
bb = part.bounding_box()
print("turret", bb.min, bb.max, round(part.volume / 1000, 1), "cm3")
