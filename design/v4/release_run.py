"""Print release, steps 1-2: regenerate every v4 printed part from source, then printcheck each STEP.
usage: python design/v4/release_run.py   (writes design/v4/printcheck.json)
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PR = ROOT / "design/v4/printed"
SKIP = {"lib.py", "style.py"}

for src in sorted(PR.glob("*.py")):
    if src.name in SKIP:
        continue
    r = subprocess.run([sys.executable, str(src)], cwd=ROOT, capture_output=True, text=True)
    print(("ok   " if r.returncode == 0 else "FAIL ") + src.name, (r.stdout.strip().splitlines() or [""])[-1][:90])
    if r.returncode:
        print(r.stderr[-800:])

out = {}
for step in sorted(PR.glob("*.step")):
    r = subprocess.run([sys.executable, "-m", "mechy.design_tools", "printcheck", str(step.relative_to(ROOT))],
                       cwd=ROOT, capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        out[step.stem] = {"error": (r.stdout + r.stderr)[-400:]}
        continue
    out[step.stem] = d
    flags = []
    if d.get("thin_walls"):
        flags.append(f"thin_walls (min {d.get('min_wall_mm')})")
    if "xyz" not in [o.get("axes") for o in d.get("fitting_orientations") or []]:
        flags.append("no xyz fit")
    if (d.get("bed_contact_mm2") or 0) < 1:
        flags.append(f"bed {d.get('bed_contact_mm2')}")
    for k in ("floating_bodies", "non_solid_bodies", "small_holes"):
        if d.get(k):
            flags.append(f"{k} {d[k]}")
    if d.get("overhang_area_mm2"):
        flags.append(f"overhang {d['overhang_area_mm2']} mm2")
    for w in d.get("warnings") or []:
        flags.append("warn: " + str(w)[:140])
    print(f"{step.stem:22s} wall {d.get('min_wall_mm')}", "; ".join(flags) or "clean", "" if d.get("ok") else "NOT OK")
(ROOT / "design/v4/printcheck.json").write_text(json.dumps(out, indent=1))
