"""Gripper base: plate screwed to the wrist servo horn, holds the gripper MG996R (tabs on its -y face,
spline toward the arm plane) and the boss for finger B's M3 pivot. Printed flat, the +y face on the bed.

Frame (gripper frame): origin on the wrist axis W, x = g (along the gripper, toward the fingertips),
y = h (across, in the arm plane), z = world -y; bed z = 0 is world y = GRIP_PLATE_Y[1].
Assembly: x -> g_hat, y -> h_hat, z -> -y_world, origin at (W_x, GRIP_PLATE_Y[1], W_z).
"""
from build123d import (Align, BuildPart, BuildSketch, Circle, Cylinder, Locations, Mode, RectangleRounded, extrude,
                       make_hull)

from lib import G, M3_CLEAR, dims, save

T = G.GRIP_PLATE_Y[1] - G.GRIP_PLATE_Y[0]        # 5
S = dims("mg996r-servo")
SHAFT_OFF, BODY_L, BODY_W = S["shaft offset from body end"], S["body length"], S["body width"]
HOLE_X, HOLE_Y = S["tab hole spacing x"], S["tab hole spacing y"]
GS, HS = G.GRIP_SERVO_G, -G.GEAR_M * G.GEAR_T / 2           # gripper servo spline at g 50, h -12
HB = -HS                                                     # finger B pivot at h +12
CLR = 0.4
WIN_G = (GS - (BODY_L - SHAFT_OFF) - CLR, GS + SHAFT_OFF + CLR)   # body runs from the spline back toward W
WIN_H = (HS - BODY_W / 2 - CLR, HS + BODY_W / 2 + CLR)
body_c = GS - (BODY_L / 2 - SHAFT_OFF)
BOSS_TOP_Y = G.FINGER_Y[1] + 0.5                             # boss ends 0.5 above finger B
BOSS_H = G.GRIP_PLATE_Y[0] - BOSS_TOP_Y                      # from the plate's -y face
HORN_SCREW_R = 7.0                                           # [est] round horn screw circle; measure the horn

with BuildPart() as p:
    with BuildSketch():
        with BuildSketch(mode=Mode.PRIVATE) as o:
            Circle(14.0)
            with Locations(((12 + 70) / 2, (-28 + 22) / 2)):
                RectangleRounded(70 - 12, 50, 6.0)
        make_hull(o.edges())
    extrude(amount=T)
    with Locations((GS, HB, T)):                              # finger B pivot boss
        Cylinder(4.5, BOSS_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # servo window
    with BuildSketch():
        with Locations(((WIN_G[0] + WIN_G[1]) / 2, (WIN_H[0] + WIN_H[1]) / 2)):
            RectangleRounded(WIN_G[1] - WIN_G[0], WIN_H[1] - WIN_H[0], 1.0)
    extrude(amount=T, mode=Mode.SUBTRACT)
    # servo tab pilots (the servo's own self-tapping screws, assembled once)
    with Locations(*[(body_c + sx * HOLE_X / 2, HS + sy * HOLE_Y / 2, 0) for sx in (-1, 1) for sy in (-1, 1)]):
        Cylinder(2.6 / 2, T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    # wrist horn: centre access hole for the spline screw + 4 horn screw holes
    Cylinder(3.5, T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)   # Ø7 access, no screw passes
    with Locations(*[(HORN_SCREW_R * c, HORN_SCREW_R * s, 0) for c, s in ((1, 0), (0, 1), (-1, 0), (0, -1))]):
        Cylinder(2.2 / 2, T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    # finger B pivot: M3 snug through plate and boss (bolt clamped; finger B turns on it)
    with Locations((GS, HB, 0)):
        Cylinder(3.2 / 2, T + BOSS_H, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

part = p.part
save(part, "gripper_base")
print("gripper_base", part.bounding_box().size, "boss h", BOSS_H)
