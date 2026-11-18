"""v3 base (v2 base + a floor cut-out so the 40 mm XY42 yaw motor stands on the table and its face stays
at z 40 under a 3 mm plate): centre boss with the AXK2035 seat and the two yaw F624, yaw motor posts,
yaw homing switch pocket, Uno and buck posts, clamp holes. Printed floor down. Frame = world frame.
"""
import math

from build123d import Align, BuildPart, BuildSketch, Box, Cone, Cylinder, Locations, Mode, RectangleRounded, extrude

from lib import BRG_D, FLANGE_D, FLANGE_T, G, dims, save

FLOOR = G.FLOOR
AXK = dims("axk2035-thrust-bearing")
BOSS_R, BOSS_TOP = 34.0, G.AXK_Z0 + 1.0              # 47.5: rim around the AXK pocket
AXK_POCKET = (AXK["outer diameter"] + 1.0, 1.0)      # loose on the OD; the washer is located by its bore
RING = (AXK["inner diameter"] - 0.4, 16.4, G.AXK_Z0 + 2.6)   # centring ring OD/ID, top z (inside washer + cage
                                                               # bores; 0.6 below the yaw pulley spigot)
TOP_BRG_TOP = G.AXK_Z0                                # top F624 flange flush with the pocket floor
BOT_SHOULDER = 9.0                                    # bottom F624 flange bears up against this face; below it a
                                                      # race washer (z 7..8) and the M4 nut (z 3.8..7): the M4 x 60
                                                      # from the deck ends at z 3.1, 0.7 through the nut
YM = (-G.C_YAW, 0.0)                                  # yaw motor axis
POST = 26.0                                           # yaw plate posts at +-26 from the motor axis
POST_H = G.YAW_MOTOR_FACE_Z                           # post tops = motor face height (plate sits on them)
SW = dims("kw12-3-switch")
SW_ROLLER = SW["roller top above body"]
SW_PRESS = 1.0                                        # cam presses the roller 1 mm below its free height
CAM_BOTTOM = G.YAW_PULLEY_Z[0] - 1.2                  # yaw pulley cam underside (yaw_pulley.CAM_H)
SW_BODY_TOP = CAM_BOTTOM + SW_PRESS - SW_ROLLER       # 44.3: body top below the boss top
SW_POCKET = (SW["body width"] + 0.4, SW["body length"] + 0.4)   # radial x tangential (+0.2/side, glue)
SW_R = 26.0
UNO_ORIGIN = (-118.0, 36.0)                           # Uno PCB lower-left corner (x0, y0), clear of the yaw plate
UNO_HOLES = [(14.0, 2.5), (15.3, 50.7), (66.1, 7.6), (66.1, 35.5)]
UNO_POST_H = 3.0                                      # Uno PCB at z 7 (was 5 -> z 9)
TIE = (-121.5, 56.0)                                  # cable zip-tie block, clear of the jack (y < 48.3) and USB (y > 67)
BUCK_C, BUCK_HOLES = (-84.0, -45.0), [(-22.5, -10.0), (22.5, 10.0)]   # x -84: post clear of the corner clamp hole
OUT = (-125.0, 80.0, -62.0, 93.0)                     # x0, x1, y0, y1 of the floor

