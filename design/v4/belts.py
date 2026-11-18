"""v3 installed belts (pitch line wrapped on both pulleys) for the assembly check -> design/v3/bought/.
belt_sh1 (20T motor -> 72T, y 20) and belt_sh2 (36T -> 140T on the lower shank, y -21.25): turret frame
(world at yaw 0). belt_yaw: world frame. belt_elbow: lower-shank frame (origin S, x along the shank,
z in-plane, world y = -3.1), placed with Ry(-th1) at S. belt_wrist: upper-shank frame (origin E, world
y = -4.1), placed with Ry(-th2) at E.
"""
import importlib.util
import math
from pathlib import Path

from build123d import BuildPart, BuildSketch, Mode, Plane, Polygon, export_step, extrude

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("geometry", HERE / "geometry.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)
(HERE / "bought").mkdir(exist_ok=True)


def loop_pts(c1, r1, c2, r2, n=90):
    dx, dy = c2[0] - c1[0], c2[1] - c1[1]
    d = math.hypot(dx, dy)
    base = math.atan2(dy, dx)
    beta = math.acos((r1 - r2) / d)
    pts = [(c1[0] + r1 * math.cos(a), c1[1] + r1 * math.sin(a))
           for a in [base + beta + (2 * math.pi - 2 * beta) * i / n for i in range(n + 1)]]
    pts += [(c2[0] + r2 * math.cos(a), c2[1] + r2 * math.sin(a))
            for a in [base - beta + 2 * beta * i / n for i in range(n + 1)]]
    return pts


def length(c1, r1, c2, r2):
    d = math.hypot(c2[0] - c1[0], c2[1] - c1[1])
    beta = math.acos((r1 - r2) / d)
    return 2 * d * math.sin(beta) + r1 * (2 * math.pi - 2 * beta) + r2 * 2 * beta


def band(c1, t1, c2, t2, plane, name):
    R1, R2 = G.pd(t1) / 2, G.pd(t2) / 2
    with BuildPart() as p:
        with BuildSketch(plane):
            Polygon(*loop_pts(c1, R1 + 0.63, c2, R2 + 0.63), align=None)
            Polygon(*loop_pts(c1, R1 - 0.75, c2, R2 - 0.75), align=None, mode=Mode.SUBTRACT)
        extrude(amount=G.BELT_W / 2, both=True)
    export_step(p.part, str(HERE / "bought" / f"{name}.step"))
    print(name, "pitch length", round(length(c1, R1, c2, R2), 1))


XZ = lambda y: Plane.XZ.offset(-y)
band(G.I_PT, G.SH_T1, G.SH_MOTOR, G.MOTOR_T, XZ(G.BELT_SH1), "belt_sh1")
band(G.S, G.SH_T3, G.I_PT, G.SH_T2, XZ(G.BELT_SH2), "belt_sh2")
band((0.0, 0.0), G.YAW_T, (-G.C_YAW, 0.0), G.MOTOR_T, Plane.XY.offset(G.YAW_BELT_Z), "belt_yaw")
band((G.L1, 0.0), G.ELBOW_T, (G.L1 - G.C_EL, 0.0), G.MOTOR_T, XZ(G.BELT_EL), "belt_elbow")
band((G.L2, 0.0), G.WRIST_T, (G.L2 - G.C_WR, 0.0), G.MOTOR_T, XZ(G.BELT_WR), "belt_wrist")
