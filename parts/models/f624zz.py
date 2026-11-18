"""F624ZZ flanged shielded miniature bearing 4x13x5, flange D15 x 1.0 (flange inside the 5 mm width).
Frame: axis Z, flange outer face at z=0, flange z 0..-1, body to z=-5. Single solid."""
import os

from build123d import *

HERE = os.path.dirname(os.path.abspath(__file__))

BORE, OD, W, FD, FT = 4.0, 13.0, 5.0, 15.0, 1.0


def cyl(d, z0, h):
    return Pos(0, 0, z0) * Cylinder(d / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


p = cyl(FD, -FT, FT) + cyl(OD, -W, W - FT)
p -= cyl(BORE, -W - 1, W + 2)
export_step(p, os.path.join(HERE, "f624zz.step"))
