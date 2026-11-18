"""Gripper collision sweep: builds the v4 assembly at grip 0..1 with the gripper's whole-part allow_contact
pairs removed (only pins in bores, horn on spline and screws stay allowed), runs the assembly check and
lists every overlap. usage: python sim/grip_sweep.py [steps]   (writes sim/grip_sweep.json)
"""
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "design/v4"
spec = importlib.util.spec_from_file_location("ba", V4 / "build_assembly.py")
ba = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(V4))
spec.loader.exec_module(ba)

GRIP = {"crank-gear-a", "crank-gear-b", "idler-link-a", "idler-link-b", "jaw-a", "jaw-b", "gripper-base",
        "gripper-servo", "gripper-horn"}
KEEP = {("crank-gear-a", "gripper-horn")}       # screwed together


def strict(allow):
    out = []
    for a, b in allow:
        if a in GRIP and b in GRIP and (a, b) not in KEEP and (b, a) not in KEEP:
            continue
        out.append([a, b])
    return out


steps = int(sys.argv[1]) if len(sys.argv) > 1 else 6
tmp = V4 / "poses" / "_gripsweep"
results = []
for k in range(steps + 1):
    f = k / steps
    pose = {"yaw": 0, "th1": 90, "th2": 0, "wr": -90, "grip": f}
    parts, allow, _ = ba.build(pose)
    d = tmp / f"g{k}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "assembly.yaml").write_text(yaml.safe_dump({"min_clearance_mm": 0.5, "pose": pose, "parts": parts,
                                                     "allow_contact": strict(allow)}, sort_keys=False))
    r = subprocess.run([sys.executable, "-m", "mechy.design_tools", "check", f"v4/poses/_gripsweep/g{k}"],
                       cwd=ROOT, capture_output=True, text=True)
    rep = json.loads(r.stdout)
    hits = [i for i in rep.get("interferences") or [] if i.get("a") in GRIP or i.get("b") in GRIP]
    near = [i for i in rep.get("clearance_issues") or [] if i.get("a") in GRIP and i.get("b") in GRIP]
    results.append({"grip": f, "interferences": hits, "close": near})
    print(f"grip {f:.2f}: {len(hits)} overlaps", "; ".join(f"{i['a']}/{i['b']} {i.get('volume_mm3', i)}" for i in hits)[:900])
shutil.rmtree(tmp)
(ROOT / "sim/grip_sweep.json").write_text(json.dumps(results, indent=1))
