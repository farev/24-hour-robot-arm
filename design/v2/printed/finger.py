"""Gripper fingers A and B: 16T module 1.5 spur gear + finger in one print, meshing 1:1 so the jaws close
symmetrically. A screws onto the gripper servo's round horn; B turns on an M3 pivot. Printed flat
(the face away from the horn on the bed), as modelled. Writes finger_a.step and finger_b.step.

Frame: origin on the gear axis, x = g (toward the fingertip), y = -h (A: toward the gripper centre
line is -y; B: +y), z = world +y; bed z = 0 is world y = FINGER_Y[0].
"""
from build123d import Align, Axis, Box, BuildPart, BuildSketch, Cylinder, Locations, Mode, Polygon, extrude

from lib import G, gear_sketch, save

T = G.FINGER_Y[1] - G.FINGER_Y[0]           # 6
M, Z = G.GEAR_M, G.GEAR_T
HALF_GAP = 1.0                              # closed: pads 2 mm apart
CENTRE = M * Z / 2                          # 12: gear axis to the gripper centre line
TIP_X = G.TOOL_DOWN - G.GRIP_SERVO_G        # 55: pad end along g from the gear axis
PAD = (TIP_X - 28.0, TIP_X)                 # pad length along g
PAD_T = 6.0
HORN_SCREW_R = 7.0                          # [est] round horn screw circle; head counterbore Ø3.8 keeps 1.2 mm to the gear root


def finger(kind):
    s = -1 if kind == "a" else 1            # pad side in local y (toward the centre line)
    face = s * (CENTRE - HALF_GAP)          # pad inner face y
    back = face - s * PAD_T
    t = T if kind == "a" else T - 0.6        # B 0.6 thinner: clears the gripper servo horn rim beside it
    with BuildPart() as p:
        g, rp, ra, rf = gear_sketch(M, Z, backlash=0.15)
        if kind == "b":                      # half a tooth pitch so B's gap faces A's tooth on the centre line
            g = g.rotate(Axis.Z, 180.0 / Z)
        extrude(g, amount=t)
        arm = [(6, -s * 5), (18, -s * 5), (PAD[0], back), (PAD[1], back), (PAD[1] + 2, (face + back) / 2),
               (PAD[1], face), (PAD[0], face), (18, s * 6), (6, s * 6)]
        with BuildSketch():
            Polygon(*arm, align=None)
        extrude(amount=t)
        # grip ridges on the pad face (0.6 mm deep grooves across the pad)
        for x in range(int(PAD[0]) + 3, int(PAD[1]) - 1, 4):
            with Locations((x, face, 0)):
                Box(1.2, 1.2, t, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        if kind == "a":
            # horn: centre access hole for the spline screw, 4 screw holes with head counterbores on the bed face
            Cylinder(3.5, t, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)   # Ø7 access to the spline screw
            pts = [(HORN_SCREW_R * c, HORN_SCREW_R * q, 0) for c, q in ((1, 0), (0, 1), (-1, 0), (0, -1))]
            with Locations(*pts):
                Cylinder(2.2 / 2, t, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
                Cylinder(3.8 / 2, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        else:
            Cylinder(3.4 / 2, t, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)   # running on M3 (rules §1)
    return p.part


for k in ("a", "b"):
    part = finger(k)
    save(part, f"finger_{k}")
    print(f"finger_{k}", part.bounding_box().size, round(part.volume / 1000, 1), "cm3")
