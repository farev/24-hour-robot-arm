"""GT2-6 320 mm closed belts as installed (pitch line wrapped on both pulleys), for the assembly check.
Writes design/v2/bought/belt_{shoulder,elbow,yaw}.step. Belt band: pitch line -0.75 (tooth tips)
to +0.63 (back), 6 mm wide. Frames: belt_shoulder/elbow in the turret frame (world at yaw 0, belt
centre plane at y = BELT_Y_L / BELT_Y_R); belt_yaw in the world frame at z = YAW_BELT_Z.
Prints the computed loop length so it can be compared with 320.
"""
import importlib.util
import math
from pathlib import Path

from build123d import BuildPart, BuildSketch, Plane, Polygon, extrude, export_step, Mode

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("geometry", HERE / "geometry.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)
(HERE / "bought").mkdir(exist_ok=True)


def loop_pts(c1, r1, c2, r2, n=90):
    """Open-belt outline around circles c1 (r1) and c2 (r2): returns points CCW."""
    dx, dy = c2[0] - c1[0], c2[1] - c1[1]
    d = math.hypot(dx, dy)
    base = math.atan2(dy, dx)
    beta = math.acos((r1 - r2) / d)              # tangent angle from the centre line
    pts = []
    a0, a1 = base + beta, base + 2 * math.pi - beta
    for i in range(n + 1):                         # big wrap on circle 1
        a = a0 + (a1 - a0) * i / n
        pts.append((c1[0] + r1 * math.cos(a), c1[1] + r1 * math.sin(a)))
    b0, b1 = base - beta, base + beta              # small wrap on circle 2
    for i in range(n + 1):
        a = b0 + (b1 - b0) * i / n
        pts.append((c2[0] + r2 * math.cos(a), c2[1] + r2 * math.sin(a)))
    return pts


def length(c1, r1, c2, r2):
    d = math.hypot(c2[0] - c1[0], c2[1] - c1[1])
    beta = math.acos((r1 - r2) / d)
    return 2 * d * math.sin(beta) + r1 * (2 * math.pi - 2 * beta) + r2 * 2 * beta


def band(c1, R1, c2, R2, plane, name):
    with BuildPart() as p:
        with BuildSketch(plane):
            Polygon(*loop_pts(c1, R1 + 0.63, c2, R2 + 0.63), align=None)
            Polygon(*loop_pts(c1, R1 - 0.75, c2, R2 - 0.75), align=None, mode=Mode.SUBTRACT)
        extrude(amount=G.BELT_W / 2, both=True)
    export_step(p.part, str(HERE / "bought" / f"{name}.step"))
    print(name, "pitch length", round(length(c1, R1, c2, R2), 1), "mm")


Rb, Rs, Ry = G.pd(G.ARM_T) / 2, G.pd(G.MOTOR_T) / 2, G.pd(G.YAW_T) / 2
S, M = (G.S_X, G.S_Z), G.ARM_MOTOR
# XZ plane: local (x, y) = world (x, z); its normal is -y, so offset(-y) puts it at world y
band(S, Rb, M, Rs, Plane.XZ.offset(-G.BELT_Y_L), "belt_shoulder")
band(S, Rb, M, Rs, Plane.XZ.offset(-G.BELT_Y_R), "belt_elbow")
band((0.0, 0.0), Ry, (-G.C_YAW, 0.0), Rs, Plane.XY.offset(G.YAW_BELT_Z), "belt_yaw")
