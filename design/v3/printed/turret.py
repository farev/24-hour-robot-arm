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
MOTOR_CB = (6.5, 3.0)
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
    f = teardrop_pts if tear else (lambda x, y, rr: circle_pts(x, y, rr, 24))
    return hull_pts(f(c[0] - half * u[0], c[1] - half * u[1], r) + f(c[0] + half * u[0], c[1] + half * u[1], r))


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
        with BuildSketch(pl):
            polygon(teardrop_pts(*S, M4_SNUG / 2))
        extrude(amount=d, mode=Mode.SUBTRACT)
        with BuildSketch(pl):
            polygon(slot_pts(I, u_i, ISLOT, M4_SNUG / 2))
        extrude(amount=d, mode=Mode.SUBTRACT)
    pl, d = on_y(TL[0], TL[0] + M4_CB[1])
    for c, half in ((S, 0.0), (I, ISLOT)):
        with BuildSketch(pl):
            polygon(slot_pts(c, u_i, half, M4_CB[0] / 2))
        extrude(amount=d, mode=Mode.SUBTRACT)
    nut = hex_prism(*M4_NUT).rotate(Axis.Z, 30).rotate(Axis.X, 90)       # along -y, a vertex up
    p.part = p.part - nut.moved(Pos(S[0], TR[1], S[1]))
    pl, d = on_y(TR[1] - M4_NUT[1], TR[1])                               # I nut: slot as wide as the nut corners
    with BuildSketch(pl):
        polygon(slot_pts(I, u_i, ISLOT, M4_NUT[0] / math.sqrt(3) + 0.1))
    extrude(amount=d, mode=Mode.SUBTRACT)
    # centre bolt clearance and the yaw pulley screw nut traps (as v2)
    Cylinder(M4_CB[0] / 2 + 0.2, DECK_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    scr = [(32 * math.cos(math.radians(t)), 32 * math.sin(math.radians(t))) for t in (45, 135, 225, 315)]
    with Locations(*[(x, y, 0) for x, y in scr]):
        Cylinder(M3_CLEAR / 2, DECK_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    for x, y in scr:
        p.part = p.part - hex_prism(M3_NUT[0], DECK_NUT_DEPTH).moved(Pos(x, y, DECK_T - DECK_NUT_DEPTH))

part = p.part
save(part, "turret")
bb = part.bounding_box()
print("turret", bb.min, bb.max, round(part.volume / 1000, 1), "cm3")
