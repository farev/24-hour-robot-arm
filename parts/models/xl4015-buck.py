"""XL4015 5 A buck module (common 51 x 26.3 mm board with heatsink and trimpot), seller-drawing class values.

Frame: PCB bottom at z = 0, origin at the board centre, long axis X. Two mounting holes Ø3 on the
diagonal at (+-22.5, +-10.0) [est; boards vary — measure before printing the tray].
"""
from pathlib import Path

from build123d import Align, Box, BuildPart, Cylinder, Locations, Mode, export_step

HERE = Path(__file__).parent
L, W, PCB, H = 51.0, 26.3, 1.6, 14.0
HOLES = [(-22.5, -10.0), (22.5, 10.0)]
with BuildPart() as b:
    Box(L, W, PCB, align=(Align.CENTER, Align.CENTER, Align.MIN))
    with Locations((0, 0, PCB)):
        Box(L - 10, W - 4, H - PCB, align=(Align.CENTER, Align.CENTER, Align.MIN))
    with Locations(*[(x, y, 0) for x, y in HOLES]):
        Cylinder(1.5, H, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
export_step(b.part, str(HERE / "xl4015-buck.step"))
print("ok")
