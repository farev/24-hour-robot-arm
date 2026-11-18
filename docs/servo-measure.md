# Measuring the MG996R for the gripper

Measure the gripper servo when it arrives, before printing the gripper plate. Use calipers; the Invention Studio has
them. Fit the **round horn** you plan to use, with its screw, then measure these to 0.1 mm.

| # | What | How | Model now |
|---|---|---|---|
| 1 | Horn top above the case top | Depth rod of the calipers from the flat top of the horn down to the case top beside it | 7.8 |
| 2 | Horn screw-hole circle | Distance between two opposite small holes on the horn, centre to centre (outside edge to outside edge, minus one hole diameter) | 14.0 (2 x 7.0) |
| 3 | Tab hole spacing, long way | Centre to centre of the two holes on one tab across to the matching holes on the other tab (outside to outside, minus one hole) | 49.5 |
| 4 | Tab hole spacing, short way | Centre to centre of the two holes on the same tab | 10.0 |
| 5 | Shaft offset | From the end of the case nearest the spline to the spline centre: measure to the spline's near edge and add half the spline diameter | 10.0 |
| 6 | Tab top below the case top | Depth rod from the case top down to the top face of a tab | 7.5 |
| 7 | Tab hole diameter | Inside jaws in one tab hole | 4.2 |
| 8 | Horn screws in the box | Count the small horn screws and the 4 tab screws, and note their size if marked | - |

Reply in the chat with the 8 values, for example "1: 8.4, 2: 15.0, 3: 49.6, ...". Mechy updates
parts/models/mg996r-servo.yaml, regenerates the gripper parts, re-runs the gripper sweep and the pose checks, and
re-slices the gripper plate.
