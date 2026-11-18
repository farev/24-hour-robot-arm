"""Yaw motor plate: the HEM 34 mm motor hangs face-up under it, slid along x in slots to tension the
yaw belt; the plate screws onto the four base posts. Printed flat (motor face side on the bed).

Frame: origin on the yaw motor axis at the plate underside (world (-C_YAW, 0, 38)), z up.
Assembly: rotation [0, 0, 0], position (-C_YAW, 0, 38).
"""
from build123d import (Align, BuildPart, BuildSketch, Cylinder, Locations, Mode, Plane, RectangleRounded,
                       SlotCenterToCenter, extrude)

from lib import G, M3_CB, M3_CLEAR, dims, save

M3_CB_D, MOTOR_CB_DEPTH = M3_CB[0], 1.5

T = G.YAW_PLATE_T
NEMA = dims("hem-17d2008-10")
PITCH = NEMA["hole pitch"]
PILOT_D = NEMA["pilot diameter"] + 1.0
SLOT = G.TENSION_SLOT
POST = 26.0

with BuildPart() as p:
    with BuildSketch():
        RectangleRounded(2 * POST + 9.0, 2 * POST + 9.0, 6.0)
    extrude(amount=T)
    with BuildSketch():
        SlotCenterToCenter(2 * SLOT, PILOT_D)
        with Locations(*[(sx * PITCH / 2, sy * PITCH / 2) for sx in (-1, 1) for sy in (-1, 1)]):
            SlotCenterToCenter(2 * SLOT, M3_CLEAR)
    extrude(amount=T, mode=Mode.SUBTRACT)
    # motor screw head counterbore slots on the top: M3 x 8 then engages 4.5 mm in the motor (rules §2)
    with BuildSketch(Plane.XY.offset(T)):
        with Locations(*[(sx * PITCH / 2, sy * PITCH / 2) for sx in (-1, 1) for sy in (-1, 1)]):
            SlotCenterToCenter(2 * SLOT, M3_CB_D)
    extrude(amount=-MOTOR_CB_DEPTH, mode=Mode.SUBTRACT)
    with Locations(*[(sx * POST, sy * POST, 0) for sx in (-1, 1) for sy in (-1, 1)]):
        Cylinder(M3_CLEAR / 2, T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

part = p.part
save(part, "yaw_motor_plate")
print("yaw_motor_plate", part.bounding_box().size)