with BuildPart() as p:
    with BuildSketch():
        with Locations(((OUT[0] + OUT[1]) / 2, (OUT[2] + OUT[3]) / 2)):
            RectangleRounded(OUT[1] - OUT[0], OUT[3] - OUT[2], 8.0)
    extrude(amount=FLOOR)
    # yaw motor cut-out: body (42.3 + 1.0) plus the +-3 tension travel along x, the motor stands on the table
    with Locations((YM[0], YM[1], 0)):
        Box(42.3 + 1.0 + 2 * G.TENSION_SLOT, 42.3 + 1.0, FLOOR, align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT)
    # centre boss: outer wall + core, hollow ring cavity with a 45 deg conical roof (prints without
    # support), joined by 6 ribs
    cav_in, cav_out = 13.0, BOSS_R - 3.0
    roof_top = BOSS_TOP - 4.0
    roof_start = roof_top - (cav_out - cav_in)
    with Locations((0, 0, FLOOR)):
        Cylinder(BOSS_R, BOSS_TOP - FLOOR, align=(Align.CENTER, Align.CENTER, Align.MIN))
        Cylinder(cav_out, roof_start - FLOOR, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    with Locations((0, 0, roof_start)):
        Cone(cav_out, cav_in, roof_top - roof_start, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    with Locations((0, 0, FLOOR)):
        Cylinder(cav_in, BOSS_TOP - FLOOR, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for a in (30, 90, 150, 210, 270, 330):
        with Locations((0, 0, FLOOR)):
            Box(BOSS_R - 2, 2.4, roof_top - FLOOR, rotation=(0, 0, a), align=(Align.MIN, Align.CENTER, Align.MIN))
    # switch support block inside the cavity (the pocket floor sits on it)
    sw_floor = SW_BODY_TOP - SW["body height"]
    with Locations((SW_R, 0, FLOOR)):
        Box(SW_POCKET[0] + 4.0, SW_POCKET[1] + 4.0, sw_floor - FLOOR, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # switch wire exit through the boss wall at +x (under the switch), flat 5 mm bridge roof
    with Locations((BOSS_R - 1.5, 0, FLOOR)):
        Box(4.0, 5.0, 6.0, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    # AXK seat: pocket on the boss top + centring ring through the washer/cage bores
    with Locations((0, 0, BOSS_TOP)):
        Cylinder(AXK_POCKET[0] / 2, AXK_POCKET[1], align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
    with Locations((0, 0, G.AXK_Z0)):
        Cylinder(RING[0] / 2, RING[2] - G.AXK_Z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        Cylinder(RING[1] / 2, RING[2] - G.AXK_Z0, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    # top F624 (radial, flange up) and bottom F624 (flange down, takes the nut's pull), M4 through; Ø7.6 relief
    # between the two pockets so only the outer rings touch the base (the inner rings turn with the bolt)
    Cylinder(4.8 / 2, BOSS_TOP, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    with Locations((0, 0, BOT_SHOULDER + 4.0)):
        Cylinder(7.6 / 2, (TOP_BRG_TOP - 5.0) - (BOT_SHOULDER + 4.0), align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)
    with Locations((0, 0, TOP_BRG_TOP)):
        Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
        Cylinder(BRG_D / 2, 5.0, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
    Cylinder(FLANGE_D / 2, BOT_SHOULDER, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    with Locations((0, 0, BOT_SHOULDER)):
        Cylinder(BRG_D / 2, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    # yaw homing switch pocket in the boss rim at +x: body standing upright, roller up under the cam;
    # a 4 x 18 slot through the support block takes the terminals and wires down to the exit
    with Locations((SW_R, 0, BOSS_TOP)):
        Box(SW_POCKET[0], SW_POCKET[1], BOSS_TOP - sw_floor, align=(Align.CENTER, Align.CENTER, Align.MAX),
            mode=Mode.SUBTRACT)
    with Locations((SW_R, 0, sw_floor)):
        Box(4.0, 18.0, sw_floor - FLOOR, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
    with Locations((SW_R + 2.0, 0, FLOOR)):
        Box(BOSS_R - SW_R, 5.0, 6.0, align=(Align.MIN, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    # yaw motor posts (the plate sits on them; Ø2.6 self-tap pilots, assembled once)
    with Locations(*[(YM[0] + sx * POST, sy * POST, FLOOR) for sx in (-1, 1) for sy in (-1, 1)]):
        Cylinder(4.5, POST_H - FLOOR, align=(Align.CENTER, Align.CENTER, Align.MIN))
        Cylinder(1.3, POST_H - FLOOR, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    # Uno posts 3 mm (the shield stack + plugs stay 8.5 mm under the turret's sweep), buck posts 5 mm; Ø2.6
    # pilots for M3 x 8 self-tapping screws, run down through the floor
    uno = [(UNO_ORIGIN[0] + x, UNO_ORIGIN[1] + y) for x, y in UNO_HOLES]
    buck = [(BUCK_C[0] + x, BUCK_C[1] + y) for x, y in BUCK_HOLES]
    for pts, h in ((uno, UNO_POST_H), (buck, 5.0)):
        with Locations(*[(x, y, FLOOR) for x, y in pts]):
            Cylinder(3.25, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations(*[(x, y, 0) for x, y in pts]):
            Cylinder(1.3, FLOOR + h, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    # cable anchor (design review 2026-11-06): zip-tie block on the -x edge beside the Uno, r 134 from the yaw axis
    # (outside the turret's 127 sweep). The motor and servo cables leave the shield toward -x, are tied here and
    # leave the base as a free service loop (route in design/v4/summary.md). Tie tunnel 4.5 x 2.5 along x.
    with Locations((TIE[0], TIE[1], FLOOR)):
        Box(5.0, 8.0, 6.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        Box(5.0, 4.5, 2.5, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    # yaw motor connector: the plug sits below the floor top on the -x side, so open the floor from the motor
    # cut-out to the base edge (plug + cable bend, matches the xy42 keep-out)
    with Locations((OUT[0] - 1.0, YM[1], 0)):
        Box(YM[0] - (42.3 + 1.0) / 2 - G.TENSION_SLOT - OUT[0] + 2.0, 20.0, FLOOR,
            align=(Align.MIN, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    # clamp / screw-down holes in the four corners (M4 or a C-clamp on the front edge)
    with Locations(*[(x, y, 0) for x in (OUT[0] + 9, OUT[1] - 9) for y in (OUT[2] + 9, OUT[3] - 9)]):
        Cylinder(4.8 / 2, FLOOR, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

part = p.part
save(part, "base")
print("base", part.bounding_box().size, round(part.volume / 1000, 1), "cm3")
