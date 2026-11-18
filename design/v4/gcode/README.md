# v4 print files, Bambu Lab X1E

These files were sliced with Bambu Studio 02.09.01 on 2026-11-06. The settings were:

- Printer preset "Bambu Lab X1E 0.4 nozzle", with Bambu's own X1E start, end, filament-change, layer-change and
  timelapse G-code merged in from its template presets.
- Filament: Generic PLA.
- Bed plate: Textured PEI Plate.
- 0.20 mm layers ("0.20mm Standard @BBL X1C").
- 4 walls, 5 top and 5 bottom layers, 20 % gyroid infill.
- No supports, no brim, no skirt.
- Parts placed as modelled, flat face down.

The plates were laid out with `python tools/mpy.py design/v4/pack_plates.py <set>` from the real part outlines.
They keep these clearances:

- 5 mm between parts.
- At least 10 mm from the side and back edges.
- Clear of the X1E's front-left exclusion area.
- At least 8 mm behind the purge and flow-calibration lines. The X1E start G-code draws them at x 18-240, y 1-12, so
  parts start at y 20.

Each plate was sliced with `python tools/mpy.py design/v4/slice_x1e.py layout <set>`. `python design/v4/verify_plates.py`
checks every plate against these clearances, and that the real X1E start G-code is in the file. The last run gave
ALL OK.

Each plate folder holds two print files:

- `.gcode.3mf` is the file to print. Send it from Bambu Studio or Handy, or copy it to the X1E's SD card. It carries the
  printer model, the plate preview and the filament data.
- `.gcode` is the same toolpath as plain G-code.

| Order | File | Parts | Time | PLA |
|---|---|---|---|---|
| 1 | coupon/coupon-plate1 | fit coupon | 1 h 05 m | 27 g |
| 2 | arm/arm-plate1 | base, yaw motor plate, shoulder compound, wrist pulley, wrist flange ring, 7 race washers, wrist washer (1.7 mm), yaw bolt spacer, 6 spacers | 7 h 18 m | 220 g |
| 3 | arm/arm-plate2 | lower shank, upper shank, yaw pulley | 6 h 56 m | 186 g |
| 4 | arm/arm-plate3 | turret | 3 h 32 m | 112 g |
| HOLD | gripper/gripper-plate1 | gripper base, crank gears A and B, 2 idler links, 2 jaws | 1 h 47 m | 40 g |

Notes on the plates:

- **Coupon first.** Check the bearing press fit (Ø13.1 column), the M4 and M3 holes and the pilots. If the fit is off,
  the parts get re-sized and re-sliced before the long plates.
- **Gripper plate on hold.** Do not print it until the MG996R horn height and tab holes are measured
  (design/v4/summary.md).
- **Wrist flange ring.** Glue it with super glue onto the wrist pulley's toothed face, centred over the bearing.
- **Race washers.** The 1 mm race washers are discs. If their first layer looks poor, reprint them on their own at
  0.1 mm layers.
- **Motor heat.** The turret, both shanks and the yaw motor plate touch the motors. If the motor cases run hot, reprint
  them in PETG (assumptions/motor-mount-material.yaml).
