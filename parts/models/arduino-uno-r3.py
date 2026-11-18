"""Arduino Uno R3 with the owned CNC Shield V3 + 4 A4988 carriers stacked on it.

Board outline and holes from the Arduino Uno Rev3 drawing (68.6 x 53.3, holes at (14.0, 2.5),
(15.3, 50.7), (66.1, 7.6), (66.1, 35.5) from the lower-left corner, USB-B and jack on the x = 0 edge).
Shield + driver stack height is an estimate from the photo.
Frame: origin at the PCB bottom-left corner, PCB bottom at z = 0, USB/jack edge at x = 0 (pointing -X).
Also writes arduino-uno-r3-keepout.step: USB-B plug + cable bend and the shield's power terminal wires.
"""
from pathlib import Path

from build123d import Align, Box, BuildPart, Cylinder, Locations, Mode, export_step

HERE = Path(__file__).parent
BL, BW, PCB = 68.6, 53.3, 1.6
HOLES = [(14.0, 2.5), (15.3, 50.7), (66.1, 7.6), (66.1, 35.5)]
HOLE_D = 3.2
USB = (-6.2, 38.1 - 6, PCB, 16.0, 12.0, 10.9)      # x0, y0, z0, dx, dy, dz  [drawing approx]
JACK = (-1.8, 3.3, PCB, 14.0, 9.0, 11.0)
STACK_H = 45.0           # [est] PCB bottom -> top of A4988 heatsinks
SHIELD_Z = 13.0          # [est] shield PCB bottom above the Uno PCB bottom (header stack)

with BuildPart() as uno:
    Box(BL, BW, PCB, align=(Align.MIN, Align.MIN, Align.MIN))
    with Locations(*[(x, y, 0) for x, y in HOLES]):
        Cylinder(HOLE_D / 2, PCB, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    for x0, y0, z0, dx, dy, dz in (USB, JACK):
        with Locations((x0, y0, z0)):
            Box(dx, dy, dz, align=(Align.MIN, Align.MIN, Align.MIN))
    with Locations((2.0, 2.0, PCB)):                       # components + headers under the shield [est]
        Box(BL - 4, BW - 4, SHIELD_Z - PCB, align=(Align.MIN, Align.MIN, Align.MIN))
    with Locations((0, 0, SHIELD_Z)):                       # shield PCB + drivers + heatsinks envelope [est]
        Box(BL, BW, STACK_H - SHIELD_Z, align=(Align.MIN, Align.MIN, Align.MIN))
    with Locations(*[(x, y, 0) for x, y in HOLES]):        # keep the screw holes open through the stack
        Cylinder(HOLE_D / 2, SHIELD_Z, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
export_step(uno.part, str(HERE / "arduino-uno-r3.step"))

with BuildPart() as ko:                                    # plug + cable bend keep-outs [est]
    with Locations((USB[0] - 40, USB[1] - 1, USB[2] - 1)):
        Box(40, USB[4] + 2, USB[5] + 2, align=(Align.MIN, Align.MIN, Align.MIN))
    with Locations((-25, 30, SHIELD_Z + 2)):               # shield screw-terminal wires leave toward -X
        Box(25, 12, 12, align=(Align.MIN, Align.MIN, Align.MIN))
    with Locations((0, 0, STACK_H)):                        # motor/servo plugs, cable bends and the bundle over the
        Box(BL, BW, 2.0, align=(Align.MIN, Align.MIN, Align.MIN))   # stack, 2 mm above the heatsinks [est]
    with Locations((-6.0, 14.0, SHIELD_Z + 2)):             # bundle leaving toward -X to the base's zip-tie block
        Box(6.0, 10.0, STACK_H - SHIELD_Z, align=(Align.MIN, Align.MIN, Align.MIN))
export_step(ko.part, str(HERE / "arduino-uno-r3-keepout.step"))
print("ok")
