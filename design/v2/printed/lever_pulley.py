"""Elbow lever pulley: 140T GT2 pulley turning on the shoulder axle, with the crank pin L that drives the
pleuel (40 mm, opposite the upper shank). Printed flat, the face toward the pleuel (world y = 14) on
the bed, as modelled.

Local frame: origin on S, +x along the upper shank direction u2, L pin at x = -40, +y in-plane,
+z = world +y (bed z = 0 is world y = 14, top z = 10 is y = 24, facing the right tower).
Assembly: R = Ry(-th2) Rx(-90) about S (local z -> world +y, local y -> world -z), see build_assembly.py.
"""
import math

from build123d import (Align, BuildPart, BuildSketch, Circle, Cone, Cylinder, Location, Locations, Mode,
                       SlotCenterToCenter, extrude)

from lib import BRG_D, BRG_W, FLANGE_D, FLANGE_T, G, M4_CB, M4_SNUG, gt2_outline, save

Y0, Y1 = G.Y["lever"]                       # 14 (bed) .. 24
H = Y1 - Y0                                 # 10
DISC_R = 46.0
BELT_Z = G.BELT_Y_R - Y0                    # 6.0: belt centre above the bed
TEETH_Z = (BELT_Z - 3.25, BELT_Z + 3.25)    # 2.75 .. 9.25 (6.5 zone for the 6 mm belt)
LEVER = G.LEVER

with BuildPart() as p:
    # bed flange disc, teeth zone, top cone flange
    Cylinder(DISC_R, TEETH_Z[0], align=(Align.CENTER, Align.CENTER, Align.MIN))
    teeth, od = gt2_outline(G.ARM_T)
    extrude(teeth.moved(Location((0, 0, TEETH_Z[0]))), amount=TEETH_Z[1] - TEETH_Z[0])
    root_r = od / 2 - 0.75
    with Locations((0, 0, TEETH_Z[1])):
        Cone(root_r, root_r + (H - TEETH_Z[1]), H - TEETH_Z[1], align=(Align.CENTER, Align.CENTER, Align.MIN))
    # lightening windows, kept clear of the L pin boss at 180 deg
    for a in (0, 72, 144 + 18, 216 - 18, 288):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        with BuildSketch():
            with Locations((24 * c, 24 * s)):
                SlotCenterToCenter(10.0, 9.0, rotation=a + 90)
        extrude(amount=H, mode=Mode.SUBTRACT)
    # S: two F624 back to back (inner races meet at z = 5), flange counterbores on both faces
    Cylinder(BRG_D / 2, H, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    with Locations((0, 0, H)):
        Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
    # L crank pin: M4 snug, head counterbored in the top face (toward the tower)
    with Locations((-LEVER, 0, 0)):
        Cylinder(M4_SNUG / 2, H, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    with Locations((-LEVER, 0, H)):
        Cylinder(M4_CB[0] / 2, M4_CB[1], align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)

part = p.part
save(part, "lever_pulley")
print("lever_pulley", part.bounding_box().size, round(part.volume / 1000, 1), "cm3")
