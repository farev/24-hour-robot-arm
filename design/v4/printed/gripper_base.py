"""v4 gripper base (parallel-jaw gripper): plate screwed to the wrist pulley's gripper face, holds the
gripper MG996R (tabs on the plate's +y face, body through the window toward -y, spline pointing +y),
the boss for crank gear B's M3 pivot and the two idler-link pivot bosses. Printed flat, -y face on the bed.

Frame (gripper frame): origin on the wrist axis W, x = g (toward the fingertips), y = -h, z = world +y;
bed z = 0 is world y = -22, top z = 5 is y = -17 (against the wrist pulley).
Assembly: columns (g, -h, +y), origin at (W_x, -22, W_z).
"""
import math

from build123d import (Align, BuildPart, BuildSketch, Circle, Cylinder, Locations, Mode, RectangleRounded, extrude,
                       make_hull)

from lib import G, M3_CB, M3_CLEAR, dims, save

Y0, Y1 = G.Y["grip_plate"]                   # -22 .. -17
T = Y1 - Y0
S = dims("mg996r-servo")
SHAFT_OFF, BODY_L, BODY_W = S["shaft offset from body end"], S["body length"], S["body width"]
HOLE_X, HOLE_Y = S["tab hole spacing x"], S["tab hole spacing y"]
GS = G.GRIP_SERVO_G
YS = G.GEAR_M * G.GEAR_T / 2                 # servo spline at h = -12 -> local y = +12
YB = -YS                                     # finger B pivot at h = +12 -> local y = -12
CLR = 0.4
if G.GRIP_SERVO_BODY_FWD:                    # body runs from the spline away from W (toward the jaws)
    WIN_G = (GS - SHAFT_OFF - CLR, GS + (BODY_L - SHAFT_OFF) + CLR)
    body_c = GS + (BODY_L / 2 - SHAFT_OFF)
else:
    WIN_G = (GS - (BODY_L - SHAFT_OFF) - CLR, GS + SHAFT_OFF + CLR)
    body_c = GS - (BODY_L / 2 - SHAFT_OFF)
WIN_Y = (YS - BODY_W / 2 - CLR, YS + BODY_W / 2 + CLR)
PLATE_END = body_c + HOLE_X / 2 + 6.0        # plate reaches past the far tab holes
FINGER_B_BED = G.FINGER_Y0 + 0.6             # finger B sits 0.6 above the horn plane
BOSS_H = (FINGER_B_BED - 0.5) - Y1           # boss from the plate top to 0.5 below finger B
SCREW_R = G.WRIST_SCREW_R                    # matches wrist_pulley.py pilots
_o = (G.IDLER_D * math.cos(math.radians(G.IDLER_DIR)), G.IDLER_D * math.sin(math.radians(G.IDLER_DIR)))   # (g, h), jaw A
IDL_G = GS + _o[0]                           # idler base pivots beside each gear, outward (parallelogram offset)
IDL_Y = YS - _o[1]                           # local y = -h: A pivot at h = -12 + o_h -> y = 12 - o_h

with BuildPart() as p:
    with BuildSketch():
        with BuildSketch(mode=Mode.PRIVATE) as o:
            Circle(22.0)
            with Locations(((12 + PLATE_END) / 2, (-22 + 28) / 2)):
                RectangleRounded(PLATE_END - 12, 50, 6.0)
            with Locations((IDL_G, IDL_Y), (IDL_G, -IDL_Y)):
                Circle(7.0)
        make_hull(o.edges())
    extrude(amount=T)
    with Locations((GS, YB, T), (IDL_G, IDL_Y, T), (IDL_G, -IDL_Y, T)):   # gear B pivot + two idler pivot bosses
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
    with Locations((GS, YB, 0), (IDL_G, IDL_Y, 0), (IDL_G, -IDL_Y, 0)):   # pivots: M3 snug, bolts from the bed face
        Cylinder(3.2 / 2, T + BOSS_H, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        # head counterbore (M3_CB) so the M3 x 30 reaches 1.9 mm past its nut on top of gear B / the idler
        Cylinder(M3_CB[0] / 2, M3_CB[1], align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

part = p.part
save(part, "gripper_base")
print("gripper_base", part.bounding_box().size, "boss h", round(BOSS_H, 2))
