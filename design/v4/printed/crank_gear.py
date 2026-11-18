"""v4 gripper crank gears A and B: 16T module 1.5 spur gear with a 26 mm crank arm ending in a pin boss
that carries a jaw. A screws to the gripper servo's round horn; B turns on an M3 pivot. Printed flat,
as modelled (bed = the face toward the gripper base). Writes crank_gear_a.step and crank_gear_b.step.

Frame: origin on the gear axis, +x along the crank, y = (world +y) x (crank), z = world +y.
A: bed z = 0 at world y = FINGER_Y0 = 0.8 (on the horn top, estimated: measure), 6.0 thick. B: bed at
y = FINGER_Y0 + 0.6, 5.4 thick.
Teeth are phased so that, with the cranks at the closed angle, A's tooth faces B's gap on the centre line.
"""
from build123d import Align, Axis, BuildPart, BuildSketch, Circle, Cylinder, Locations, Mode, extrude, make_hull

from lib import G, gear_sketch, save

M, Z = G.GEAR_M, G.GEAR_T
L = G.CRANK_L
HORN_SCREW_R = 7.0                          # [est] round horn screw circle (measure the horn)
# local angle of the mesh contact at the closed pose: crank (g,h) angle theta, contact direction psi -> theta - psi
PHASE = {"a": (G.CRANK_CLOSED * -1 - 90.0) % (360 / Z),                 # A: tooth on the contact line
         "b": (G.CRANK_CLOSED + 90.0 - 180.0 / Z) % (360 / Z)}          # B: gap on the contact line


def crank(kind):
    t = 6.0 if kind == "a" else G.LINK_T
    boss_h = G.PIN_BOSS_TOP - (G.FINGER_Y0 + (0.0 if kind == "a" else 0.6)) - t   # boss on top up to y 9.0
    with BuildPart() as p:
        g, rp, ra, rf = gear_sketch(M, Z, backlash=0.35)       # FDM teeth print ~0.1 fat per flank (rules §1)
        extrude(g.rotate(Axis.Z, PHASE[kind]), amount=t)
        with BuildSketch():                                    # crank arm, tapered from the hub to the pin end
            with BuildSketch(mode=Mode.PRIVATE) as arm:
                Circle(7.0)
                with Locations((L, 0)):
                    Circle(4.5)
            make_hull(arm.edges())
        extrude(amount=t)
        with Locations((L, 0, t)):
            Cylinder(3.6, boss_h, align=(Align.CENTER, Align.CENTER, Align.MIN))     # jaw pin boss
        with Locations((L, 0, 0)):
            Cylinder(3.2 / 2, t + boss_h, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)  # M3 snug
        if kind == "a":                                         # horn: centre access + 4 screws, heads from the top
            Cylinder(3.5, t, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
            pts = [(HORN_SCREW_R * c, HORN_SCREW_R * s) for c, s in ((1, 0), (0, 1), (-1, 0), (0, -1))]
            with Locations(*[(x, y, 0) for x, y in pts]):           # M2 clearance (rules §2): the screw threads
                Cylinder(1.3, t, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)   # into the horn only
            with Locations(*[(x, y, t) for x, y in pts]):
                Cylinder(1.9, 2.0, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
        else:
            Cylinder(3.4 / 2, t, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)   # runs on the M3 pivot
    return p.part


for k in ("a", "b"):
    part = crank(k)
    save(part, f"crank_gear_{k}")
    print(f"crank_gear_{k}", part.bounding_box().size, "phase", round(PHASE[k], 2))
