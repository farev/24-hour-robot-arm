"""AXK2035 needle thrust bearing (cage, 20x35x2) with two AS2035 washers (20x35x1).
Frame: axis Z, origin at bottom face centre, stack to z=+4. Three solids: washer, cage, washer."""
import os

from build123d import *

HERE = os.path.dirname(os.path.abspath(__file__))

ID, OD = 20.0, 35.0
WASHER_T, CAGE_T = 1.0, 2.0


def ring(z0, t):
    outer = Pos(0, 0, z0) * Cylinder(OD / 2, t, align=(Align.CENTER, Align.CENTER, Align.MIN))
    inner = Pos(0, 0, z0 - 1) * Cylinder(ID / 2, t + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return outer - inner


w1 = ring(0, WASHER_T)
cage = ring(WASHER_T, CAGE_T)
w2 = ring(WASHER_T + CAGE_T, WASHER_T)
export_step(Compound([w1, cage, w2]), os.path.join(HERE, "axk2035-thrust-bearing.step"))
