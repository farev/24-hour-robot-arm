"""ISO 4762 socket head cap screws and ISO 4032 nuts used in v2, from standard_parts/fasteners_*.csv.

Screw frame: axis Z, origin at the underside of the head (the bearing face), head toward +Z,
shank toward -Z (length = nominal length). Nut frame: axis Z, bottom face at z = 0.
Writes m<d>x<l>-shcs.step and m<d>-nut.step.
"""
import csv
from pathlib import Path

from build123d import Align, BuildPart, Cylinder, Locations, Mode, RegularPolygon, extrude, BuildSketch, export_step

HERE = Path(__file__).parent
DATA = Path("/Users/fabianarevalo/Documents/Mechy/engine/mechy/data/standard_parts")
shcs = {r["thread"]: r for r in csv.DictReader(open(DATA / "fasteners_iso4762_shcs.csv"))}
nuts = {r["thread"]: r for r in csv.DictReader(open(DATA / "fasteners_hex_nuts.csv"))}
SCREWS = [("M3", 6), ("M3", 8), ("M3", 10), ("M3", 16), ("M3", 30), ("M4", 20), ("M4", 25), ("M4", 30), ("M4", 60), ("M4", 70)]

for th, length in SCREWS:
    r = shcs[th]
    d = float(th[1:])
    with BuildPart() as s:
        Cylinder(float(r["head_dia_dk_mm"]) / 2, float(r["head_height_k_mm"]), align=(Align.CENTER, Align.CENTER, Align.MIN))
        Cylinder(d / 2 - 0.05, length, align=(Align.CENTER, Align.CENTER, Align.MAX))
    export_step(s.part, str(HERE / f"{th.lower()}x{length}-shcs.step"))

for th in ("M3", "M4"):
    r = nuts[th]
    with BuildPart() as n:
        with BuildSketch():
            RegularPolygon(float(r["width_across_corners_e_min_mm"]) / 2 + 0.05, 6)
        extrude(amount=float(r["height_iso4032_mm"]))
        Cylinder(float(th[1:]) / 2, 10, mode=Mode.SUBTRACT)
    export_step(n.part, str(HERE / f"{th.lower()}-nut.step"))
print("ok")
