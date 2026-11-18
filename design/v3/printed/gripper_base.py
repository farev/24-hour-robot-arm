"""v3 gripper base: plate screwed to the wrist pulley's gripper face, holds the gripper MG996R (tabs on the
plate's +y face, body through the window toward -y, spline pointing +y) and the boss for finger B's M3
pivot. Printed flat, the -y face on the bed, as modelled.

Frame (gripper frame): origin on the wrist axis W, x = g (toward the fingertips), y = -h, z = world +y;
bed z = 0 is world y = -22, top z = 5 is y = -17 (against the wrist pulley).
Assembly: columns (g, -h, +y), origin at (W_x, -22, W_z).
"""
import math

from build123d import (Align, BuildPart, BuildSketch, Circle, Cylinder, Locations, Mode, RectangleRounded, extrude,
                       make_hull)

from lib import G, M3_CLEAR, dims, save

Y0, Y1 = G.Y["grip_plate"]                   # -22 .. -17
T = Y1 - Y0
S = dims("mg996r-servo")
SHAFT_OFF, BODY_L, BODY_W = S["shaft offset from body end"], S["body length"], S["body width"]
HOLE_X, HOLE_Y = S["tab hole spacing x"], S["tab hole spacing y"]
GS = G.GRIP_SERVO_G
YS = G.GEAR_M * G.GEAR_T / 2                 # servo spline at h = -12 -> local y = +12
YB = -YS                                     # finger B pivot at h = +12 -> local y = -12
CLR = 0.4
WIN_G = (GS - (BODY_L - SHAFT_OFF) - CLR, GS + SHAFT_OFF + CLR)
WIN_Y = (YS - BODY_W / 2 - CLR, YS + BODY_W / 2 + CLR)
body_c = GS - (BODY_L / 2 - SHAFT_OFF)
FINGER_B_BED = G.FINGER_Y0 + 0.6             # finger B sits 0.6 above the horn plane
BOSS_H = (FINGER_B_BED - 0.5) - Y1           # boss from the plate top to 0.5 below finger B
SCREW_R = 15.0                               # matches wrist_pulley.py pilots

with BuildPart() as p:
    with BuildSketch():
        with BuildSketch(mode=Mode.PRIVATE) as o:
            Circle(22.0)
            with Locations(((12 + 70) / 2, (-22 + 28) / 2)):
                RectangleRounded(70 - 12, 50, 6.0)
        make_hull(o.edges())
    extrude(amount=T)
    with Locations((GS, YB, T)):                              # finger B pivot boss
        Cylinder(4.5, BOSS_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    with BuildSketch():                                       # servo window
        with Locations(((WIN_G[0] + WIN_G[1]) / 2, (WIN_Y[0] + WIN_Y[1]) / 2)):
            RectangleRounded(WIN_G[1] - WIN_G[0], WIN_Y[1] - WIN_Y[0], 1.0)
    extrude(amount=T, mode=Mode.SUBTRACT)
    with Locations(*[(body_c + sx * HOLE_X / 2, YS + sy * HOLE_Y / 2, 0) for sx in (-1, 1) for sy in (-1, 1)]):
        Cylinder(2.6 / 2, T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)   # servo screws
    Cylinder(5.0, T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)          # wrist axle nut
    with Locations(*[(SCREW_R * math.cos(math.radians(a)), SCREW_R * math.sin(math.radians(a)), 0)
                     for a in (45, 135, 225, 315)]):
        Cylinder(M3_CLEAR / 2, T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    with Locations((GS, YB, 0)):                              # finger B pivot, M3 snug
        Cylinder(3.2 / 2, T + BOSS_H, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

part = p.part
save(part, "gripper_base")
print("gripper_base", part.bounding_box().size, "boss h", round(BOSS_H, 2))
