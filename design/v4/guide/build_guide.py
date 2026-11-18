"""Step-by-step assembly guide for the v4 arm, rendered from design/v4/assembly.yaml.

Each step is a cumulative sub-assembly: the parts added in that step are blue, everything fitted before is grey. Writes design/v4/guide/stepNN/assembly.yaml, renders it with Mechy's renderer, and builds
docs/assembly-guide.md and docs/assembly-guide.pdf (one page per step).
usage: python tools/mpy.py design/v4/guide/build_guide.py [--no-render]
"""
import re
import subprocess
import sys
import textwrap
from collections import Counter
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DOCS = ROOT / "docs"
IMG = DOCS / "assembly-guide"
GREY = "#D4D4D0"
NEW = "#2F7FD8"                  # every part added in the step (belts keep their black)

S = [  # (title, part-id regexes added in this step, actions, cautions)
    ("Check the fits first",
     [],
     ["Print the fit coupon (coupon plate) before the arm plates.",
      "Press an F624ZZ into each Ø12.9-13.2 pocket by thumb: pick the size that holds the bearing without a vice. "
      "The parts are printed at 13.1.",
      "Push an M4 bolt through the 4.0-4.3 holes and an M3 through 3.4/3.6, and drive an M3 into the 2.4/2.6 pilots."],
     ["If 13.1 is loose or too tight, stop: the plates get re-sized and re-sliced first."]),
    ("Base: bearings, washer and yaw switch",
     [r"^base$", r"^yaw-bearing-(top|bottom)$", r"^yaw-race-washer$", r"^yaw-switch$"],
     ["Press the top F624ZZ into the boss from above, flange up (flush with the AXK seat).",
      "Press the bottom F624ZZ from underneath, flange down against its shoulder.",
      "Solder two wires to the KW12-3's C and NO lugs, feed them down the slot and glue the switch upright in its "
      "pocket (roller up)."],
     ["Both bearings press in by hand; never hammer PLA."]),
    ("Yaw motor",
     [r"^yaw-motor$", r"^yaw-motor-plate$", r"^yaw-motor-pulley$", r"^yaw-motor-screw-", r"^yaw-plate-screw-"],
     ["Slide a GT2 20T pulley on the yaw motor shaft, hub toward the motor, 0.5 mm above the plate; tighten the "
      "set screws on the shaft flat.",
      "Screw the motor face-up under the 3 mm yaw plate: 4 x M3 x 6 through the slots (heads in the counterbores).",
      "Lower the motor through the base floor cut-out (it stands on the table) and screw the plate to the 4 posts: "
      "4 x M3 x 16. Leave the slot screws loose for belt tension."],
     ["The motor plug faces the -x edge: it exits through the floor opening."]),
    ("Thrust bearing, yaw pulley, turret",
     [r"^axk2035$", r"^yaw-pulley$", r"^turret$", r"^deck-(screw|nut)-", r"^belt-yaw$", r"^yaw-(bolt|nut)$", r"^yaw-bolt-spacer$"],
     ["Drop 4 M3 nuts into the deck traps from the top of the turret.",
      "Screw the 120T yaw pulley under the deck: 4 x M3 x 10 from the pulley side into the nuts.",
      "Lay the AXK2035 (washer, cage, washer) on the base seat around the centring ring.",
      "Loop a 320 mm belt round the yaw pulley, set the turret on the AXK and hook the belt over the motor pulley.",
      "Drop the printed 8 x 10 mm yaw bolt spacer into the deck's centre hole, then push an M4 x 70 down through it, "
      "the pulley, the AXK and both bearings; add the race washer and the M4 nut from underneath, snug (the turret "
      "must still turn freely, and the bolt tip stays above the table).",
      "Slide the yaw motor out in its slots until the belt is taut, then tighten the plate screws."],
     ["Tension: the belt should deflect ~3 mm under a firm finger press, no more."]),
    ("Shoulder motor and intermediate pulley",
     [r"^shoulder-motor$", r"^shoulder-motor-pulley$", r"^shoulder-motor-screw-", r"^sh-compound$", r"^i-bearing-",
      r"^spacer-i", r"^i-(axle|nut|washer)", r"^belt-sh1$"],
     ["Pulley on the shoulder motor shaft (2.5 mm from the tower face), then screw the motor to the right tower's "
      "outer face: 4 x M3 x 10 through the slots, heads in the counterbores on the inner face. Leave them loose.",
      "Press an F624ZZ into each end of the 72T/36T compound pulley, flanges out; slide the two 20 mm spacer tubes "
      "inside.",
      "Loop a 200 mm belt over the compound's 72T and set the compound between the towers on the I slot.",
      "M4 x 70 through the left tower (head in the counterbore), race washer, compound, race washer, right tower; "
      "M4 nut in the right tower's slot. Hand-tight for now.",
      "Hook the 200 mm belt over the motor pulley and slide the motor along its slots until taut; tighten."],
     ["Set the motor pulley before fitting the motor: its set screws can't be reached later."]),
    ("Lower shank on the shoulder axle",
     [r"^lower-shank$", r"^lower-bearing-", r"^spacer-(s|ls)$", r"^s-(axle|nut|washer)", r"^belt-sh2$"],
     ["Press an F624ZZ into each face of the lower shank hub; put the 8 mm spacer tube inside.",
      "Loop a 320 mm belt over the compound's 36T and over the lower shank's 140T teeth.",
      "M4 x 70 through the left tower, race washer, lower shank hub, 32 mm spacer, race washer, right tower; nut in "
      "its trap. Tighten until the shank turns freely without play.",
      "Slide the I axle along its slot to tension the 320 mm belt, then tighten the I nut."],
     ["The shoulder has no self-locking: support the shank by hand until the motors are powered."]),
    ("Elbow motor and upper shank",
     [r"^elbow-motor$", r"^elbow-motor-pulley$", r"^elbow-motor-screw-", r"^upper-shank$", r"^elbow-bearing-",
      r"^spacer-e$", r"^e-(bolt|washer|nut)", r"^belt-elbow$"],
     ["Pulley on the elbow motor shaft (1.4 mm from the plate), then screw the motor to the lower shank's -y face: "
      "4 x M3 x 8 through the slots, heads in the counterbores. Loose.",
      "Press an F624ZZ into each side of the upper shank's elbow hub, 7 mm spacer inside.",
      "Loop a 320 mm belt over the upper shank's 140T and the elbow motor pulley.",
      "M4 x 30 through the lower shank (head in the counterbore), race washer, upper shank hub, race washer, M4 nut.",
      "Slide the elbow motor along the shank until the belt is taut; tighten."],
     []),
    ("Wrist motor and wrist pulley",
     [r"^wrist-motor$", r"^wrist-motor-pulley$", r"^wrist-motor-screw-", r"^wrist-(pulley|flange|bearing|axle|washer|nut)",
      r"^spacer-w$", r"^belt-wrist$"],
     ["Glue the flange ring onto the toothed face of the wrist pulley (super glue), centred over the bearing.",
      "Pulley on the wrist (HEM) motor shaft 1.3 mm out from the shank, then screw the motor to the upper shank's "
      "+y face: 4 x M3 x 8, slots loose.",
      "Press an F624ZZ into each face of the wrist pulley, 5.3 mm spacer inside.",
      "Loop a 200 mm belt over the wrist pulley and the motor pulley.",
      "M4 x 30 through the upper shank (head in the counterbore), the 1.7 mm wrist washer, the wrist pulley, M4 nut.",
      "Tension with the motor slots and tighten."],
     ["The 1.7 mm washer is the thick one; the eight 1 mm race washers go elsewhere."]),
    ("Gripper (after the servo is measured)",
     [r"^gripper-", r"^crank-gear-", r"^idler-link-", r"^jaw-", r"^grip-", r"^idler-pivot", r"^j[12]-"],
     ["Print the gripper plate only after the servo measurements (docs/servo-measure.md).",
      "Servo into the gripper base window, body toward the jaws: 4 x M3 x 10 into the tab pilots.",
      "Gear B and both idler links on their M3 x 30 pivots from the base's bed face, nuts on top left just free "
      "(thread glue).",
      "Centre the servo (GRIP 50 from the firmware), then screw crank gear A to the horn with the horn screws so its "
      "teeth mesh with B and both cranks point the same way.",
      "Jaws onto the crank and idler pins: M3 x 20, nuts underneath, just free.",
      "Screw the gripper base to the wrist pulley: 4 x M3 x 16 self-tapping."],
     ["Turn the gears by hand through the full stroke before powering: nothing should bind."]),
    ("Electronics",
     [r"^uno-cnc-shield$", r"^buck-converter$"],
     ["Screw the Uno to its 4 posts (M3 x 8) and the XL4015 to its 2 posts.",
      "Fit the A4988s (EN to EN), the microstep jumpers and the two A-axis jumpers; set Vref (docs/bring-up.md).",
      "Wire everything as in the Electronics view (hw/wiring.yaml); set the buck to 6.3 V before the servo plugs in.",
      "Tie the cables at the base's -x edge, leave a ~0.5 m loop up to the arm, and turn the yaw by hand through "
      "-150..150 to check nothing snags."],
     ["Never power the servo from the Uno's 5 V; unplugging the 24 V jack is the e-stop (lower the arm first)."]),
]

