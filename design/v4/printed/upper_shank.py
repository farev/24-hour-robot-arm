"""v3 upper shank: elbow 140T teeth at E (driven by the elbow stepper on the lower shank), two F624 at E,
HEM wrist stepper mounted near W, M4 wrist axle clamped at W. Printed flat, the +y face (world y = 10,
where the wrist motor sits) on the bed, as modelled.

Local frame: origin on E, +x along u2 to W (150), +y in-plane, +z = world -y
(bed z = 0 is world y = 10, beam top z = 10 is y = 0, teeth z 10..16.2 = y 0..-6.2, cone to z 17 = y -7).
Assembly: R = Ry(-th2) Rx(90) about E, position (E_x, 10, E_z).
"""
import math

from build123d import (Align, BuildPart, BuildSketch, Circle, Cone, Cylinder, Location, Locations, Mode,
                       RectangleRounded, SlotCenterToCenter, extrude, make_hull)

from lib import BRG_D, BRG_W, FLANGE_D, FLANGE_T, G, M3_CLEAR, M4_CB, M4_SNUG, dims, gt2_outline, save

T = G.Y["upper"][1] - G.Y["upper"][0]                       # 10 beam
TEETH_Z = (T, T + 6.2)
H = T + 7.0                                                  # 17 at E
DISC_R = 46.0
L2 = G.L2
MX = L2 - G.C_WR                                             # wrist motor axis along the shank (91.4)
NEMA = dims("hem-17d2008-10")
PITCH = NEMA["hole pitch"]
PILOT_D = NEMA["pilot diameter"] + 1.0
SLOT = G.TENSION_SLOT
MOTOR_CB = (6.5, 6.5)                                        # from the top face -> M3 x 8, 4.5 mm into the motor
W_R = 13.0

with BuildPart() as p:
    with BuildSketch():
        Circle(DISC_R)
        with BuildSketch(mode=Mode.PRIVATE) as beam:
            Circle(26.0)
            with Locations((MX, 0)):
                RectangleRounded(52.0, 52.0, 6.0)
            with Locations((L2, 0)):
                Circle(W_R)
        make_hull(beam.edges())
    extrude(amount=T)
    teeth, od = gt2_outline(G.ELBOW_T)
    extrude(teeth.moved(Location((0, 0, TEETH_Z[0]))), amount=TEETH_Z[1] - TEETH_Z[0])
    root_r = od / 2 - 0.75
    with Locations((0, 0, TEETH_Z[1])):
        Cone(root_r, root_r + (H - TEETH_Z[1]), H - TEETH_Z[1], align=(Align.CENTER, Align.CENTER, Align.MIN))
    # disc windows (mass rides at E): 5 slots 13 x 11 at r 25.5, evenly 72 deg apart and symmetric about the
    # beam (36, 108, 180, 252, 324). User 2026-11-05: five cut-outs, same on both shanks; the first version
    # (5 at 60 deg, each spanning ~62 deg) left no web. Narrowest web now ~8.5 mm (end circles).
    for a in (36, 108, 180, 252, 324):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        with BuildSketch():
            with Locations((25.5 * c, 25.5 * s)):
                SlotCenterToCenter(13.0, 11.0, rotation=a + 90)
        extrude(amount=H, mode=Mode.SUBTRACT)
    with BuildSketch():
        with Locations(((50 + 62) / 2, 0)):
            SlotCenterToCenter(12.0, 9.0)
        with Locations(((124 + 138) / 2, 0)):
            SlotCenterToCenter(14.0, 6.0)
    extrude(amount=T, mode=Mode.SUBTRACT)
    # E: two F624 (bed face and the cone face), Ø7.6 through for the race tube
    Cylinder(3.8, H, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    Cylinder(BRG_D / 2, BRG_W, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    with Locations((0, 0, H)):
        Cylinder(BRG_D / 2, BRG_W, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
        Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
    # wrist motor (on the bed face side): pilot + M3 slots along the shank, head counterbores from the top
    with BuildSketch():
        with Locations((MX, 0)):
            SlotCenterToCenter(2 * SLOT, PILOT_D)
        with Locations(*[(MX + sx * PITCH / 2, sy * PITCH / 2) for sx in (-1, 1) for sy in (-1, 1)]):
            SlotCenterToCenter(2 * SLOT, M3_CLEAR)
    extrude(amount=T, mode=Mode.SUBTRACT)
    with BuildSketch(Location((0, 0, T))):
        with Locations(*[(MX + sx * PITCH / 2, sy * PITCH / 2) for sx in (-1, 1) for sy in (-1, 1)]):
            SlotCenterToCenter(2 * SLOT, MOTOR_CB[0])
    extrude(amount=-MOTOR_CB[1], mode=Mode.SUBTRACT)
    # W: M4 snug wrist axle, head counterbored in the bed face
    with Locations((L2, 0, 0)):
        Cylinder(M4_SNUG / 2, T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        Cylinder(M4_CB[0] / 2, M4_CB[1], align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

part = p.part
save(part, "upper_shank")
print("upper_shank", part.bounding_box().size, round(part.volume / 1000, 1), "cm3")
