"""KW12-3 roller-lever microswitch (20 x 6.4 x 10.2 mm body class, the HiLetgo 10-pack type).
Values from the generic KW12-3 datasheet (Mouser-hosted 101411) and seller drawings; estimates marked.

Frame: body bottom (terminal edge) at z = 0, body to z = 10.2, length along X centred on x = 0,
thickness along Y (the two M2 mounting holes go through Y), lever + roller on the top edge,
hinged at -X, roller at +X. Terminals toward -Z.
"""
from pathlib import Path

from build123d import Align, Box, BuildPart, Cylinder, Locations, Mode, export_step

HERE = Path(__file__).parent
L, W, H = 20.0, 6.4, 10.2         # body [datasheet typ]
HOLE_D, HOLE_PITCH, HOLE_Z = 2.3, 9.5, 2.9   # M2 holes through Y [datasheet typ; height est]
LEVER_T, LEVER_W = 0.5, 4.0
ROLLER_D, ROLLER_W = 4.8, 3.0     # [est]
ROLLER_X, ROLLER_TOP = 8.0, H + 6.0   # roller centre x and free top height [est]
PIN_L = 3.8

with BuildPart() as sw:
    Box(L, W, H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    with Locations((-HOLE_PITCH / 2, 0, HOLE_Z), (HOLE_PITCH / 2, 0, HOLE_Z)):
        Cylinder(HOLE_D / 2, W + 0.2, rotation=(90, 0, 0), mode=Mode.SUBTRACT)
    with Locations(((-L / 2 + 1 + ROLLER_X) / 2, 0, H + 1.5)):
        Box(ROLLER_X + L / 2 - 1, LEVER_W, LEVER_T)
    with Locations((ROLLER_X, 0, ROLLER_TOP - ROLLER_D / 2)):
        Cylinder(ROLLER_D / 2, ROLLER_W, rotation=(90, 0, 0))
    with Locations(*[(x, 0, -PIN_L / 2) for x in (-8.0, 0.0, 8.0)]):
        Box(0.6, 3.0, PIN_L)
export_step(sw.part, str(HERE / "kw12-3-switch.step"))
print("ok")