HW = [(r"m4x70", "M4 x 70"), (r"m4x60", "M4 x 60"), (r"m4x30", "M4 x 30"), (r"m3x30", "M3 x 30"), (r"m3x20", "M3 x 20"),
      (r"m3x16", "M3 x 16"), (r"m3x10", "M3 x 10"), (r"m3x8", "M3 x 8"), (r"m3x6", "M3 x 6"), (r"m4-nut", "M4 nut"),
      (r"m3-nut", "M3 nut"), (r"f624zz", "F624ZZ bearing"), (r"race_washer\.", "race washer 1 mm"),
      (r"race_washer_w", "wrist washer 1.7 mm"), (r"gt2-20t", "GT2 20T pulley"), (r"belt_(yaw|sh2|elbow)", "320 mm belt"),
      (r"belt_(sh1|wrist)", "200 mm belt")]


def hardware(parts):
    c = Counter()
    for p in parts:
        for pat, name in HW:
            if re.search(pat, p["model"]):
                c[name] += 1
                break
    return [f"{n} x {k}" for k, n in c.items()]


asm = yaml.safe_load((ROOT / "design/v4/assembly.yaml").read_text())
parts = [p for p in asm["parts"] if "keepout" not in p["id"]]
taken, steps = set(), []
for n, (title, pats, acts, warns) in enumerate(S, 1):
    new = [p for p in parts if p["id"] not in taken and any(re.search(r, p["id"]) for r in pats)]
    taken |= {p["id"] for p in new}
    steps.append({"n": n, "title": title, "new": new, "acts": acts, "warns": warns, "cum": set(taken)})
