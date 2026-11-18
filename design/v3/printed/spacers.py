"""v3 inner-race spacer tubes (Ø7 x Ø4.3, wall 1.35) and the race washer (Ø9 x Ø4.3 x 1.0). Printed upright.
S stack between the tower inner faces (-27 .. 25 = 52): washer 1 + lower shank hub 18 (two F624 + spacer_ls 8)
+ spacer_s 32 + washer 1. I stack: washer 1 + compound 50 (two F624 + spacer_i 40) + washer 1.
E: two F624 in the upper shank hub (17) + spacer_e 7. W: two F624 in the wrist pulley (16) + spacer_w 6.
"""
from build123d import Align, BuildPart, Cylinder, Mode

from lib import G, save

OD, ID, BRG = 7.0, 4.3, 5.0
Y = G.Y
LENGTHS = {
    "spacer_s": (Y["tower_r"][0] - 1.0) - Y["lower"][1],                       # 24 - (-8) = 32
    "spacer_ls": (Y["lower"][1] - Y["pulley_l"][0]) - 2 * BRG,                 # 8
    "spacer_i": (((Y["tower_r"][0] - 1.0) - Y["pulley_l"][0]) - 2 * BRG) / 2,  # 40 as two 20 mm tubes (a 40 mm tube tips)
    "spacer_e": (Y["upper"][1] - Y["upper_teeth"][0]) - 2 * BRG,               # 17 - 10 = 7
    "spacer_w": (Y["wrist_pulley"][1] - Y["wrist_pulley"][0]) - 2 * BRG,       # 16 - 10 = 6
}
for name, length in LENGTHS.items():
    with BuildPart() as p:
        Cylinder(OD / 2, length, align=(Align.CENTER, Align.CENTER, Align.MIN))
        Cylinder(ID / 2, length, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    save(p.part, name)
    print(name, round(length, 2))
with BuildPart() as w:
    Cylinder(4.5, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    Cylinder(ID / 2, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
save(w.part, "race_washer")
print("race_washer 1.0")
