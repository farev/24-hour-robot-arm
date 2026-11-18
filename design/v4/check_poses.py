"""Run the assembly interference check on the home assembly and every pose. usage: python design/v4/check_poses.py"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
files = [ROOT / "design/v4/assembly.yaml"] + sorted((ROOT / "design/v4/poses").glob("*/assembly.yaml"))
for f in files:
    r = subprocess.run([sys.executable, "-m", "mechy.design_tools", "check", str(f.parent.relative_to(ROOT / "design"))],
                       cwd=ROOT, capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        print(f.parent.name, "ERROR", (r.stdout + r.stderr)[-400:])
        continue
    keys = {k: (len(v) if isinstance(v, list) else v) for k, v in d.items() if not isinstance(v, dict)}
    print(f.parent.name, json.dumps(keys)[:300])
    for k in ("interferences", "collisions", "issues"):
        for item in (d.get(k) or [])[:8]:
            print("   ", k, json.dumps(item)[:200])
