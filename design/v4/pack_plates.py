"""Nest printed parts onto as few 256 x 256 build plates as possible, from their real outlines.
usage: python design/v4/pack_plates.py <set>     set: arm | gripper | coupon
Each part is printed as modelled (bed face down) and only turned about Z. Outlines are rasterised at 0.5 mm,
grown by half the part spacing, and placed first-fit-decreasing (largest first, 24 angles, bottom-left).
Writes design/v4/gcode/<set>/layout/plate<N>/<part>-<k>.stl in bed coordinates and layout.json.
"""
import csv
import json
import shutil
import struct
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation
from scipy.signal import fftconvolve

HERE = Path(__file__).resolve().parent
BED, RES = 256.0, 0.5            # mm, mm per cell
MARGIN, SPACING = 10.0, 5.0      # keep-off from the bed edges (user 2026-11-06: not too close), gap between parts
FRONT_LINES_Y = 12.0             # X1E start G-code draws its purge + flow-calibration lines at y 1..12, x 18..240
LINE_CLEAR = 10.0                # keep parts this far behind them: 8 mm + the 2 mm Bambu Studio shifts every
                                 # loaded plate toward the front (measured: coupon laid out y 20, sliced y 18.4)
GRIPPER = {"gripper-base", "crank-gear-a", "crank-gear-b", "idler-link-a", "jaw-a", "jaw-b"}
ANGLES = range(0, 360, 15)


def read_stl(path):
    b = Path(path).read_bytes()
    if b[:5] == b"solid" and b"facet" in b[:400]:
        v = [list(map(float, l.split()[1:4])) for l in b.decode().splitlines() if l.strip().startswith("vertex")]
        return np.array(v).reshape(-1, 3, 3)
    n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(float)


def write_stl(path, tris):
    tris = np.asarray(tris, np.float32)
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(tris), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    rec["n"], rec["v"] = n, tris.reshape(-1, 9)
    Path(path).write_bytes(b"mechy plate layout".ljust(80, b" ") + struct.pack("<I", len(tris)) + rec.tobytes())


def raster(xy_tris, shape, origin):
    """Fill the projected triangles (N, 3, 2) into a boolean grid; origin = world xy of cell (0, 0)."""
    g = np.zeros(shape, bool)
    for t in xy_tris:
        c = (t - origin) / RES
        x0, y0 = np.floor(c.min(0)).astype(int)
        x1, y1 = np.ceil(c.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, shape[1] - 1), min(y1, shape[0] - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        (ax, ay), (bx, by), (cx, cy) = c
        d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(d) < 1e-9:
            continue
        l1 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / d
        l2 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / d
        inside = (l1 >= -0.02) & (l2 >= -0.02) & (l1 + l2 <= 1.02)
        g[y0:y1 + 1, x0:x1 + 1] |= inside
    return g


def part_masks(tris):
    """Per angle: (grown mask, rotated triangles centred on the outline's bbox centre)."""
    out = []
    grow = int(round(SPACING / 2 / RES))
    disk = np.hypot(*np.mgrid[-grow:grow + 1, -grow:grow + 1]) <= grow
    e1, e2 = tris[:, 1, :2] - tris[:, 0, :2], tris[:, 2, :2] - tris[:, 0, :2]
    keep = np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]) > 1e-6        # triangles with projected area
    for a in ANGLES:
        r = np.radians(a)
        R = np.array([[np.cos(r), -np.sin(r)], [np.sin(r), np.cos(r)]])
        t = tris.copy()
        t[..., :2] = tris[..., :2] @ R.T
        lo, hi = t[..., :2].reshape(-1, 2).min(0), t[..., :2].reshape(-1, 2).max(0)
        t[..., :2] -= (lo + hi) / 2
        t[..., 2] -= t[..., 2].min()
        half = (hi - lo) / 2 + SPACING / 2 + RES
        n = np.ceil(2 * half / RES).astype(int) + 1
        m = raster(t[keep][..., :2], (n[1], n[0]), -half)
        out.append((a, binary_dilation(m, disk), t, -half))
    return out


which = sys.argv[1] if len(sys.argv) > 1 else "arm"
rows = list(csv.DictReader((HERE / "print_list.csv").open()))
items = []
for r in rows:
    part = r["part"].split(" (")[0]
    sel = {"coupon": part == "fit-coupon", "gripper": part in GRIPPER}.get(which, part not in GRIPPER | {"fit-coupon"})
    if sel:
        tris = read_stl(HERE / r["stl"])
        masks = part_masks(tris)
        for k in range(int(r["qty"])):
            items.append({"part": part, "k": k + 1, "masks": masks, "area": int(masks[0][1].sum())})
