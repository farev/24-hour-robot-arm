"""Upper shank: elbow hub E (two F624), rear arm to PU (pleuel pin), and the wrist servo frame at W.
Printed flat, the world y = +4 face (where the wrist servo tabs sit) on the bed, as modelled.

Local frame: origin on E, +x along u2 to the wrist W (150), PU at x = -40, +y in-plane,
+z = world -y (bed z = 0 is world y = 4, top z = 10 is y = -6).
Assembly: rotation [90, -th2, 0] about E, position (E_x, 4, E_z).
The MG996R body passes through the frame window, spline on W pointing world +y, body toward E.
"""
from build123d import (Align, BuildPart, BuildSketch, Circle, Cylinder, Locations, Mode, Rectangle,
                       RectangleRounded, SlotCenterToCenter, extrude, make_hull)

from lib import BRG_D, BRG_W, FLANGE_D, FLANGE_T, G, M3_CLEAR, M3_NUT, M4_NUT, M4_SNUG, dims, hex_prism, save

T = G.Y["upper"][1] - G.Y["upper"][0]        # 10
L2, LEV = G.L2, G.LEVER
S = dims("mg996r-servo")
SHAFT_OFF = S["shaft offset from body end"]
BODY_L, BODY_W = S["body length"], S["body width"]
HOLE_X, HOLE_Y = S["tab hole spacing x"], S["tab hole spacing y"]
CLR = 0.4                                     # window clearance around the servo body per side (rules §1)
body_c = L2 - (BODY_L / 2 - SHAFT_OFF)        # body centre along x (body runs from W back toward E)
WIN_X = (L2 - (BODY_L - SHAFT_OFF) - CLR, L2 + SHAFT_OFF + CLR)
WIN_HALF = BODY_W / 2 + CLR
FRAME_X = (110.0, 170.0)
FRAME_HALF = 16.0
E_R, PU_R = 11.0, 8.0

with BuildPart() as p:
    with BuildSketch():
        with BuildSketch(mode=Mode.PRIVATE) as rear:
            Circle(E_R)
            with Locations((-LEV, 0)):
                Circle(PU_R)
        make_hull(rear.edges())
        with BuildSketch(mode=Mode.PRIVATE) as beam:
            Circle(E_R)
            with Locations((FRAME_X[0] + 4, 0)):
                Rectangle(8, 2 * FRAME_HALF - 4)
        make_hull(beam.edges())
        with Locations(((FRAME_X[0] + FRAME_X[1]) / 2, 0)):
            RectangleRounded(FRAME_X[1] - FRAME_X[0], 2 * FRAME_HALF, 4.0)
    extrude(amount=T)
    # servo window
    with BuildSketch():
        with Locations(((WIN_X[0] + WIN_X[1]) / 2, 0)):
            RectangleRounded(WIN_X[1] - WIN_X[0], 2 * WIN_HALF, 1.0)
    extrude(amount=T, mode=Mode.SUBTRACT)
    # beam lightening slot
    with BuildSketch():
        with Locations(((22 + 98) / 2, 0)):
            SlotCenterToCenter(98 - 22, 8.0)
    extrude(amount=T, mode=Mode.SUBTRACT)
    # servo tab screws: the servo's own ~M3 self-tapping screws into Ø2.6 pilots (assembled once, rules §2);
    # hole centre is only 4 mm from the window, too close for a nut trap
    tabs = [(body_c + sx * HOLE_X / 2, sy * HOLE_Y / 2) for sx in (-1, 1) for sy in (-1, 1)]
    with Locations(*[(x, y, 0) for x, y in tabs]):
        Cylinder(2.6 / 2, T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    # E: two F624 back to back, flange counterbores on both faces
    Cylinder(BRG_D / 2, T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    with Locations((0, 0, T)):
        Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
    # PU: M4 snug, nut trap on the top face (world y = -6)
    with Locations((-LEV, 0, 0)):
        Cylinder(M4_SNUG / 2, T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    p.part = p.part - hex_prism(*M4_NUT).moved(Locations((-LEV, 0, T - M4_NUT[1])).locations[0])

part = p.part
save(part, "upper_shank")
print("upper_shank", part.bounding_box().size, round(part.volume / 1000, 1), "cm3", "tabs", tabs)
