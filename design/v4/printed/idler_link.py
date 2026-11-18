"""v4 gripper idler link (print 2): the second bar of each jaw's parallelogram, same length as the crank.
Base end turns on an M3 pivot in a gripper-base boss; jaw end has a boss up to the jaw plane.
Printed flat, as modelled.

Frame: origin on the base pivot, +x along the link to the jaw pin, z = world +y; bed z = 0 at y = -1.1.
"""
from build123d import Align, BuildPart, BuildSketch, Circle, Cylinder, Locations, Mode, SlotCenterToCenter, extrude, make_hull

from lib import G, save

L = G.CRANK_L
T = G.LINK_T
BOSS_H = G.PIN_BOSS_TOP - G.LINK_Y[1]

with BuildPart() as p:
    with BuildSketch():
        with BuildSketch(mode=Mode.PRIVATE) as s:
            Circle(4.5)
            with Locations((L, 0)):
                Circle(4.5)
        make_hull(s.edges())
    extrude(amount=T)
    with BuildSketch():                                         # lightening slot
        with Locations((L / 2, 0)):
            SlotCenterToCenter(L - 14, 3.0)
    extrude(amount=T, mode=Mode.SUBTRACT)
    with Locations((L, 0, T)):
        Cylinder(3.6, BOSS_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    with Locations((0, 0, 0), (L, 0, 0)):
        Cylinder(3.4 / 2, T + BOSS_H, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)   # M3 running

part = p.part
save(part, "idler_link")
print("idler_link", part.bounding_box().size)