items.sort(key=lambda it: -it["area"])

ncell = int(BED / RES)
edge = int(MARGIN / RES) - int(SPACING / 2 / RES)
EXCLUDE = (18.0, 28.0)           # X1E bed_exclude_area (front-left, x 0..18, y 0..28), from the machine preset


def blank():
    """Empty plate with the exclusion area (plus the part spacing) marked as taken."""
    g = np.zeros((ncell, ncell), bool)
    g[:int((EXCLUDE[1] + 3.0) / RES), :int((EXCLUDE[0] + 3.0) / RES)] = True
    g[:int((FRONT_LINES_Y + LINE_CLEAR - SPACING / 2) / RES), :] = True   # calibration strip across the front
    return g


def place(occ, it):
    """Best spot for `it` on plate `occ`: the one that keeps the union of placed parts most compact."""
    grid = occ["grid"]
    rows, cols = np.nonzero(grid)
    bb = (rows.min(), rows.max(), cols.min(), cols.max()) if len(rows) else None
    best = None
    for a, m, t, org in it["masks"]:
        if m.shape[0] > ncell - 2 * edge or m.shape[1] > ncell - 2 * edge:
            continue
        area = grid[edge:ncell - edge, edge:ncell - edge].astype(float)
        ov = fftconvolve(area, m[::-1, ::-1].astype(float), mode="valid")
        free = np.argwhere(ov < 0.5) + edge
        if not len(free):
            continue
        r0, c0 = free[:, 0], free[:, 1]
        if bb is None:
            score = r0 + c0 + 0.0
        else:   # bounding box of the union after placing, then bottom-left as a tie-break
            h = np.maximum(bb[1], r0 + m.shape[0]) - np.minimum(bb[0], r0)
            w = np.maximum(bb[3], c0 + m.shape[1]) - np.minimum(bb[2], c0)
            score = h * w + 0.01 * (r0 + c0)
        j = int(np.argmin(score))
        if best is None or score[j] < best[0]:
            best = (score[j], a, m, t, org, free[j])
    return best


def pack(order):
    plates = []
    for it in order:
        for occ in plates + [None]:
            new = occ is None
            occ = {"grid": blank(), "parts": []} if new else occ
            best = place(occ, it)
            if best:
                if new:
                    plates.append(occ)
                _, a, m, t, org, (row, col) = best
                occ["grid"][row:row + m.shape[0], col:col + m.shape[1]] |= m
                # mask cell (0, 0) is world xy `org` of the centred part; that cell is bed xy (col, row) * RES
                shift = np.array([col * RES - org[0], row * RES - org[1], 0.0])
                occ["parts"].append({"part": it["part"], "k": it["k"], "angle": a, "tris": t + shift})
                break
        else:
            sys.exit(f"{it['part']} does not fit an empty plate")
    return plates


# try every order of the big parts (small parts follow, largest first); keep the fewest plates, then the
# fullest last plate emptiest (so the leftovers group together)
import itertools
big, small = items[:4], items[4:]
best_plates = None
for perm in itertools.permutations(big):
    plates = pack(list(perm) + small)
    key = (len(plates), plates[-1]["grid"].mean())
    print("order", [p["part"] for p in perm], "->", len(plates), "plates")
    if best_plates is None or key < best_plates[0]:
        best_plates = (key, plates)
    if len(plates) <= 2:
        break
plates = best_plates[1]

out = HERE / "gcode" / which / "layout"
shutil.rmtree(out, ignore_errors=True)
summary = []
for pi, p in enumerate(plates, 1):
    d = out / f"plate{pi}"
    d.mkdir(parents=True)
    for q in p["parts"]:
        write_stl(d / f"{q['part']}-{q['k']}.stl", q["tris"])
    used = p["grid"].mean()
    ext = np.concatenate([q["tris"].reshape(-1, 3) for q in p["parts"]])
    summary.append({"plate": pi, "parts": [f"{q['part']}#{q['k']}@{q['angle']}" for q in p["parts"]],
                    "bed_fill": round(float(used), 3), "xy_min": ext.min(0)[:2].round(1).tolist(),
                    "xy_max": ext.max(0)[:2].round(1).tolist()})
    print(f"plate {pi}: fill {used:.0%}, {len(p['parts'])} parts, xy {ext.min(0)[:2].round(1)}..{ext.max(0)[:2].round(1)}:",
          ", ".join(f"{q['part']}@{q['angle']}" for q in p["parts"]))
(out / "layout.json").write_text(json.dumps(summary, indent=1))
