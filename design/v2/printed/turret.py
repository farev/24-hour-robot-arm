"""Turret: deck + left and right motor towers in one print (the shoulder axle holes are coaxial by
construction). Printed deck down, towers up, as modelled; horizontal holes get 45 deg teardrop roofs.

Frame: the world frame at yaw 0 shifted down so the deck underside is z = 0 (world z = 62.5).
Assembly: rotation [0, 0, yaw], position (0, 0, 62.5).
Shoulder motor on the left tower's -y face, elbow motor on the right tower's +y face, both at C_ARM
from S along 195 deg, slotted +-3 mm along the belt for tension.
"""
import math

from build123d import (Align, Axis, BuildPart, BuildSketch, Circle, Cylinder, Locations, Mode, Plane, Pos,
                       Rectangle, RectangleRounded, Rot, extrude)

from lib import (G, M3_CLEAR, M3_NUT, M4_CB, M4_NUT, M4_SNUG, circle_pts, dims, hex_prism, hull_pts, polygon,
                 save, teardrop_pts)

Z0 = G.DECK_Z[0]
DECK_T = G.DECK_Z[1] - G.DECK_Z[0]          # 5
SX, SZ = G.S_X, G.S_Z - Z0                   # shoulder axis in this frame
MX, MZ = G.ARM_MOTOR[0], G.ARM_MOTOR[1] - Z0
U = (math.cos(math.radians(G.ARM_MOTOR_DIR)), math.sin(math.radians(G.ARM_MOTOR_DIR)))
SLOT = G.TENSION_SLOT
NEMA = dims("xy42sth40-1204a")
PITCH = NEMA["hole pitch"]
PILOT_D = NEMA["pilot diameter"] + 1.0       # pilot + 1.0 so the motor slides in its slot
TL, TR = G.Y["tower_l"], G.Y["tower_r"]
DECK_NUT_DEPTH = 3.8                         # leaves a 1.2 mm floor; the M3 x 10 tip engages 2.1 of the 2.4 nut
MOTOR_CB = (6.5, 3.0)                        # M3 head counterbore in the tower inner face -> M3 x 10 into the motor
TAIL_X = -88.0                              # tower tails / deck strips reach back to here
FRONT_X = 22.0


def on_y(y0, y1):
    """XZ sketch plane (local x = world x, local y = world z) whose extrusion fills world y0..y1."""
    return Plane.XZ.offset(-y1), y1 - y0


def rounded_rect_pts(cx, cy, w, h, r, n=8):
    pts = []
    for qx, qy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        pts += circle_pts(cx + qx * (w / 2 - r), cy + qy * (h / 2 - r), r, 4 * n)
    return pts


tower_pts = hull_pts([(TAIL_X, DECK_T), (FRONT_X, DECK_T), (FRONT_X, DECK_T + 5), (TAIL_X, DECK_T + 5)]
                     + circle_pts(SX, SZ, 14.0) + rounded_rect_pts(MX, MZ, 54.0, 54.0, 6.0))

with BuildPart() as p:
    # ---- deck: round centre + rectangle under the towers + strips under the tower tails
    with BuildSketch():
        Circle(45.0)
        with Locations(((FRONT_X - 58) / 2, (TL[0] + TR[1]) / 2)):
            RectangleRounded(FRONT_X + 58, TR[1] - TL[0], 6.0)
        for y0, y1 in (TL, TR):
            with Locations(((TAIL_X - 50) / 2, (y0 + y1) / 2)):
                RectangleRounded(-50 - TAIL_X, y1 - y0, 3.0)
    extrude(amount=DECK_T)
    # ---- towers (start inside the deck so they fuse with it)
    for y0, y1 in (TL, TR):
        pl, d = on_y(y0, y1)
        with BuildSketch(pl):
            polygon(tower_pts)
        extrude(amount=d)
    # ---- motor mounts: teardrop pilot slot and 4 M3 slots along the belt direction
    for y0, y1 in (TL, TR):
        pl, d = on_y(y0, y1)
        with BuildSketch(pl):
            polygon(hull_pts(teardrop_pts(MX - SLOT * U[0], MZ - SLOT * U[1], PILOT_D / 2)
                             + teardrop_pts(MX + SLOT * U[0], MZ + SLOT * U[1], PILOT_D / 2)))
        extrude(amount=d, mode=Mode.SUBTRACT)
        inner = (y1 - MOTOR_CB[1], y1) if y0 < 0 else (y0, y0 + MOTOR_CB[1])   # inner face of this tower
        pl_cb, d_cb = on_y(*inner)
        for hx in (-PITCH / 2, PITCH / 2):
            for hz in (-PITCH / 2, PITCH / 2):
                for plane, dd, dia in ((pl, d, M3_CLEAR), (pl_cb, d_cb, MOTOR_CB[0])):
                    with BuildSketch(plane):           # teardrop slots: 45 deg roofs, no support
                        polygon(hull_pts(teardrop_pts(MX + hx - SLOT * U[0], MZ + hz - SLOT * U[1], dia / 2)
                                         + teardrop_pts(MX + hx + SLOT * U[0], MZ + hz + SLOT * U[1], dia / 2)))
                    extrude(amount=dd, mode=Mode.SUBTRACT)
    # ---- shoulder axle: M4 snug through both towers, head counterbore left, nut trap right
    for y0, y1 in (TL, TR):
        pl, d = on_y(y0, y1)
        with BuildSketch(pl):
            polygon(teardrop_pts(SX, SZ, M4_SNUG / 2))
        extrude(amount=d, mode=Mode.SUBTRACT)
    pl, d = on_y(TL[0], TL[0] + M4_CB[1])
    with BuildSketch(pl):
        polygon(teardrop_pts(SX, SZ, M4_CB[0] / 2))
    extrude(amount=d, mode=Mode.SUBTRACT)
    nut = hex_prism(*M4_NUT).rotate(Axis.Z, 30).rotate(Axis.X, 90)      # prism along -y, a vertex up
    p.part = p.part - nut.moved(Pos(SX, TR[1], SZ))
    # (no shoulder/elbow switches: the 1 mm pulley-to-tower gap gives a lever switch too little travel;
    #  those joints home from the rest pose, see summary.md)
    # ---- centre bolt: Ø8.4 through the deck, the M4 x 60 head seats on the yaw pulley (no thin floor);
    #      4 M3 nut traps for the yaw pulley screws
    Cylinder(M4_CB[0] / 2 + 0.2, DECK_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    scr = [(32 * math.cos(math.radians(t)), 32 * math.sin(math.radians(t))) for t in (45, 135, 225, 315)]
    with Locations(*[(x, y, 0) for x, y in scr]):
        Cylinder(M3_CLEAR / 2, DECK_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    for x, y in scr:                       # nut sits 3.8 deep so an M3 x 10 from the yaw pulley engages
        p.part = p.part - hex_prism(M3_NUT[0], DECK_NUT_DEPTH).moved(Pos(x, y, DECK_T - DECK_NUT_DEPTH))

part = p.part
save(part, "turret")
bb = part.bounding_box()
print("turret", bb.min, bb.max, round(part.volume / 1000, 1), "cm3")
