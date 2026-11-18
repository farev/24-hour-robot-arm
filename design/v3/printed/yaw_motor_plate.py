"""v3 yaw motor plate (3 mm): the 40 mm XY42 yaw motor hangs face-up under it, standing on the table
through the base cut-out, slid along x in slots to tension the yaw belt. Printed flat.

Frame: origin on the yaw motor axis at the plate underside (world (-C_YAW, 0, 40)), z up.
Motor screws M3 x 6 (3 mm plate + 3 mm into the motor); plate screws M3 x 16 into the base posts.
"""
from build123d import Align, BuildPart, BuildSketch, Cylinder, Locations, Mode, RectangleRounded, SlotCenterToCenter, extrude

from lib import G, M3_CLEAR, dims, save

T = G.YAW_PLATE_T
NEMA = dims("xy42sth40-1204a")
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
    with Locations(*[(sx * POST, sy * POST, 0) for sx in (-1, 1) for sy in (-1, 1)]):
        Cylinder(M3_CLEAR / 2, T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

part = p.part
save(part, "yaw_motor_plate")
print("yaw_motor_plate", part.bounding_box().size)
