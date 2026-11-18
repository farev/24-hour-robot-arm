"""Motor-side gravity torque with the payload for a ref_arm (parallel-linkage) variant.

usage: python sim/torque_check.py <variant> [payload_kg]
Sweeps tool-midpoint targets on the table plane (r = 0.10..0.40 m, z = 3/8/15 cm), keeps the
reachable ones, and compares the worst gravity torque per motor with holding torque x ratio
(motor values from hw/motors.yaml). Computed from the Mechy arm model, not measured.
"""
import json
import sys
from pathlib import Path

import numpy as np

from mechy.arm_model import ArmModel, ParallelLevelArm
from mechy.project import Project

root = Path(__file__).resolve().parent.parent
variant = sys.argv[1] if len(sys.argv) > 1 else "v1"
payload = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3
p = Project(root)
hw = p.hardware()
arm = ArmModel(p.params(variant), hw["motors"], hw["drivers"])
mp = root / "design" / variant / "mass_props.json"
if mp.exists():
    arm.mass_props = json.loads(mp.read_text())
motors = {m["id"]: m for m in hw["motors"]}
hold = np.array([motors[j["motor"]]["holding_torque_nm"] for j in arm.params["joints"]])
ratio = np.array([j["gear_ratio"] for j in arm.params["joints"]])
cap = hold * ratio
k = ParallelLevelArm(arm)

heights = (0.03, 0.08, 0.15)
worst, worst_pose, max_r = np.zeros(4), [None] * 4, {z: None for z in heights}
for r in np.arange(0.10, 0.401, 0.005):
    for z in heights:
        q = k.ik([r, 0.0, z])
        if q is None:
            continue
        max_r[z] = round(float(r), 3)
        t = np.abs(arm.motor_gravity_torque(q, ball_mass=payload))
        for i in range(4):
            if t[i] > worst[i]:
                worst[i], worst_pose[i] = t[i], [round(float(r), 3), z]
print(json.dumps({
    "variant": variant, "payload_kg": payload,
    "max_reach_m_at_tool_height": {str(z): v for z, v in max_r.items()},
    "capacity_holding_x_ratio_nm": cap.round(3).tolist(),
    "worst_gravity_nm": worst.round(3).tolist(),
    "worst_pose_r_z": worst_pose,
    "worst_frac_of_capacity": (worst / cap).round(3).tolist(),
}, indent=1))
