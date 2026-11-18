"""Fit-test coupon: print this first (about 15 min) in the same PLA, flat on the bed, and tell Mechy which
sizes fit. Writes fit_coupon.step and fit-coupon.stl (not part of the assembly).

Row 1: F624ZZ press pockets Ø12.9 / 13.0 / 13.1 / 13.2 (5 deep, flange counterbore 15.4 x 1.1).
       The parts use 13.1: the bearing should press in by thumb and not fall out.
Row 2: M4 snug holes Ø4.0 / 4.1 / 4.2 / 4.3 (parts use 4.2: the bolt slides in with light force).
Row 3: M3 holes Ø3.4 / 3.6 and self-tap pilots Ø2.4 / 2.6 (parts use 3.6 clearance, 2.6 pilot).
Numbers are debossed next to each hole (0.6 deep).
"""
from pathlib import Path

from build123d import (Align, BuildPart, BuildSketch, Box, Cylinder, Locations, Mode, Text, extrude, export_stl)

from lib import FLANGE_D, FLANGE_T, save

HERE = Path(__file__).parent
T = 6.0
rows = [
    [(12.9, "12.9"), (13.0, "13.0"), (13.1, "13.1"), (13.2, "13.2")],
    [(4.0, "4.0"), (4.1, "4.1"), (4.2, "4.2"), (4.3, "4.3")],
    [(3.4, "3.4"), (3.6, "3.6"), (2.4, "2.4"), (2.6, "2.6")],
]
PITCH_X, PITCH_Y = 22.0, 20.0
with BuildPart() as p:
    Box(4 * PITCH_X + 4, 3 * PITCH_Y + 4, T, align=(Align.MIN, Align.MIN, Align.MIN))
    for r, row in enumerate(rows):
        for c, (d, label) in enumerate(row):
            x, y = 2 + PITCH_X * (c + 0.5), 2 + PITCH_Y * (2 - r) + 11.5
            with Locations((x, y, T)):
                if r == 0:
                    Cylinder(d / 2, 5.0, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
                    Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
                    Cylinder(2.5, T, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)  # push-out hole
                else:
                    Cylinder(d / 2, T, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
            with BuildSketch() as s:
                with Locations((x, y - 9.5)):
                    Text(label, font_size=3.5)
            extrude(s.sketch.moved(Locations((0, 0, T)).locations[0]), amount=-0.6, mode=Mode.SUBTRACT)
part = p.part
save(part, "fit_coupon")
export_stl(part, str(HERE / "fit-coupon.stl"))
print("fit_coupon", part.bounding_box().size)
