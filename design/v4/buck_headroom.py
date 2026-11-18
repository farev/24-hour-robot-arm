"""Headroom above the XL4015 buck in the v4 assembly (home pose). For every other part, the lowest point inside
(a) the column straight above the buck footprint and (b) the ring the turret sweeps over the buck (the yaw axis is
the world z axis), so header pins + Dupont plugs on top of the buck can be checked.
usage: python tools/mpy.py design/v4/buck_headroom.py
"""
import math
from pathlib import Path

import yaml
from build123d import Box, Cylinder, Location, Pos, import_step

ROOT = Path(__file__).resolve().parents[2]
A = yaml.safe_load((ROOT / "design/v4/assembly.yaml").read_text())


def placed(p):
    s = import_step(str(ROOT / p["model"]))
    return Location(tuple(p["position"]), tuple(p["rotation"])) * s


buck = placed(next(p for p in A["parts"] if p["id"] == "buck-converter"))
bb = buck.bounding_box()
print(f"buck x {bb.min.X:.1f}..{bb.max.X:.1f}  y {bb.min.Y:.1f}..{bb.max.Y:.1f}  z {bb.min.Z:.1f}..{bb.max.Z:.1f}")
H = 200.0
col = Pos((bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2, bb.max.Z + H / 2) * Box(bb.size.X + 4, bb.size.Y + 4, H)
corners = [(x, y) for x in (bb.min.X, bb.max.X) for y in (bb.min.Y, bb.max.Y)]
r_out = max(math.hypot(x, y) for x, y in corners) + 2
r_in = max(0.0, math.hypot(max(bb.min.X, min(0, bb.max.X)), max(bb.min.Y, min(0, bb.max.Y))) - 2)
ring = Pos(0, 0, bb.max.Z + H / 2) * (Cylinder(r_out, H) - Cylinder(r_in, H))
print(f"sweep ring r {r_in:.1f}..{r_out:.1f}")
print("-- static parts over the buck PCB (+2 mm), where exactly:")
board_top = bb.min.Z + 1.6
tight = Pos((bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2, board_top + 25) * Box(bb.size.X + 4, bb.size.Y + 4, 50)
for pid in ("base", "yaw-motor-plate", "yaw-motor", "uno-cnc-shield"):
    p = next((q for q in A["parts"] if q["id"] == pid), None)
    if not p:
        continue
    c = placed(p) & tight
    if c is not None and c.volume > 1e-3:
        b = c.bounding_box()
        print(f"{pid:18s} x {b.min.X:.1f}..{b.max.X:.1f}  y {b.min.Y:.1f}..{b.max.Y:.1f}  z {b.min.Z:.1f}..{b.max.Z:.1f}  vol {c.volume:.0f}")
print(f"board top z {board_top:.1f}")
print("-- every part, column and sweep ring:")
for p in A["parts"]:
    if p["id"] in ("buck-converter",):
        continue
    try:
        s = placed(p)
    except Exception as e:  # noqa: BLE001
        print(p["id"], "load failed", e)
        continue
    out = []
    for name, region in (("column", col), ("ring", ring)):
        try:
            c = s & region
            vol = c.volume if c is not None else 0.0
        except Exception:  # noqa: BLE001
            vol = 0.0
        if vol > 1e-3:
            out.append(f"{name} min z {c.bounding_box().min.Z:.1f} (gap {c.bounding_box().min.Z - bb.max.Z:.1f})")
    if out:
        print(f"{p['id']:28s} " + " | ".join(out))
