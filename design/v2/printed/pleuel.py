"""Pleuel (push rod) L -> PU, parallel to the lower shank, closing the elbow parallelogram.
Printed flat, the world y = 13 face (toward the lever pulley) on the bed, as modelled.

Local frame: origin on L, +x toward PU (150 mm, along u1), +y in-plane, +z = world -y
(bed z = 0 is world y = 13, top z = 8 is y = 5). One F624 per end, flange on the bed face;
the remaining 3 mm is a Ø10 hole for the M4 washer + nut (L) or the race spacer (PU).
Assembly: rotation [90, -th1, 0] about L, position (L_x, 13, L_z).
"""
from build123d import (Align, BuildPart, BuildSketch, Circle, Cylinder, Locations, Mode, SlotCenterToCenter,
                       extrude, make_hull)

from lib import BRG_D, BRG_W, FLANGE_D, FLANGE_T, G, save

T = G.Y["pleuel"][1] - G.Y["pleuel"][0]      # 8
LEN = G.L1                                   # parallelogram: equal to the lower shank
END_R = 9.5                                  # F624 Ø13.1 pocket + 3 mm wall (rules §4)
MID_HALF = 6.0                               # beam half-depth

with BuildPart() as p:
    with BuildSketch():
        with BuildSketch(mode=Mode.PRIVATE) as s:
            Circle(END_R)
            with Locations((LEN, 0)):
                Circle(END_R)
        make_hull(s.edges())
    extrude(amount=T)
    with BuildSketch():                                   # lightening slot
        with Locations((LEN / 2, 0)):
            SlotCenterToCenter(LEN - 2 * END_R - 16, 6.0)
    extrude(amount=T, mode=Mode.SUBTRACT)
    for x in (0.0, LEN):
        with Locations((x, 0, 0)):
            Cylinder(BRG_D / 2, BRG_W, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
            Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
            Cylinder(5.0, T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)   # Ø10: washer + nut / spacer

part = p.part
save(part, "pleuel")
print("pleuel", part.bounding_box().size, round(part.volume / 1000, 1), "cm3")