left = [p["id"] for p in parts if p["id"] not in taken]
if left:
    sys.exit(f"parts in no step: {left}")

render = "--no-render" not in sys.argv
IMG.mkdir(parents=True, exist_ok=True)
for s in steps:
    if not s["new"]:
        continue
    d = HERE / f"step{s['n']:02d}"
    d.mkdir(exist_ok=True)
    new_ids = {p["id"] for p in s["new"]}
    sub = []
    for p in parts:
        if p["id"] in s["cum"]:
            q = dict(p)
            if p["id"] not in new_ids:
                q["color"] = GREY
            elif not p["id"].startswith("belt-"):
                q["color"] = NEW
            sub.append(q)
    ids = {p["id"] for p in sub}
    allow = [a for a in asm.get("allow_contact", []) if a[0] in ids and a[1] in ids]
    (d / "assembly.yaml").write_text(yaml.safe_dump({"min_clearance_mm": 0.5, "parts": sub, "allow_contact": allow},
                                                    sort_keys=False, width=140))
    if render:
        r = subprocess.run([sys.executable, "-m", "mechy.design_tools", "render", f"v4/guide/step{s['n']:02d}"],
                           cwd=ROOT, capture_output=True, text=True)
        if r.returncode:
            sys.exit(r.stdout + r.stderr)
    for v in ("iso", "front", "side", "top"):
        src = d / "views" / f"{v}.png"
        if src.exists():
            (IMG / f"step{s['n']:02d}-{v}.png").write_bytes(src.read_bytes())
    print("step", s["n"], len(s["new"]), "new parts")

