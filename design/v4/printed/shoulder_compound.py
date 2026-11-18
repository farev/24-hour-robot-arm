"""v3 shoulder intermediate pulley: 72T (driven by the shoulder motor's 20T) and 36T (drives the lower
shank's 140T) on one tube, turning on two F624 on an M4 x 70 axle through both towers. Printed standing,
the 72T end (world y = 24) on the bed, as modelled.

Frame: origin on the intermediate axis I at the 72T end face, +z = world -y (top z = 50 is world y = -26).
Assembly: R = Rx(90) (z -> -y), position (I_x, 24, I_z).
"""
from build123d import Align, BuildPart, Cone, Cylinder, Location, Locations, Mode, extrude

from lib import BRG_D, BRG_W, FLANGE_D, FLANGE_T, G, gt2_outline, save

Y_TOP, Y_BOT = G.Y["tower_r"][0] - 1.0, G.Y["pulley_l"][0]   # 24 .. -26 (race washers fill the 1 mm to each tower)
H = Y_TOP - Y_BOT                                             # 50
zp = lambda y: Y_TOP - y
T72 = (zp(G.BELT_SH1 + 3.1), zp(G.BELT_SH1 - 3.1))            # 0.9 .. 7.1
T36 = (zp(G.BELT_SH2 + 3.1), zp(G.BELT_SH2 - 3.1))            # 42.15 .. 48.35
TUBE_R = 10.5                                                 # <= 36T root (10.7); F624 pocket wall 3.95

with BuildPart() as p:
    t72, od72 = gt2_outline(G.SH_T1)
    # 72T teeth start on the bed (no 0.9 mm bed flange: too thin to print); the tower face 1 mm away and
    # the motor pulley's flanges keep the belt on
    extrude(t72, amount=T72[1])
    r72 = od72 / 2 - 0.75
    with Locations((0, 0, T72[1])):                                                        # 45 deg taper to the tube
        Cone(r72, TUBE_R, r72 - TUBE_R, align=(Align.CENTER, Align.CENTER, Align.MIN))
    Cylinder(TUBE_R, T36[0], align=(Align.CENTER, Align.CENTER, Align.MIN))
    t36, od36 = gt2_outline(G.SH_T2)
    cone_h = od36 / 2 + 1.0 - TUBE_R                                                       # 45 deg (was 1.0 tall, 60 deg)
    with Locations((0, 0, T36[0] - cone_h)):                                               # flange cone under the 36T
        Cone(TUBE_R, od36 / 2 + 1.0, cone_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    extrude(t36.moved(Location((0, 0, T36[0]))), amount=T36[1] - T36[0])
    with Locations((0, 0, T36[1])):
        Cylinder(od36 / 2 - 0.75, H - T36[1], align=(Align.CENTER, Align.CENTER, Align.MIN))
    # bearings at both ends, Ø7.6 race tube between
    Cylinder(3.8, H, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    Cylinder(BRG_D / 2, BRG_W, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    with Locations((0, 0, H)):
        Cylinder(BRG_D / 2, BRG_W, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
        Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)

part = p.part
save(part, "shoulder_compound")
print("shoulder_compound", part.bounding_box().size, round(part.volume / 1000, 1), "cm3")
