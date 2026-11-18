"""Yaw ring pulley (120T GT2) under the turret deck: sits on the AXK2035 upper washer, carries the yaw
homing cam. Printed upside down (deck face on the bed), as modelled.

Frame: z = 0 is the deck contact face (world z 62.5), +z = world down; x = world x, y = world -y.
Assembly: rotation [180, 0, yaw] about the yaw axis, position (0, 0, 62.5).
"""
import math

from build123d import Align, BuildPart, BuildSketch, Cone, Cylinder, Location, Locations, Mode, extrude

from lib import G, M3_CB, M3_CLEAR, dims, gt2_outline, polygon, save, circle_pts

Z_TOP, Z_HUB = G.YAW_PULLEY_Z[1], G.YAW_PULLEY_Z[0]       # world 62.5 (deck) and 50.5 (hub face on the AXK)
zp = lambda zw: Z_TOP - zw                                 # world z -> print z
TEETH = (zp(G.YAW_BELT_Z + 3.1), zp(G.YAW_BELT_Z - 3.1))   # 6.2 zone around the belt centre (world 55)
H = zp(Z_HUB)                                              # 12
AXK = dims("axk2035-thrust-bearing")
SPIGOT_D = AXK["inner diameter"] - 0.3                     # centres the upper washer on its bore (snug)
SPIGOT_H = 0.8                                             # < washer thickness 1.0
CAM_R, CAM_W, CAM_ARC, CAM_H = 26.0, 4.0, 150.0, 1.2       # half-moon cam over the base switch at r 26
SCREW_R, CB_DEPTH = G.DECK_SCREW_R, 6.3                    # M3 x 10 into the deck nut traps, 0.7 past the nut

with BuildPart() as p:
    Cylinder(39.5, TEETH[0], align=(Align.CENTER, Align.CENTER, Align.MIN))          # deck-side flange / hub
    teeth, od = gt2_outline(G.YAW_T)
    extrude(teeth.moved(Location((0, 0, TEETH[0]))), amount=TEETH[1] - TEETH[0])
    root = od / 2 - 0.75
    with Locations((0, 0, TEETH[1])):                                                # 45 deg lower flange
        Cone(root, root + (H - TEETH[1]), H - TEETH[1], align=(Align.CENTER, Align.CENTER, Align.MIN))
    with Locations((0, 0, H)):
        Cylinder(SPIGOT_D / 2, SPIGOT_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # half-moon cam: presses the base switch over one half of the travel, edge at yaw 0
    with BuildSketch(Location((0, 0, H))):
        pts =([((CAM_R + CAM_W / 2) * math.cos(math.radians(a)), (CAM_R + CAM_W / 2) * math.sin(math.radians(a)))
                for a in range(0, int(CAM_ARC) + 1, 5)]
               + [((CAM_R - CAM_W / 2) * math.cos(math.radians(a)), (CAM_R - CAM_W / 2) * math.sin(math.radians(a)))
                  for a in range(int(CAM_ARC), -1, -5)])
        polygon(pts)
    extrude(amount=CAM_H)
    # centre bolt, 4 counterbored M3 holes from the hub face
    Cylinder(4.8 / 2, H + SPIGOT_H, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    scr = [(SCREW_R * math.cos(math.radians(t)), SCREW_R * math.sin(math.radians(t))) for t in G.DECK_SCREW_ANG]
    with Locations(*[(x, y, 0) for x, y in scr]):
        Cylinder(M3_CLEAR / 2, H, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    with Locations(*[(x, y, H) for x, y in scr]):
        Cylinder(M3_CB[0] / 2, CB_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
    # lightening ring pocket from the deck face (bed) is not used: keeps the bed face continuous

part = p.part
save(part, "yaw_pulley")
print("yaw_pulley", part.bounding_box().size, round(part.volume / 1000, 1), "cm3")
