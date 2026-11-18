"""Inner-race spacer tubes (Ø7 x Ø4.3, wall 1.35) that set the bolt clamp stacks. Printed upright.
Writes spacer_s.step (shoulder axle, between the lower shank and the lever pulley inner races),
spacer_ls.step (inside the lower shank hub, between its two F624) and spacer_pu.step (pleuel PU
bearing to the upper shank). Frame: axis Z, bottom face at z = 0.
S stack between the tower inner faces (51.0): race washer 1 + F624 5 + spacer_ls 8 + F624 5 +
spacer_s 21 + 2 x F624 10 + race washer 1. Also writes race_washer.step.
"""
from build123d import Align, BuildPart, Cylinder, Mode

from lib import G, save

OD, ID = 7.0, 4.3
LENGTHS = {
    "spacer_s": G.Y["lever"][0] - G.Y["lower"][1],           # 21 (1.0 race washers fill the 1.0 tower gaps)
    "spacer_ls": (G.Y["lower"][1] - G.Y["pulley_l"][0]) - 2 * 5.0,   # 18 - two bearings = 8
    "spacer_pu": (G.Y["pleuel"][1] - 5.0) - G.Y["upper"][1],  # pleuel inner race face (8) -> upper shank face (4)
}
for name, length in LENGTHS.items():
    with BuildPart() as p:
        Cylinder(OD / 2, length, align=(Align.CENTER, Align.CENTER, Align.MIN))
        Cylinder(ID / 2, length, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    save(p.part, name)
    print(name, round(length, 2))

# race washer: Ø9 x Ø4.3 x 1.0 (wall 2.35, 5 layers), fills each 1 mm joint gap and bears on the inner race
with BuildPart() as w:
    Cylinder(4.5, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    Cylinder(ID / 2, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
save(w.part, "race_washer")
print("race_washer 1.0")
