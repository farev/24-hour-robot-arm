"""v3 lower shank: shoulder 140T (stage 2 of the 14:1) at S, elbow stepper mounted on its -y face near E,
M4 elbow bolt clamped at E. Printed flat, the +y face (world y = -8) on the bed, as modelled.

Local frame: origin on S, +x along the shank to E (150), +y in-plane, +z = world -y
(bed z = 0 is world y = -8, plate top z = 10 is y = -18, teeth to z = 18 = y -26).
Assembly: R = Ry(-th1) Rx(90) about S, position (S_X, -8, S_Z).
The elbow XY42 sits on the plate top (world -y face) with its shaft through the plate, belt on the bed side.
"""
import math

from build123d import (Align, BuildPart, BuildSketch, Circle, Cone, Cylinder, Location, Locations, Mode,
                       RectangleRounded, SlotCenterToCenter, extrude, make_hull)

from lib import BRG_D, BRG_W, FLANGE_D, FLANGE_T, G, M3_CLEAR, M4_CB, M4_SNUG, dims, gt2_outline, save

PLATE_T = G.Y["lower"][1] - G.Y["lower"][0]                  # 10
H = G.Y["lower"][1] - G.Y["pulley_l"][0]                     # 18
TEETH_Z = (PLATE_T, PLATE_T + 6.5)
DISC_R = 46.0
L1 = G.L1
MX = L1 - G.C_EL                                             # elbow motor axis along the shank (80.5)
NEMA = dims("xy42sth40-1204a")
PITCH = NEMA["hole pitch"]
PILOT_D = NEMA["pilot diameter"] + 1.0
SLOT = G.TENSION_SLOT
MOTOR_CB = (6.5, 6.0)                                        # M3 head counterbore from the bed face -> M3 x 8, 4 mm into the motor
E_R = 13.0

with BuildPart() as p:
    with BuildSketch():
        Circle(DISC_R)
        with BuildSketch(mode=Mode.PRIVATE) as beam:
            Circle(30.0)
            with Locations((MX, 0)):
                RectangleRounded(52.0, 52.0, 6.0)
            with Locations((L1, 0)):
                Circle(E_R)
        make_hull(beam.edges())
    extrude(amount=PLATE_T)
    teeth, od = gt2_outline(G.SH_T3)
    extrude(teeth.moved(Location((0, 0, TEETH_Z[0]))), amount=TEETH_Z[1] - TEETH_Z[0])
    root_r = od / 2 - 0.75
    with Locations((0, 0, TEETH_Z[1])):
        Cone(root_r, root_r + (H - TEETH_Z[1]), H - TEETH_Z[1], align=(Align.CENTER, Align.CENTER, Align.MIN))
    for a in (40, 112, 184, 256, 328):                       # disc windows
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        with BuildSketch():
            with Locations((25 * c, 25 * s)):
                SlotCenterToCenter(12.0, 9.0, rotation=a + 90)
        extrude(amount=H, mode=Mode.SUBTRACT)
    with BuildSketch():                                      # beam windows clear of the motor square
        with Locations(((36 + 50) / 2, 0)):
            SlotCenterToCenter(14.0, 10.0)
        with Locations(((112 + 134) / 2, 0)):
            SlotCenterToCenter(22.0, 8.0)
    extrude(amount=PLATE_T, mode=Mode.SUBTRACT)
    # S hub: two F624, Ø7.6 through for the race tube
    Cylinder(3.8, H, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    Cylinder(BRG_D / 2, BRG_W, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    with Locations((0, 0, H)):
        Cylinder(BRG_D / 2, BRG_W, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
        Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
    # elbow motor: pilot slot and M3 slots along the shank (+-3 for belt tension), head counterbores on the bed face
    with BuildSketch():
        with Locations((MX, 0)):
            SlotCenterToCenter(2 * SLOT, PILOT_D)
        with Locations(*[(MX + sx * PITCH / 2, sy * PITCH / 2) for sx in (-1, 1) for sy in (-1, 1)]):
            SlotCenterToCenter(2 * SLOT, M3_CLEAR)
    extrude(amount=PLATE_T, mode=Mode.SUBTRACT)
    with BuildSketch():
        with Locations(*[(MX + sx * PITCH / 2, sy * PITCH / 2) for sx in (-1, 1) for sy in (-1, 1)]):
            SlotCenterToCenter(2 * SLOT, MOTOR_CB[0])
    extrude(amount=MOTOR_CB[1], mode=Mode.SUBTRACT)
    # E: M4 snug, head counterbored in the plate top (world -y face) -> M4 x 30
    with Locations((L1, 0, 0)):
        Cylinder(M4_SNUG / 2, PLATE_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    with Locations((L1, 0, PLATE_T)):
        Cylinder(M4_CB[0] / 2, M4_CB[1], align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)

part = p.part
save(part, "lower_shank")
print("lower_shank", part.bounding_box().size, round(part.volume / 1000, 1), "cm3")
