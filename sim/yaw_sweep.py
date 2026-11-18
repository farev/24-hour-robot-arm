"""Yaw sweep collision check: every part that turns with the turret against every fixed base part, for
yaw = -150 .. 150 deg in steps (arm at the home pose). Bounding boxes first, then solid intersections.

usage: python sim/yaw_sweep.py <variant> [step_deg]
"""
import importlib.util
import sys
from pathlib import Path

from build123d import Extrinsic, Location, Rotation, import_step

ROOT = Path(__file__).resolve().parent.parent
variant = sys.argv[1] if len(sys.argv) > 1 else "v4"
step = int(sys.argv[2]) if len(sys.argv) > 2 else 10
spec = importlib.util.spec_from_file_location("ba", ROOT / f"design/{variant}/build_assembly.py")
BA = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BA)

home = dict(BA.POSES[None][0])
parts0, _, _ = BA.build(dict(home, yaw=0))
parts90, _, _ = BA.build(dict(home, yaw=90))
fixed = {a["id"] for a, b in zip(parts0, parts90) if a["position"] == b["position"] and a["rotation"] == b["rotation"]}
cache = {}


def solid(p):
    if p["model"] not in cache:
        cache[p["model"]] = import_step(str(ROOT / p["model"]))
    return cache[p["model"]].moved(Location(tuple(p["position"])) * Rotation(*p["rotation"], ordering=Extrinsic.XYZ))


allowed = set()
for a, b in BA.build(home)[1]:
    allowed.add((a, b)); allowed.add((b, a))
base_parts = [solid(p) for p in parts0 if p["id"] in fixed]
base_ids = [p["id"] for p in parts0 if p["id"] in fixed]
hits = []
for yaw in range(-150, 151, step):
    parts, _, _ = BA.build(dict(home, yaw=yaw))
    for p in parts:
        if p["id"] in fixed:
            continue
        s = solid(p)
        bb = s.bounding_box()
        for bid, b in zip(base_ids, base_parts):
            if (p["id"], bid) in allowed:
                continue
            bb2 = b.bounding_box()
            if (bb.min.X > bb2.max.X or bb.max.X < bb2.min.X or bb.min.Y > bb2.max.Y or bb.max.Y < bb2.min.Y
                    or bb.min.Z > bb2.max.Z or bb.max.Z < bb2.min.Z):
                continue
            v = sum(x.volume for x in s.intersect(b)) if s.intersect(b) else 0.0
            if v > 0.01:
                hits.append((yaw, p["id"], bid, round(v, 2)))
print(f"{variant}: yaw -150..150 step {step}: {len(fixed)} fixed parts, {len(hits)} collisions")
for h in hits:
    print("  yaw", h[0], h[1], "x", h[2], h[3], "mm3")
