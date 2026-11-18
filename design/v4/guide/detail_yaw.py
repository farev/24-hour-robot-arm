"""Exploded close-up of the yaw axle stack (where the yaw bolt spacer goes), rendered with Mechy's renderer.
usage: python tools/mpy.py design/v4/guide/detail_yaw.py   -> docs/assembly-guide/detail-yaw-*.png
"""
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
asm = yaml.safe_load((ROOT / "design/v4/assembly.yaml").read_text())
by = {p["id"]: p for p in asm["parts"]}
# top to bottom, with the extra lift each gets in the exploded view (mm)
# (the turret is left out: its towers hide the stack; the spacer sits in the deck's Ø8.4 centre hole, on the pulley)
STACK = [("yaw-bolt", 60), ("yaw-bolt-spacer", 40), ("yaw-pulley", 18), ("axk2035", 6), ("yaw-bearing-top", -6),
         ("yaw-bearing-bottom", -24), ("yaw-race-washer", -34), ("yaw-nut", -46)]
COL = {"yaw-bolt-spacer": "#2F7FD8", "yaw-bolt": "#E8A33D"}
parts = []
for pid, lift in STACK:
    p = dict(by[pid])
    p["position"] = [p["position"][0], p["position"][1], p["position"][2] + lift]
    p["color"] = COL.get(pid, "#C8C8C4" if pid == "turret" else p.get("color", "#B0B0B0"))
    parts.append(p)
d = HERE / "detail_yaw"
d.mkdir(exist_ok=True)
(d / "assembly.yaml").write_text(yaml.safe_dump({"min_clearance_mm": 0.5, "parts": parts, "allow_contact": []},
                                                sort_keys=False, width=140))
r = subprocess.run([sys.executable, "-m", "mechy.design_tools", "render", "v4/guide/detail_yaw"], cwd=ROOT,
                   capture_output=True, text=True)
if r.returncode:
    sys.exit(r.stdout + r.stderr)
out = ROOT / "docs/assembly-guide"
for v in ("iso", "front", "side"):
    (out / f"detail-yaw-{v}.png").write_bytes((d / "views" / f"{v}.png").read_bytes())
print("written", [f"detail-yaw-{v}.png" for v in ("iso", "front", "side")])