# Markdown guide
md = ["# v4 robot arm: assembly guide", "",
      "Each picture shows the arm after the step: **parts added in that step in blue, earlier parts grey**. "
      "Printed parts and hardware come from design/v4 (print plates in design/v4/gcode). Wiring is in the "
      "Electronics view (hw/wiring.yaml); power-up and calibration in docs/bring-up.md.", "",
      "Tools: 2.5 and 3 mm hex keys, small screwdriver, multimeter, soldering iron, super glue, calipers.", ""]
for s in steps:
    md += [f"## Step {s['n']}: {s['title']}", ""]
    if s["new"]:
        md += [f"![Step {s['n']}](assembly-guide/step{s['n']:02d}-iso.png)", ""]
        if s["n"] == 4 and (IMG / "detail-yaw-iso.png").exists():
            md += ["Yaw axle, exploded (turret left out): M4 x 70 (gold) -> spacer (blue, sits in the deck's centre hole) "
                   "-> yaw pulley -> AXK2035 -> top bearing -> base -> bottom bearing -> race washer -> M4 nut.", "",
                   "![Yaw axle stack](assembly-guide/detail-yaw-iso.png)", ""]
        hw = hardware(s["new"])
        printed = sorted({p["id"] for p in s["new"] if p.get("kind") == "printed"})
        if printed:
            md += ["**Printed:** " + ", ".join(printed), ""]
        if hw:
            md += ["**Hardware:** " + ", ".join(hw), ""]
    md += [f"{i}. {a}" for i, a in enumerate(s["acts"], 1)] + [""]
    md += [f"> **Caution:** {w}" for w in s["warns"]] + ([""] if s["warns"] else [])
(DOCS / "assembly-guide.md").write_text("\n".join(md))

# steps.json: the same steps as data, for the assembly-guide window (windows/assembly-guide)
import json  # noqa: E402
(HERE / "steps.json").write_text(json.dumps({
    "variant": "v4", "model": "design/v4/assembly.glb",
    "steps": [{"n": s["n"], "title": s["title"], "parts": [p["id"] for p in s["new"]],
               "printed": sorted({p["id"] for p in s["new"] if p.get("kind") == "printed"}),
               "hardware": hardware(s["new"]), "actions": s["acts"], "cautions": s["warns"],
               "image": f"docs/assembly-guide/step{s['n']:02d}-iso.png" if s["new"] else None,
               "detail": "docs/assembly-guide/detail-yaw-iso.png" if s["n"] == 4 else None} for s in steps]},
    indent=1))

# PDF: one page per step
import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

with PdfPages(DOCS / "assembly-guide.pdf") as pdf:
    for s in steps:
        fig = plt.figure(figsize=(8.5, 11))
        fig.text(0.06, 0.955, f"Step {s['n']} of {len(steps)}: {s['title']}", fontsize=16, weight="bold")
        fig.text(0.06, 0.935, "v4 robot arm assembly guide - this step in blue, earlier parts grey", fontsize=8,
                 color="#666666")
        top = 0.92
        if s["new"]:
            ax = fig.add_axes([0.06, 0.47, 0.88, 0.45])
            ax.imshow(mpimg.imread(IMG / f"step{s['n']:02d}-iso.png"))
            ax.axis("off")
            top = 0.45
        lines = []
        if s["new"]:
            printed = sorted({p["id"] for p in s["new"] if p.get("kind") == "printed"})
            if printed:
                lines += textwrap.wrap("Printed: " + ", ".join(printed), 105) + [""]
            hw = hardware(s["new"])
            if hw:
                lines += textwrap.wrap("Hardware: " + ", ".join(hw), 105) + [""]
        for i, a in enumerate(s["acts"], 1):
            w = textwrap.wrap(a, 100)
            lines += [f"{i}. {w[0]}"] + [f"    {x}" for x in w[1:]]
        for wt in s["warns"]:
            lines += [""] + textwrap.wrap("CAUTION: " + wt, 100)
        fig.text(0.06, top, "\n".join(lines), fontsize=9.5, va="top", family="DejaVu Sans", linespacing=1.45)
        pdf.savefig(fig)
        plt.close(fig)
print(DOCS / "assembly-guide.md", DOCS / "assembly-guide.pdf")
