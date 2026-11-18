"""Top-down map of every sliced plate, drawn from the G-code itself: the printed area of each part (all layers,
grey) with the first layer on top (colour), the purge / flow-calibration lines the X1E start G-code draws (red),
the bed exclusion area and the 10 mm edge band (hatched), and part labels.
usage: python tools/mpy.py design/v4/plate_maps.py     -> design/v4/gcode/plates/<plate>.png
"""
import re
import struct
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "gcode" / "plates"
OUT.mkdir(parents=True, exist_ok=True)
BED, EDGE = 256.0, 10.0
sys.path.insert(0, str(HERE))


def moves(text):
    """Extruding XY segments (x0, y0, x1, y1, z) with absolute/relative modes tracked."""
    x = y = z = e = 0.0
    abs_xyz = abs_e = True
    out = []
    for raw in text.splitlines():
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
        nx, ny, nz = x, y, z
        for k in "XYZ":
            m = re.search(k + r"(-?[\d.]+)", s)
            if m:
                v = float(m.group(1)) if abs_xyz else {"X": x, "Y": y, "Z": z}[k] + float(m.group(1))
                nx, ny, nz = (v, ny, nz) if k == "X" else (nx, v, nz) if k == "Y" else (nx, ny, v)
        m = re.search(r"E(-?[\d.]+)", s)
        de = 0.0
        if m:
            ev = float(m.group(1))
            de, e = ((ev - e), ev) if abs_e else (ev, e + ev)
        if de > 0 and (nx != x or ny != y):
            out.append((x, y, nx, ny, nz))
        x, y, z = nx, ny, nz
    return np.array(out) if out else np.zeros((0, 5))


def stl_centroid(path):
    b = path.read_bytes()
    n = struct.unpack("<I", b[80:84])[0]
    v = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))["v"]
    v = v.reshape(-1, 3)
    return (v[:, 0].min() + v[:, 0].max()) / 2, (v[:, 1].min() + v[:, 1].max()) / 2


NICE = {"yaw-race-washer": "washer", "spacer-i": "sp-I", "spacer-s": "sp-S", "spacer-ls": "sp-LS", "spacer-e": "sp-E",
        "spacer-w": "sp-W", "wrist-washer": "wrist washer", "idler-link-a": "idler"}
for gc in sorted(HERE.glob("gcode/*/*-plate*/*.gcode")):
    text = gc.read_text()
    start, body = text.split("; MACHINE_START_GCODE_END", 1)
    body = body.split("; MACHINE_END_GCODE_START")[0]
    pre = moves(start)
    pre = pre[pre[:, 4] < 1.0] if len(pre) else pre
    parts = moves(body)
    z1 = parts[:, 4].min()
    first = parts[parts[:, 4] <= z1 + 1e-3]
    info = (gc.parent / "slice_info.config").read_text()
    t = int(re.search(r'key="prediction" value="(\d+)"', info).group(1))
    w = float(re.search(r'key="weight" value="([\d.]+)"', info).group(1))

    fig, ax = plt.subplots(figsize=(7.6, 8.2), dpi=110)
    ax.add_patch(Rectangle((0, 0), BED, BED, fc="#F4F4F2", ec="#333333", lw=1.5))
    for r in ((0, 0, BED, EDGE), (0, BED - EDGE, BED, EDGE), (0, 0, EDGE, BED), (BED - EDGE, 0, EDGE, BED)):
        ax.add_patch(Rectangle(r[:2], r[2], r[3], fc="none", ec="#BBBBBB", hatch="////", lw=0))
    ax.add_patch(Rectangle((0, 0), 18, 28, fc="#E9C46A", ec="#B08900", alpha=0.6, lw=1))
    ax.text(9, 31, "no-print\nzone", ha="center", va="bottom", fontsize=7, color="#7A5C00")
    ax.add_patch(Rectangle((0, 12), BED, 8, fc="#F8D7DA", ec="none", alpha=0.7))
    ax.text(250, 16, "8 mm clearance", ha="right", va="center", fontsize=7, color="#A33")
    if len(pre):
        ax.add_collection(LineCollection(pre[:, [0, 1, 2, 3]].reshape(-1, 2, 2), colors="#D62828", lw=1.6))
        ax.text(128, 6.5, "purge + flow-calibration lines (X1E start G-code)", ha="center", va="center", fontsize=7,
                color="#D62828")
    step = max(1, len(parts) // 120000)
    ax.add_collection(LineCollection(parts[::step, [0, 1, 2, 3]].reshape(-1, 2, 2), colors="#B9C3CC", lw=0.4))
    ax.add_collection(LineCollection(first[:, [0, 1, 2, 3]].reshape(-1, 2, 2), colors="#2A9D8F", lw=0.5))
    lay = HERE / "gcode" / gc.parent.parent.name / "layout" / gc.parent.name.split("-")[-1]
    for stl in sorted(lay.glob("*.stl")):
        name = stl.stem.rsplit("-", 1)[0]
        if name == "yaw-race-washer" and not stl.stem.endswith("-1"):
            continue
        cx, cy = stl_centroid(stl)
        ax.text(cx, cy - 2.0, NICE.get(name, name), ha="center", va="center", fontsize=7.5, color="#1D3557",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.75))
    x0, x1, y0, y1 = parts[:, [0, 2]].min(), parts[:, [0, 2]].max(), parts[:, [1, 3]].min(), parts[:, [1, 3]].max()
    ax.set_xlim(-6, BED + 6)
    ax.set_ylim(-6, BED + 6)
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm)  - front of the printer is at the bottom")
    ax.set_ylabel("y (mm)")
    ax.set_title(f"{gc.stem}: {t // 3600} h {t % 3600 // 60:02d} min, {w:.0f} g PLA\n"
                 f"parts x {x0:.0f}-{x1:.0f}, y {y0:.0f}-{y1:.0f} mm  (grey: all layers, teal: first layer)",
                 fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / f"{gc.stem}.png")
    plt.close(fig)
    print(OUT / f"{gc.stem}.png")
