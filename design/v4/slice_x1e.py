"""Slice the v4 printed parts for a Bambu Lab X1E (0.4 nozzle, Generic PLA) with the Bambu Studio CLI.
usage: python design/v4/slice_x1e.py <plate-set>   plate-set: coupon | arm | gripper
Writes design/v4/gcode/<plate-set>/<plate-set>.gcode.3mf (sliced project the X1E prints directly) and the
per-plate .gcode files. Bambu Studio arranges the parts (rotation allowed) and adds plates only when needed.
"""
import csv
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from mechy.design_tools.printing import PROCESS_OVERRIDES, printer_settings, slicer_presets

HERE = Path(__file__).resolve().parent
EXE = "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
PROFILES = Path("/Applications/BambuStudio.app/Contents/Resources/profiles")
GRIPPER = {"gripper-base", "crank-gear-a", "crank-gear-b", "idler-link-a", "jaw-a", "jaw-b"}
# structural settings (fdm_pla_rules §4): 4 walls on load-bearing parts, 20 % gyroid, 5 top/bottom layers
PROCESS = {"wall_loops": "4", "sparse_infill_density": "20%", "sparse_infill_pattern": "gyroid",
           "top_shell_layers": "5", "bottom_shell_layers": "5", "enable_support": "0",
           "curr_bed_type": "Textured PEI Plate",                       # assumption: the Studio's X1E plates
           # no brim / skirt: toolpaths stay inside the packed outlines, so the edge and calibration-line clearances
           # hold (auto brim put a ring 6 mm out from a spacer, to x 4.2). No part trips printcheck's tall ratio.
           "brim_type": "no_brim", "skirt_loops": "0", **PROCESS_OVERRIDES}

def with_templates(machine, preset):
    """Merge Bambu's '<machine> template <key>' presets (the real X1E start/end/filament-change/layer/timelapse
    G-code) into the machine preset. The `inherits` chain alone gives the generic fdm_bbl_3dp_001_common start
    G-code (home, level, one purge line), which has no flow calibration, nozzle wipe or AMS filament load."""
    for f in sorted((PROFILES / "BBL" / "machine").glob(f"{machine} template *.json")):
        t = json.loads(f.read_text())
        preset.update({k: v for k, v in t.items() if k.endswith("_gcode")})
    return preset


which = sys.argv[1] if len(sys.argv) > 1 else "arm"
only = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None   # optional part subset (plate trials)


def slice_layout(which):
    """Slice each plate laid out by pack_plates.py as its own job, positions kept (no arrange)."""
    lay = HERE / "gcode" / which / "layout"
    pdir = HERE / "gcode" / which / "presets"
    pdir.mkdir(parents=True, exist_ok=True)
    machine, presets = slicer_presets(PROFILES, printer_settings())
    with_templates(machine, presets[0])
    presets[1].update(PROCESS)
    paths = []
    for i, p in enumerate(presets):
        paths.append(pdir / f"{['machine', 'process', 'filament'][i]}.json")
        paths[-1].write_text(json.dumps(p, indent=1))
    for plate in sorted(lay.glob("plate*")):
        name = f"{which}-{plate.name}"
        out = HERE / "gcode" / which / name
        shutil.rmtree(out, ignore_errors=True)
        out.mkdir()
        stls = sorted(str(f) for f in plate.glob("*.stl"))
        cmd = [EXE, "--load-settings", f"{paths[0]};{paths[1]}", "--load-filaments", str(paths[2]),
               "--orient", "0", "--arrange", "0", "--slice", "0", "--export-3mf", f"{name}.gcode.3mf",
               "--outputdir", str(out), *stls]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, stdin=subprocess.DEVNULL)
        print(name, "exit", r.returncode, len(stls), "objects")
        if r.returncode:
            print((r.stdout + r.stderr)[-2500:])
            sys.exit(1)
        with zipfile.ZipFile(out / f"{name}.gcode.3mf") as z:
            for n in z.namelist():
                if n == "Metadata/plate_1.gcode":
                    (out / f"{name}.gcode").write_bytes(z.read(n))
                elif n == "Metadata/plate_1.png":
                    (out / f"{name}.png").write_bytes(z.read(n))
                elif n.endswith("slice_info.config"):
                    (out / "slice_info.config").write_bytes(z.read(n))
        for extra in ("plate_1.gcode", "result.json"):
            (out / extra).unlink(missing_ok=True)


if which == "layout":
    slice_layout(sys.argv[2])
    sys.exit(0)
rows = list(csv.DictReader((HERE / "print_list.csv").open()))
files = []
for r in rows:
    part = r["part"].split(" (")[0]
    keep = (part == "fit-coupon") if which == "coupon" else \
           (part in GRIPPER) if which == "gripper" else (part not in GRIPPER and part != "fit-coupon")
    if only is not None:
        keep = part in only
    if keep:
        files += [str(HERE / r["stl"])] * int(r["qty"])

out = HERE / "gcode" / which
shutil.rmtree(out, ignore_errors=True)
(out / "presets").mkdir(parents=True)
machine, presets = slicer_presets(PROFILES, printer_settings())
presets[1].update(PROCESS)
paths = []
for i, p in enumerate(presets):
    paths.append(out / "presets" / f"{['machine', 'process', 'filament'][i]}.json")
    paths[-1].write_text(json.dumps(p, indent=1))
cmd = [EXE, "--load-settings", f"{paths[0]};{paths[1]}", "--load-filaments", str(paths[2]),
       "--orient", "0", "--arrange", "1", "--allow-rotations", "--slice", "0",
       "--export-3mf", f"{which}.gcode.3mf", "--outputdir", str(out), *files]
print(machine, "|", presets[1]["name"], "|", presets[2]["name"], "|", len(files), "objects")
r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, stdin=subprocess.DEVNULL)
print("exit", r.returncode)
if r.returncode:
    print((r.stdout + r.stderr)[-2500:])
    sys.exit(1)
pkg = out / f"{which}.gcode.3mf"
with zipfile.ZipFile(pkg) as z:
    for n in z.namelist():
        if n.endswith(".gcode"):
            (out / Path(n).name.replace("plate", f"{which}-plate")).write_bytes(z.read(n))
        if n.endswith("slice_info.config"):
            (out / "slice_info.config").write_bytes(z.read(n))
        if n.startswith("Metadata/plate_") and n.endswith(".png") and "_small" not in n and "no_light" not in n:
            (out / Path(n).name.replace("plate", f"{which}-plate")).write_bytes(z.read(n))
print(sorted(p.name for p in out.iterdir()))
