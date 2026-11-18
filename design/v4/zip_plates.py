"""Zip every sliced plate (.gcode.3mf + .gcode), the plate maps and the README for the printer.
usage: python design/v4/zip_plates.py   -> design/v4/gcode/v4-x1e-plates.zip
The gripper plate goes in a HOLD- folder (print only after the servo is measured).
"""
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
G = HERE / "gcode"
ORDER = {"coupon-plate1": "1-coupon-plate1", "arm-plate1": "2-arm-plate1", "arm-plate2": "3-arm-plate2",
         "arm-plate3": "4-arm-plate3", "gripper-plate1": "HOLD-gripper-plate1"}
out = G / "v4-x1e-plates.zip"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(G / "README.md", "README.md")
    for d in sorted(p for p in G.glob("*/*-plate*") if p.is_dir() and p.name in ORDER):
        folder = ORDER[d.name]
        for f in sorted(d.glob(f"{d.name}.gcode*")):
            z.write(f, f"{folder}/{f.name}")
        png = G / "plates" / f"{d.name}.png"
        if png.exists():
            z.write(png, f"{folder}/{d.name}-map.png")
with zipfile.ZipFile(out) as z:
    for i in z.infolist():
        print(f"{i.file_size / 1e6:8.2f} MB  {i.filename}")
print(out, f"{out.stat().st_size / 1e6:.1f} MB")
