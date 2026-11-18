"""Shared helpers for the v2 printed parts: GT2 pulley teeth, involute spur gears, fits and holes.

Fits follow .claude/skills/printable-part-design/references/fdm_pla_rules.md (vertical holes, model sizes):
  bearing press  D + 0.10   (§1)      M3 clear 3.6, M4 clear 4.8 (§2, clearance_loose)
  snug on M4     4.2        (§1 +0.2) counterbores and nut traps from §2
"""
import importlib.util
import math
from pathlib import Path

import yaml
from build123d import (BuildLine, BuildPart, BuildSketch, Circle, Locations, Mode, Polygon, Polyline,
                       RegularPolygon, extrude, make_face, export_step)

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
_spec = importlib.util.spec_from_file_location("geometry", HERE.parent / "geometry.py")
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)


def dims(slug):
    """critical_dims of parts/models/<slug>.yaml by name (value_mm)."""
    d = yaml.safe_load((ROOT / "parts/models" / f"{slug}.yaml").read_text())
    return {c["name"]: c["value_mm"] for c in d["critical_dims"]}


# ---- fits (rules §1-§3) -------------------------------------------------------------------
F624 = dims("f624zz")
BRG_D = F624["outer diameter"] + 0.10          # press fit, rules §1
BRG_W = F624["width"]
FLANGE_D = F624["flange diameter"] + 0.40      # flange counterbore, running clearance
FLANGE_T = F624["flange thickness"] + 0.10
INNER_RACE_D = 6.2                              # race-contact boss / washer OD (< inner ring OD ~6.4) [est]
M3_CLEAR, M4_CLEAR, M4_SNUG = 3.6, 4.8, 4.2
M3_CB = (6.5, 3.3)                              # counterbore Ø x depth (rules §2)
M4_CB = (8.0, 4.4)
M3_NUT = (5.75, 2.7)                            # hex trap across flats x depth
M4_NUT = (7.25, 3.5)


def hex_prism(af, depth):
    """Hex nut pocket solid: across-flats af, height depth, base at z=0 (use with Mode.SUBTRACT)."""
    with BuildPart() as p:
        with BuildSketch():
            RegularPolygon(af / math.sqrt(3), 6)
        extrude(amount=depth)
    return p.part


# ---- GT2 pulley profile -------------------------------------------------------------------
def gt2_outline(teeth, groove_r=0.62, extra=0.0):
    """Toothed pulley outline (Sketch) for a GT2 2 mm belt: OD = PD - 0.508 (Gates), with `teeth`
    round grooves of radius `groove_r` sunk 0.75 mm below the OD (simplified GT2 profile [est]).
    `extra` grows the OD (print compensation). Returns (sketch, od)."""
    pd = teeth * 2.0 / math.pi
    od = pd - 0.508 + extra
    centre_r = od / 2 - 0.75 + groove_r
    with BuildSketch() as s:
        Circle(od / 2)
        with Locations(*[(centre_r * math.cos(2 * math.pi * i / teeth), centre_r * math.sin(2 * math.pi * i / teeth))
                         for i in range(teeth)]):
            Circle(groove_r, mode=Mode.SUBTRACT)
    return s.sketch, od


# ---- involute spur gear -------------------------------------------------------------------
def gear_sketch(module, teeth, backlash=0.15):
    """20 deg involute spur gear outline (Sketch), addendum 1 m, dedendum 1.25 m; each tooth thinned
    by `backlash` (mm, at the pitch circle) for FDM. Returns (sketch, pitch r, tip r, root r)."""
    pa = math.radians(20.0)
    rp = module * teeth / 2
    rb = rp * math.cos(pa)
    ra = rp + module
    rf = rp - 1.25 * module
    inv = lambda a: math.tan(a) - a
    half = (math.pi / teeth) / 2 - backlash / (2 * rp)
    t_max = math.sqrt((ra / rb) ** 2 - 1)
    flank = []
    for k in range(9):
        r = rb * math.sqrt(1 + (t_max * k / 8) ** 2)
        flank.append((r, half + inv(pa) - inv(math.acos(rb / r))))
    pts = []
    for i in range(teeth):
        c = 2 * math.pi * i / teeth
        a0 = half + inv(pa) + 0.05
        pts.append((rf * math.cos(c - a0), rf * math.sin(c - a0)))
        for r, a in flank:                         # one flank root -> tip
            pts.append((r * math.cos(c - a), r * math.sin(c - a)))
        for r, a in reversed(flank):               # other flank tip -> root
            pts.append((r * math.cos(c + a), r * math.sin(c + a)))
        pts.append((rf * math.cos(c + a0), rf * math.sin(c + a0)))
    with BuildSketch() as s:
        with BuildLine():
            Polyline(*pts, close=True)
        make_face()
    return s.sketch, rp, ra, rf


def circle_pts(cx, cy, r, n=48):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def teardrop_pts(cx, cy, r, n=24):
    """Circle of radius r with a 45 deg roof apex above it (+y), for horizontal holes (rules §5)."""
    pts = [(cx + r * math.cos(a), cy + r * math.sin(a))          # 135 deg -> bottom -> 45 deg
           for a in [math.radians(135 + 270 * i / n) for i in range(n + 1)]]
    return pts + [(cx, cy + r * math.sqrt(2))]


def hull_pts(points):
    """Convex hull (monotone chain), counter-clockwise."""
    pts = sorted(set((round(x, 6), round(y, 6)) for x, y in points))
    if len(pts) < 3:
        return pts
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for q in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    for q in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    return lower[:-1] + upper[:-1]


def polygon(points, mode=Mode.ADD):
    """Add a closed polygon face (points as given, no re-centring) to the active BuildSketch."""
    Polygon(*points, align=None, mode=mode)


def save(part, name):
    """Export <name>.step next to the part sources."""
    export_step(part, str(HERE / f"{name}.step"))
