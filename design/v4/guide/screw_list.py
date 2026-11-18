"""Count every screw, nut and washer in design/v4/assembly.yaml by size and where it goes, add the fasteners that are
not modelled, and write docs/screw-list.md.
usage: python tools/mpy.py design/v4/guide/screw_list.py
"""
import re
from collections import OrderedDict, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
asm = yaml.safe_load((ROOT / "design/v4/assembly.yaml").read_text())
WHERE = [  # part-id pattern -> where it goes
    (r"^yaw-motor-screw-", "yaw motor to yaw plate"), (r"^yaw-plate-screw-", "yaw plate to base posts (self-tapping)"),
    (r"^deck-screw-", "yaw pulley to turret deck"), (r"^deck-nut-", "turret deck nut traps"),
    (r"^yaw-bolt$", "yaw axle through turret, AXK and base"), (r"^yaw-nut$", "yaw axle, under the base"),
    (r"^shoulder-motor-screw-", "shoulder motor to right tower"),
    (r"^s-axle$", "shoulder axle (S)"), (r"^s-nut$", "shoulder axle nut (right tower)"),
    (r"^i-axle$", "intermediate axle (I)"), (r"^i-nut$", "intermediate axle nut (right tower slot)"),
    (r"^elbow-motor-screw-", "elbow motor to lower shank"), (r"^e-bolt$", "elbow axle"), (r"^e-nut$", "elbow axle nut"),
    (r"^wrist-motor-screw-", "wrist motor to upper shank"), (r"^wrist-axle$", "wrist axle"),
    (r"^wrist-nut$", "wrist axle nut"),
    (r"^grip-pivot$", "gear B pivot"), (r"^grip-pivot-nut$", "gear B pivot nut"),
    (r"^idler-pivot-[ab]$", "idler link pivots"), (r"^idler-pivot-nut-", "idler pivot nuts"),
    (r"^j[12]-pin-", "jaw pins (crank and idler ends)"), (r"^j[12]-nut-", "jaw pin nuts"),
    (r"^grip-mount-screw-", "gripper base to wrist pulley (self-tapping)"),
]
SIZE = [(r"m4x70", "M4 x 70 SHCS"), (r"m4x60", "M4 x 60 SHCS"), (r"m4x30", "M4 x 30 SHCS"), (r"m3x30", "M3 x 30 SHCS"),
        (r"m3x20", "M3 x 20 SHCS"), (r"m3x16", "M3 x 16 SHCS"), (r"m3x10", "M3 x 10 SHCS"), (r"m3x8", "M3 x 8 SHCS"),
        (r"m3x6", "M3 x 6 SHCS"), (r"m4-nut", "M4 hex nut"), (r"m3-nut", "M3 hex nut")]
GRIPPER = ("grip", "idler-pivot", "j1-", "j2-")
counts = OrderedDict((name, defaultdict(int)) for _, name in SIZE)
for p in asm["parts"]:
    size = next((n for pat, n in SIZE if re.search(pat, p["model"])), None)
    if not size:
        continue
    where = next((w for pat, w in WHERE if re.search(pat, p["id"])), p["id"])
    if p["id"].startswith(GRIPPER):
        where += " [gripper]"
    counts[size][where] += 1
EXTRA = {  # not modelled in the assembly
    "M3 x 8 SHCS": {"Uno to its 4 base posts (self-tapping)": 4, "XL4015 buck to its 2 base posts (self-tapping)": 2},
    "M3 x 10 SHCS": {"servo tabs to gripper base (self-tapping) [gripper]": 4},
}
for size, uses in EXTRA.items():
    for w, n in uses.items():
        counts[size][w] += n

rows, total = [], 0
for size, uses in counts.items():
    n = sum(uses.values())
    if not n:
        continue
    total += n
    rows.append((size, n, uses))
supply = {"M4 x 70 SHCS": "M4 x 70 pack (30 pcs)",
          "M4 x 30 SHCS": "M4 kit (10 in the kit)", "M4 hex nut": "M4 kit (110)", "M3 hex nut": "M3 kit (210)",
          "M3 x 30 SHCS": "M3 kit (10)", "M3 x 20 SHCS": "M3 kit (25)", "M3 x 16 SHCS": "M3 kit (25)",
          "M3 x 10 SHCS": "M3 kit (25)", "M3 x 8 SHCS": "M3 kit (40)", "M3 x 6 SHCS": "M3 kit (40)"}
md = ["# v4 arm: screws, nuts and washers", "",
      "Counted from design/v4/assembly.yaml (every modelled fastener) plus the ones the assembly doesn't model "
      "(Uno and buck posts, servo tabs). SHCS = socket head cap screw. All of them come from three Amazon packs in "
      "the cart (docs/amazon-cart.md): an M3 kit (6-30 mm + nuts), an M4 kit (6-30 mm + nuts) and M4 x 70 (also the yaw "
      "axle, on a printed 10 mm spacer, so no M4 x 60 is needed). "
      "The \"From\" column gives how many the pack holds.", "",
      "| Size | Qty | Where it goes | From |", "|---|---|---|---|"]
for size, n, uses in rows:
    where = "; ".join(f"{w} x{k}" for w, k in uses.items())
    md.append(f"| **{size}** | **{n}** | {where} | {supply.get(size, 'your stock')} |")
gr = sum(k for _, _, u in rows for w, k in u.items() if "[gripper]" in w)
md += ["", f"**{total} fasteners in all**, of which {gr} are for the gripper (needed only when the gripper is "
       "built, after the servo measurement).", "",
       "## Not in the screw packs", "",
       "- **Servo horn screws (4):** use the small self-tapping screws from the MG996R box to fix crank gear A to the "
       "horn. If the box has none: M2 x 6-8 self-tapping (crank A holes are 2.6 mm clearance).",
       "- **Pulley set screws:** come with the GT2 20T pulleys (2 per pulley, M3 grub screws; 2.5 mm or 1.5 mm hex "
       "key depending on the pulley).", "",
       "## Washers (printed, on the arm plates)", "",
       "- 7 x race washer 1.0 mm: yaw (1), shoulder axle (2), intermediate axle (2), elbow (2).",
       "- 1 x wrist washer 1.7 mm: wrist axle, between the upper shank and the wrist pulley.",
       "- 1 x yaw bolt spacer (8 x 10 mm tube): under the yaw axle M4 x 70 head, inside the turret deck hole.",
       "- No steel washers are needed.", "",
       "## Thread locking", "",
       "The gripper pivot and jaw-pin nuts must stay just loose so the parts turn: use a drop of medium "
       "threadlocker or nyloc nuts (7 x M3; the kits have plain nuts only)."]
(ROOT / "docs/screw-list.md").write_text("\n".join(md) + "\n")
for size, n, uses in rows:
    print(f"{size:14s} {n:3d}  {dict(uses)}")
print("total", total, "gripper", gr)
