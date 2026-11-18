"""v4 wrist pulley: 60T GT2 (3:1 from the HEM wrist stepper) turning on two F624 on the M4 wrist axle; the
gripper base screws to its bed face. Printed with the gripper face (world y = -17) on the bed, as modelled.
Also writes wrist_flange.step: the belt flange ring for the +y side (design review 2026-11-06), printed flat and
glued (super glue) onto the pulley's top face over the tooth tips; a printed-in flange there would overhang.

Frame: origin on the wrist axis W at the gripper face, +z = world +y (top z = 15.3 is world y = -1.7).
Assembly: R = (g, -h, +y) columns rotated with the wrist angle, position (W_x, -17, W_z); the ring at y -1.7.
"""
import math

from build123d import Align, BuildPart, Cylinder, Location, Locations, Mode, extrude

from lib import BRG_D, BRG_W, FLANGE_D, FLANGE_T, G, gt2_outline, save

Y0, Y1 = G.Y["wrist_pulley"]                 # -17 .. -1.7
H = Y1 - Y0                                  # 15.3
TEETH_Z = (G.BELT_WR - 3.1 - Y0, G.BELT_WR + 3.1 - Y0)   # 9.1 .. 15.3
HUB_R = 21.0                                 # full disc under the teeth = the belt flange (no overhang)
SCREW_R = G.WRIST_SCREW_R                    # gripper base screws: M3 x 16 self-tapping, Ø2.6 pilots 12 deep

with BuildPart() as p:
    Cylinder(HUB_R, TEETH_Z[0], align=(Align.CENTER, Align.CENTER, Align.MIN))
    teeth, od = gt2_outline(G.WRIST_T)
    extrude(teeth.moved(Location((0, 0, TEETH_Z[0]))), amount=TEETH_Z[1] - TEETH_Z[0])
    # two F624, flanges at both faces, Ø7.6 between for the race tube
    Cylinder(3.8, H, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    Cylinder(BRG_D / 2, BRG_W, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    with Locations((0, 0, H)):
        Cylinder(BRG_D / 2, BRG_W, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
        Cylinder(FLANGE_D / 2, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
    with Locations(*[(SCREW_R * math.cos(math.radians(a)), SCREW_R * math.sin(math.radians(a)), 0) for a in (45, 135, 225, 315)]):
        Cylinder(1.3, 12.0, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

part = p.part
save(part, "wrist_pulley")
print("wrist_pulley", part.bounding_box().size, round(part.volume / 1000, 1), "cm3")

FID, FOD, FT = G.WRIST_FLANGE                # clears the Ø15.4 bearing counterbore and the Ø9 washer
with BuildPart() as f:
    Cylinder(FOD / 2, FT, align=(Align.CENTER, Align.CENTER, Align.MIN))
    Cylinder(FID / 2, FT, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
save(f.part, "wrist_flange")
print("wrist_flange", f.part.bounding_box().size)
