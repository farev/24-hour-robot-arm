"""TowerPro MG996R servo, built from the TowerPro drawing (Cornell-hosted copy) plus reseller numbers.

Frame: origin on the output shaft axis at the case top face (the face the spline comes out of),
that face at z = 0, spline along +Z, body toward -Z, long axis along +X (shaft near the -X end).
Also writes mg996r-horn.step: the round horn that ships with it (estimate), seated on the spline.
"""
from pathlib import Path

from build123d import (Align, Box, BuildPart, Cylinder, Locations, Mode, Pos, export_step)

HERE = Path(__file__).parent
BODY_L = 40.7        # drawing 40.7 approx
BODY_W = 19.7        # drawing 19.7 (20 callout)
CASE_H = 36.6        # drawing 36.6 (case bottom -> top face) [read at page resolution, edge assignment estimate]
TAB_SPAN = 53.6      # drawing 53.6
TAB_T = 2.5          # estimate
TAB_TOP_BELOW = 7.5  # drawing 26.6 = case bottom -> tab bottom, so tab top = 36.6 - 26.6 - 2.5 = 7.5 below top [est]
HOLE_D = 4.2         # reseller 4.1 measured, rounded up [est]
HOLE_X = 49.5        # [est] hole spacing along the long axis
HOLE_Y = 10.0        # [est] reseller 9.5-10
SHAFT_OFF = 10.0     # [est] spline axis from the near body end
SPLINE_D, SPLINE_H = 5.8, 4.0   # reseller 5.7-5.8; boss + spline 6.3 above the case (42.9 - 36.6) [est]
BOSS_D, BOSS_H = 12.0, 2.3      # [est] round boss under the spline
HORN_D, HORN_T = 21.0, 5.5      # [est] round horn, sits on the spline

cx = BODY_L / 2 - SHAFT_OFF          # body centre along X
with BuildPart() as servo:
    with Locations((cx, 0, -CASE_H / 2)):
        Box(BODY_L, BODY_W, CASE_H)
    with Locations((cx, 0, -TAB_TOP_BELOW - TAB_T / 2)):
        Box(TAB_SPAN, BODY_W, TAB_T)
    with Locations((cx + s * HOLE_X / 2, t * HOLE_Y / 2, -TAB_TOP_BELOW - TAB_T / 2)
                   for s in (-1, 1) for t in (-1, 1)):
        Cylinder(HOLE_D / 2, TAB_T + 0.2, mode=Mode.SUBTRACT)
    Cylinder(BOSS_D / 2, BOSS_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    with Locations((0, 0, BOSS_H)):
        Cylinder(SPLINE_D / 2, SPLINE_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
export_step(servo.part, str(HERE / "mg996r-servo.step"))

with BuildPart() as horn:                       # round horn: bottom face on the boss top
    with Locations((0, 0, BOSS_H)):
        Cylinder(HORN_D / 2, HORN_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        Cylinder(SPLINE_D / 2 - 0.05, HORN_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
export_step(horn.part, str(HERE / "mg996r-horn.step"))
print("ok")
