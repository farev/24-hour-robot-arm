"""High Efficiency Motors HEM-17D2008-10 NEMA 17 stepper (34 mm), built from NEMA 17 standard values.

No datasheet is available. Body length 34 mm was measured by the user; the label gives 0.28 N.m and
0.8 A/phase. Face, hole pattern, pilot and shaft are NEMA 17 standard values (estimates). The
rear PCB tab is estimated from the photo parts/images/hem-17d2008-10.jpg.

Frame: origin at the centre of the mounting face (pilot excluded), that face at z = 0, body toward
-Z, shaft along +Z, PCB tab toward -X.
Exports parts/models/hem-17d2008-10.step.
"""
from pathlib import Path

from build123d import Align, Axis, Box, BuildPart, Cylinder, Locations, Mode, chamfer, export_step

OUT = Path(__file__).resolve().parent

FACE = 42.3          # body square (estimate: NEMA 17 standard)
LENGTH = 34.0        # body length (user measured)
PITCH = 31.0         # M3 hole square pattern, holes at (+-15.5, +-15.5) (estimate)
PILOT_D, PILOT_H = 22.0, 2.0
SHAFT_D, SHAFT_L = 5.0, 24.0   # shaft length from the mounting face to the tip (estimate)
HOLE_D, HOLE_DEPTH = 2.5, 4.5  # M3 tapped hole modelled at tap-drill size (estimate)
CORNER = 4.0         # chamfer on the four long edges (cosmetic)

# Rear PCB / connector tab on the -X side (estimated from the photo).
TAB_X_OUT = 3.0      # protrusion beyond the side face
TAB_Y = 16.0         # width
TAB_Z0, TAB_Z1 = -34.0, -22.0     # z extent; rear face is at z = -34

with BuildPart() as motor:
    Box(FACE, FACE, LENGTH, align=(Align.CENTER, Align.CENTER, Align.MAX))
    motor.part = chamfer(motor.part.edges().filter_by(Axis.Z), CORNER)
    Cylinder(PILOT_D / 2, PILOT_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    Cylinder(SHAFT_D / 2, SHAFT_L, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # PCB tab (overlaps the side face by 1 mm)
    with Locations((-FACE / 2 - TAB_X_OUT / 2 + 0.5, 0, (TAB_Z0 + TAB_Z1) / 2)):
        Box(TAB_X_OUT + 1.0, TAB_Y, TAB_Z1 - TAB_Z0)
    # tapped holes
    for sx in (-1, 1):
        for sy in (-1, 1):
            with Locations((sx * PITCH / 2, sy * PITCH / 2, 0)):
                Cylinder(HOLE_D / 2, HOLE_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MAX),
                         mode=Mode.SUBTRACT)

export_step(motor.part, str(OUT / "hem-17d2008-10.step"))
print("bbox", motor.part.bounding_box())
