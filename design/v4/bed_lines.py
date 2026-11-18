"""Map every line the printer extrudes on the bed before the print (purge, flow calibration), from a sliced .gcode.
usage: python design/v4/bed_lines.py <file.gcode>   -> regions (x0, x1, y0, y1) in bed mm
"""
import re
import sys

g = open(sys.argv[1]).read().split("; MACHINE_START_GCODE_END")[0]
x = y = z = e = 0.0
abs_xyz = abs_e = True
segs = []
for raw in g.splitlines():
    s = raw.split(";")[0].strip()
    if not s:
        continue
    c = s.split()[0]
    if c in ("G90", "G91"):
        abs_xyz = c == "G90"
        continue
    if c in ("M82", "M83"):
        abs_e = c == "M82"
        continue
    if c == "G92":
        m = re.search(r"E(-?[\d.]+)", s)
        e = float(m.group(1)) if m else e
        continue
    if c not in ("G0", "G1", "G2", "G3"):
        continue

    def val(k, cur):
        m = re.search(k + r"(-?[\d.]+)", s)
        return cur if not m else (float(m.group(1)) if abs_xyz else cur + float(m.group(1)))

    nx, ny, nz = val("X", x), val("Y", y), val("Z", z)
    m = re.search(r"E(-?[\d.]+)", s)
    de = 0.0
    if m:
        ev = float(m.group(1))
        de = (ev - e) if abs_e else ev
        e = ev if abs_e else e + ev
    if de > 0 and nz < 1.0 and (nx != x or ny != y):
        segs.append((min(x, nx), max(x, nx), min(y, ny), max(y, ny)))
    x, y, z = nx, ny, nz

regions = []
for s in segs:
    for r in regions:
        if s[0] <= r[1] + 10 and s[1] >= r[0] - 10 and s[2] <= r[3] + 10 and s[3] >= r[2] - 10:
            r[0], r[1], r[2], r[3], r[4] = min(r[0], s[0]), max(r[1], s[1]), min(r[2], s[2]), max(r[3], s[3]), r[4] + 1
            break
    else:
        regions.append(list(s) + [1])
print(len(segs), "extruding moves below z 1 before the print")
for r in regions:
    print(f"x {r[0]:.1f}..{r[1]:.1f}  y {r[2]:.1f}..{r[3]:.1f}  ({r[4]} moves)")
