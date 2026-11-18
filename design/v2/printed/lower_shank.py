"""Lower shank with its 140T GT2 shoulder pulley (one print). Printed flat, +y face (toward the upper
shank) on the bed, as modelled.

Local frame: origin on the shoulder axis S, +x along the shank to the elbow E (150 mm), +y = in-plane
(world up at th1 = 0), +z = thickness = world -y (bed z = 0 is world y = -7, top z = 18 is y = -25).
Assembly: rotation [90, -th1, 0] about S, position (S_X, -7, S_Z).
"""
import math

from build123d import (Align, BuildPart, BuildSketch, Circle, Cone, Cylinder, Location, Locations, Mode,
                       SlotCenterToCenter, extrude, make_hull)

from lib import BRG_D, BRG_W, FLANGE_D, FLANGE_T, G, M4_SNUG, gt2_outline, save

# --- numbers ----------------------------------------------------------------------------------
PLATE_T = G.Y["lower"][1] - G.Y["lower"][0]                  # 10: shank plate (world y -7..-17)
H = G.Y["lower"][1] - G.Y["pulley_l"][0]                     # 18: total thickness at S (to y -25)
TEETH_Z = (PLATE_T, PLATE_T + 6.5)                           # teeth zone z 10..16.5 (6 mm belt)
DISC_R = 46.0                                                # plate disc at S = inner belt flange
L1 = G.L1
END_R = 12.0                                                 # elbow boss radius (wall 4 around the M4 bolt + washer)
ROOT_R = 30.0                                                # shank half-depth where it leaves the disc

with BuildPart() as p:
    # plate: disc at S + tapered beam to E (hull of two circles)
    with BuildSketch():
        Circle(DISC_R)
        with BuildSketch(mode=Mode.PRIVATE) as beam:
            Circle(ROOT_R)
            with Locations((L1, 0)):
                Circle(END_R)
        make_hull(beam.edges())
    extrude(amount=PLATE_T)
    # 140T teeth zone on the disc, then a 45 deg cone flange (prints without support)
    teeth, od = gt2_outline(G.ARM_T)
    extrude(teeth.moved(Location((0, 0, TEETH_Z[0]))), amount=TEETH_Z[1] - TEETH_Z[0])
    root_r = od / 2 - 0.75
    with Locations((0, 0, TEETH_Z[1])):
        Cone(root_r, root_r + (H - TEETH_Z[1]), H - TEETH_Z[1], align=(Align.CENTER, Align.CENTER, Align.MIN))
    # lightening windows through the disc, between the hub and the teeth ring
    for a in (40, 112, 184, 256, 328):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        with BuildSketch():
            with Locations((25 * c, 25 * s)):
                SlotCenterToCenter(12.0, 9.0, rotation=a + 90)
        extrude(amount=H, mode=Mode.SUBTRACT)
    # beam lightening slot
    with BuildSketch():
        with Locations(((60 + 122) / 2, 0)):
            SlotCenterToCenter(122 - 60, 12.0)
    extrude(amount=PLATE_T, mode=Mode.SUBTRACT)
    # S hub: F624 press pockets with flange counterbores on both faces, Ø7.6 through for the Ø7 race tube
    Cylinder(3.8, H, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    Cylinder(BRG_D / 2, BRG_W, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    with Locations((0, 0, H)):
        Cylinder(BRG_D / 2, BRG_W, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
        Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
    # E: M4 snug hole, the elbow bolt is clamped here (head on the z = 10 face)
    with Locations((L1, 0, 0)):
        Cylinder(M4_SNUG / 2, PLATE_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

part = p.part
save(part, "lower_shank")
print("lower_shank", part.bounding_box().size, round(part.volume / 1000, 1), "cm3")
