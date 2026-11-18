"""Run the viewer's planFromSpec + harnessBOM on design/v4/wiring.json under Node (three.js stubbed).
usage: python tools/test_wiring_plan.py
"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "viewers/cad/wiring.js").read_text().replace("import * as THREE from 'three';", "const THREE = {};")
nodes = json.dumps(["yaw-motor", "shoulder-motor", "elbow-motor", "wrist-motor", "gripper-servo", "yaw-switch",
                    "uno-cnc-shield", "buck-converter"])
test = f"""
import {{ planFromSpec, harnessBOM }} from './wiring.mjs';
import fs from 'fs';
const spec = JSON.parse(fs.readFileSync({json.dumps(str(ROOT / 'design/v4/wiring.json'))}, 'utf8'));
const have = new Set({nodes});
const plan = planFromSpec(spec, (n) => have.has(n));
console.log('components', plan.components.map((c) => `${{c.id}}${{c.node ? '' : ' (placed)'}}`).join(', '));
for (const c of plan.cables) console.log('cable', c.id, ':', c.from.comp, '->', c.to.comp, '|', c.conductors.map((k) => k.pin).join(' '), '|', c.kind);
console.log('controller pins', plan.components[0].pins.length);
console.log('notes', plan.notes.length, plan.notes.filter((n) => /not found|unknown/.test(n)));
const lengths = Object.fromEntries(plan.cables.map((c) => [c.id, 300]));
console.log('harness BOM', harnessBOM(plan, lengths, []).map((b) => `${{b.item}} x${{b.qty}}`).join('; '));
"""
d = Path(tempfile.mkdtemp(prefix="wiring-test-"))
(d / "wiring.mjs").write_text(src)
(d / "test.mjs").write_text(test)
r = subprocess.run([shutil.which("node"), str(d / "test.mjs")], capture_output=True, text=True)
print(r.stdout, r.stderr[-1500:])
shutil.rmtree(d)
