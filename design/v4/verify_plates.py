"""Check every sliced plate: Bambu's X1E start G-code is in, part extrusion stays clear of the start-G-code lines
(purge / flow calibration) and the bed edges, and report time and filament.
usage: python design/v4/verify_plates.py
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE, LINE_GAP = 10.0, 8.0
ok_all = True
for gc in sorted(HERE.glob("gcode/*/*-plate*/*.gcode")):
    text = gc.read_text()
    start, body = text.split("; MACHINE_START_GCODE_END", 1)
    body = body.split("; MACHINE_END_GCODE_START")[0]
    real_start = ";===== machine: X1E" in start and "M620 S" in start and "extrude_cali_flag" in start
    lines = subprocess.run([sys.executable, str(HERE / "bed_lines.py"), str(gc)], capture_output=True, text=True).stdout
    regs = [tuple(map(float, m)) for m in re.findall(r"x ([\d.]+)\.\.([\d.]+)\s+y ([\d.]+)\.\.([\d.]+)", lines)]
    xs, ys = [], []
    for line in body.splitlines():
        if line.startswith("G1") and re.search(r" E[\d.]", line):
            mx, my = re.search(r" X([-\d.]+)", line), re.search(r" Y([-\d.]+)", line)
            if mx:
                xs.append(float(mx.group(1)))
            if my:
                ys.append(float(my.group(1)))
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    near_lines = any(y0 < r[3] + LINE_GAP and x1 > r[0] and x0 < r[1] for r in regs)
    near_edge = x0 < EDGE - 3 or y0 < EDGE - 3 or x1 > 256 - EDGE + 3 or y1 > 256 - EDGE + 3   # 3 mm skirt/brim
    info = (gc.parent / "slice_info.config").read_text()
    t = int(re.search(r'key="prediction" value="(\d+)"', info).group(1))
    w = re.search(r'key="weight" value="([\d.]+)"', info).group(1)
    good = real_start and not near_lines and not near_edge
    ok_all &= good
    print(f"{gc.stem:16s} {'OK ' if good else 'BAD'} start={'X1E' if real_start else 'GENERIC'} "
          f"lines={[tuple(round(v) for v in r) for r in regs]} parts x {x0:.1f}..{x1:.1f} y {y0:.1f}..{y1:.1f} "
          f"{t // 3600}h{t % 3600 // 60:02d}m {w} g")
print("ALL OK" if ok_all else "PROBLEMS")
