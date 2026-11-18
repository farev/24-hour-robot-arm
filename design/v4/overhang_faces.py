"""List downward-facing faces (normal steeper than 45 deg from vertical) above the bed for v4 printed parts.
usage: python design/v4/overhang_faces.py <part> [<part> ...]   (STEP names in design/v4/printed)
"""
import sys
from pathlib import Path

from build123d import import_step

PR = Path(__file__).resolve().parent / "printed"
for name in sys.argv[1:]:
    part = import_step(str(PR / f"{name}.step"))
    z0 = part.bounding_box().min.Z
    rows = []
    for f in part.faces():
        try:
            n = f.normal_at(f.center())
        except Exception:  # noqa: BLE001
            continue
        if n.Z > -0.707:
            continue
        bb = f.bounding_box()
        if bb.min.Z - z0 < 0.05:
            continue
        rows.append((round(bb.min.Z - z0, 2), round(f.area, 1), round(bb.size.X, 1), round(bb.size.Y, 1),
                     round(bb.center().X, 1), round(bb.center().Y, 1), f.geom_type if isinstance(f.geom_type, str) else f.geom_type.name))
    rows.sort()
    print(f"== {name}: {len(rows)} faces, {round(sum(r[1] for r in rows), 1)} mm2")
    for r in rows:
        print(f"  z {r[0]:6} area {r[1]:7}  size {r[2]} x {r[3]}  at ({r[4]}, {r[5]})  {r[6]}")
