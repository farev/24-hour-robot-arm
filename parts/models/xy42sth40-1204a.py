"""XYSLDJ XY42STH40-1204A NEMA 17 stepper (40 mm), built from NEMA 17 standard values.

The series datasheet (datasheet_XY42STH.pdf) gives only length 40 mm and mass 0.28 kg; it has no
drawing. Face, hole pattern, pilot and shaft are NEMA 17 standard values (estimates). The side
connector is estimated from the photo parts/images/xy42sth40-1204a.jpg.

Frame: origin at the centre of the mounting face (pilot excluded), that face at z = 0, body toward
-Z, shaft along +Z, connector side toward -X.
Exports parts/models/xy42sth40-1204a.step and parts/models/xy42sth40-1204a-keepout.step.
"""
from pathlib import Path

from build123d import Align, Axis, Box, BuildPart, Cylinder, Locations, Mode, chamfer, export_step

OUT = Path(__file__).resolve().parent

FACE = 42.3          # body square
LENGTH = 40.0        # body length (series datasheet table)
PITCH = 31.0         # M3 hole square pattern, holes on the diagonals (+-15.5, +-15.5)
PILOT_D, PILOT_H = 22.0, 2.0
SHAFT_D, SHAFT_L = 5.0, 24.0   # shaft length from the mounting face to the tip
HOLE_D, HOLE_DEPTH = 2.5, 4.5  # M3 tapped hole modelled at tap-drill size
CORNER = 4.0         # chamfer on the four long edges (cosmetic)

# Connector socket on the -X side face near the rear end (estimated from the photo).
CONN_X_OUT = 5.0     # protrusion beyond the side face
CONN_Y = 14.0        # width (6-pin 2.0 mm pitch housing)
CONN_Z0, CONN_Z1 = -36.0, -27.0   # z extent; rear face is at z = -40
# Mating plug keep-out: plug body further out along -X, with room for the cable bend.
PLUG_X_OUT = 12.0
PLUG_Y = 16.0
PLUG_Z0, PLUG_Z1 = -38.0, -25.0

with BuildPart() as motor:
    Box(FACE, FACE, LENGTH, align=(Align.CENTER, Align.CENTER, Align.MAX))
    motor.part = chamfer(motor.part.edges().filter_by(Axis.Z), CORNER)
    Cylinder(PILOT_D / 2, PILOT_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    Cylinder(SHAFT_D / 2, SHAFT_L, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # connector socket body (overlaps the side face by 1 mm)
    with Locations((-FACE / 2 - CONN_X_OUT / 2 + 0.5, 0, (CONN_Z0 + CONN_Z1) / 2)):
        Box(CONN_X_OUT + 1.0, CONN_Y, CONN_Z1 - CONN_Z0)
    # tapped holes
    for sx in (-1, 1):
        for sy in (-1, 1):
            with Locations((sx * PITCH / 2, sy * PITCH / 2, 0)):
                Cylinder(HOLE_D / 2, HOLE_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MAX),
                         mode=Mode.SUBTRACT)

with BuildPart() as keepout:
    with Locations((-FACE / 2 - CONN_X_OUT - PLUG_X_OUT / 2, 0, (PLUG_Z0 + PLUG_Z1) / 2)):
        Box(PLUG_X_OUT, PLUG_Y, PLUG_Z1 - PLUG_Z0)

export_step(motor.part, str(OUT / "xy42sth40-1204a.step"))
export_step(keepout.part, str(OUT / "xy42sth40-1204a-keepout.step"))
print("bbox", motor.part.bounding_box())
