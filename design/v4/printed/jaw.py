"""v4 gripper jaws A and B (from the user's reference picture): a stiff jaw riding on two pins (crank J1 and
idler J2, 19 mm apart on a back ear pointing outward) so it translates without rotating; forward pad with
a serrated grip face and triangular truss pockets on top. Printed flat, as modelled. Writes jaw_a / jaw_b.

Frame: origin on J1, +x along the gripper axis g, y = -h, z = world +y; bed z = 0 at world y = JAW_Y[0].
A (h < 0): pad face toward local -y.  B: mirrored (pad face toward +y).
"""
import math

from build123d import (Align, Box, BuildPart, BuildSketch, Circle, Cylinder, Locations, Mode, Polygon, extrude,
                       make_hull)

from lib import G, save

T = G.JAW_Y[1] - G.JAW_Y[0]                    # 6
D = G.IDLER_D                                   # J1 -> J2
FACE = G.PAD_FACE                               # pad face inward of the pin line
PAD = G.PAD
OUTER = 6.0                                     # pad back edge outward of the pin line
POCKET_D = 2.0                                  # truss pockets depth (top face)
SERR_P, SERR_D = 1.6, 0.6                       # grip serrations pitch / depth


OG = D * math.cos(math.radians(G.IDLER_DIR))    # J1 -> J2 along g (-1.7)
OH = abs(D * math.sin(math.radians(G.IDLER_DIR)))   # J1 -> J2 outward (18.9)


def jaw(kind):
    s = -1 if kind == "a" else 1                # inward = local s*y
    face, back = s * FACE, -s * OUTER
    j2 = (OG, -s * OH)                          # idler pin: outward of J1 (the jaw's back ear)
    with BuildPart() as p:
        with BuildSketch():
            with BuildSketch(mode=Mode.PRIVATE) as k:      # ear carrying both pins, webbed to the pad
                Circle(5.0)
                with Locations(j2):
                    Circle(5.0)
                with Locations((PAD[0] + 4, back + s * 2.0)):
                    Circle(3.0)
            make_hull(k.edges())
            Polygon((PAD[0] - 6, back), (PAD[1] - 3, back), (PAD[1] + 1, back + s * 3),
                    (PAD[1] + 1, face), (PAD[0], face), (PAD[0] - 6, 0.6 * face), align=None)
        extrude(amount=T)
        # truss pockets on the top face (like the reference): alternating triangles, 1.6 mm webs
        lo, hi = -OUTER + 1.6, FACE - 1.8                       # inward coordinate u = s * y
        xs = PAD[0] + 1.6
        tri = [[(xs, lo), (xs + 8.4, lo), (xs + 4.2, hi)],
               [(xs + 5.8, hi), (xs + 14.2, hi), (xs + 10.0, lo)],
               [(xs + 11.6, lo), (min(xs + 20.0, PAD[1] - 2.0), lo), (xs + 15.8, hi)]]
        tri = [[(x, s * u) for x, u in t] for t in tri]
        for t in tri:
            with BuildSketch() as sk:
                Polygon(*t, align=None)
            extrude(sk.sketch.moved(Locations((0, 0, T)).locations[0]), amount=-POCKET_D, mode=Mode.SUBTRACT)
        # serrated grip face
        x = PAD[0] + 1.0
        while x < PAD[1] - 0.5:
            with Locations((x, face, 0)):
                Box(SERR_P / 2, 2 * SERR_D, T, rotation=(0, 0, 45), align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT)
            x += SERR_P
        with Locations((0, 0, 0), (j2[0], j2[1], 0)):
            Cylinder(3.4 / 2, T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)   # M3 running
            # no boss-seat recess: a Ø7.6 seat over the Ø7.2 pin boss left a 1.2 mm ear wall; the pin pulls the jaw
            # down onto the boss top (0.5 mm modelled gap)
    return p.part


for k in ("a", "b"):
    part = jaw(k)
    save(part, f"jaw_{k}")
    print(f"jaw_{k}", part.bounding_box().size, round(part.volume / 1000, 1), "cm3")
