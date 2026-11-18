"""GT2 20T, 5 mm bore, 6 mm belt aluminium pulley with 2x M3 set screws.
Frame: bore axis Z, origin at hub end face centre (z=0), teeth toward +Z.
Pitch dia / OD from standard_parts/timing_pulleys.csv (GT2-20T); hub and flange sizes are
typical for the 16 mm long 6 mm-belt pulley sold in the Amazon 5-pack (estimate)."""
import math
import os

from build123d import *

HERE = os.path.dirname(os.path.abspath(__file__))

BORE = 5.0
HUB_D, HUB_L = 13.0, 7.0
FLANGE_D, FLANGE_T = 16.0, 1.0
TEETH_L = 7.0
OD = 12.224
N = 20
TOOTH_H = 0.75
SETSCREW_D = 3.0  # M3 tap hole
L = HUB_L + FLANGE_T + TEETH_L + FLANGE_T  # 16


def cyl(d, z0, h):
    return Pos(0, 0, z0) * Cylinder(d / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


p = cyl(HUB_D, 0, HUB_L)
p += cyl(FLANGE_D, HUB_L, FLANGE_T)
teeth = cyl(OD, HUB_L + FLANGE_T, TEETH_L)
r = OD / 2
for i in range(N):
    a = 2 * math.pi * (i + 0.5) / N  # groove between teeth
    g = Pos(r * math.cos(a), r * math.sin(a), HUB_L + FLANGE_T - 0.1) * Cylinder(
        TOOTH_H, TEETH_L + 0.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    teeth -= g
p += teeth
p += cyl(FLANGE_D, HUB_L + FLANGE_T + TEETH_L, FLANGE_T)
p -= cyl(BORE, -1, L + 2)
# two set screws on the hub, 90 deg apart, mid hub
zc = HUB_L / 2
for ang in (0, 90):
    h = Rot(0, 0, ang) * Pos(0, 0, zc) * Rot(0, 90, 0) * Cylinder(
        SETSCREW_D / 2, HUB_D, align=(Align.CENTER, Align.CENTER, Align.MIN))
    p -= h
export_step(p, os.path.join(HERE, "gt2-20t-pulley.step"))
