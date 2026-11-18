// Joint rig, pose demo loop and explode offsets for the assembly viewer.
//
// Pure scene-graph logic with no DOM, so it runs in node tests. The joint maths mirrors
// engine/mechy/design_tools/rig.py (`joint_transforms`): a revolute joint rotates by
// (value - home) degrees about `axis` through `origin` (right-hand rule); a prismatic joint
// translates (value - home) mm along the unit `axis`; a child joint rides on its parent;
// a coupled joint takes home + sum(ratio * (driver - driver.home)).
//
// Pivots live in the assembly root's frame (z up, the GLB root carries the y-up rotation),
// so joints.yaml values convert straight over: mm -> m for origins and prismatic travel.
import * as THREE from 'three';

const MM = 0.001;
const MOVE_MIN_S = 0.8;
const MOVE_SPEED = 60;   // deg/s or mm/s: a move takes max(MOVE_MIN_S, biggest delta / MOVE_SPEED)
const HOLD_S = 0.25;
const COINCIDENT = 1e-6;

export const minJerk = (u) => u * u * u * (10 - 15 * u + 6 * u * u);

const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
const isVec3 = (a) => Array.isArray(a) && a.length >= 3 && isNum(a[0]) && isNum(a[1]) && isNum(a[2]);
const isObj = (o) => o !== null && typeof o === 'object' && !Array.isArray(o);
/** An id as written in joints.yaml: strings and numbers (`id: 2` parses as a number) become strings; else ''. */
const idOf = (v) => (typeof v === 'string' || isNum(v) ? String(v) : '');
const vec = (a) => new THREE.Vector3(a[0], a[1], a[2]);

/** Keep only the usable joints; everything dropped or repaired is described in `problems`. */
function normalizeJoints(list, problems) {
  const byId = new Map();
  list.forEach((spec, i) => {
    const bad = (why) => problems.push(`joint ${isObj(spec) && spec.id !== undefined ? `"${spec.id}"` : `#${i}`}: ${why}, skipped`);
    if (!isObj(spec)) return bad('not an object');
    const id = idOf(spec.id);
    if (!id) return bad('needs an id');
    if (byId.has(id)) return bad('duplicate id');
    if (spec.type !== 'revolute' && spec.type !== 'prismatic') return bad('type must be revolute or prismatic');
    if (!isVec3(spec.origin)) return bad('needs a numeric origin [x, y, z]');
    if (!isVec3(spec.axis) || vec(spec.axis).lengthSq() === 0) return bad('needs a non-zero numeric axis [x, y, z]');
    const coupled = (Array.isArray(spec.coupled) ? spec.coupled : [])
      .filter((c) => isObj(c) && idOf(c.joint) && isNum(Number(c.ratio)) && c.ratio !== null && c.ratio !== '')
      .map((c) => ({ joint: idOf(c.joint), ratio: Number(c.ratio) }));
    byId.set(id, {
      spec: { ...spec, id }, coupled,
      parentId: idOf(spec.parent) || null,
      origin: vec(spec.origin).multiplyScalar(MM),
      axis: vec(spec.axis).normalize(),
      prismatic: spec.type === 'prismatic',
      home: isNum(spec.home) ? spec.home : 0,
      base: new THREE.Vector3(),   // pivot position in its parent's frame at home
      pivot: null,
    });
  });

  for (const j of byId.values()) j.coupled = j.coupled.filter((c) => c.joint !== j.spec.id && byId.has(c.joint));

  // Unknown parents become ground; one edge of every parent cycle (or self-parent) is cut.
  for (const j of byId.values()) {
    if (j.parentId !== null && !byId.has(j.parentId)) {
      problems.push(`joint "${j.spec.id}": unknown parent "${j.parentId}", attached to the assembly root`);
      j.parentId = null;
    }
  }
  for (const j of byId.values()) {
    const seen = new Set([j.spec.id]);
    for (let p = j.parentId; p !== null; p = byId.get(p).parentId) {
      if (p === j.spec.id) {
        problems.push(`joint "${j.spec.id}": parent cycle, attached to the assembly root`);
        j.parentId = null;
        break;
      }
      if (seen.has(p)) break;   // leads into a cycle that does not include this joint
      seen.add(p);
    }
  }
  return byId;
}

/**
 * Create one pivot per joint over `assemblyRoot` and move each listed part node under it,
 * keeping its placement. Returns null when the rig has no usable joints. Malformed input
 * degrades instead of throwing: bad joints are skipped, unknown or cyclic parents become
 * ground, a part listed twice is attached once; each case is described in `problems`.
 */
export function buildRig(assemblyRoot, rig) {
  const list = isObj(rig) && Array.isArray(rig.joints) ? rig.joints : [];
  const problems = [];
  const byId = normalizeJoints(list, problems);
  if (!byId.size) return null;

  assemblyRoot.updateMatrixWorld(true);

  // Resolve part nodes before any pivot exists so a part id can never match a pivot.
  const missing = [];
  const duplicates = [];
  const claimed = new Set();
  const plan = [];   // [joint, node]
  for (const j of byId.values()) {
    for (const raw of Array.isArray(j.spec.parts) ? j.spec.parts : []) {
      const id = idOf(raw);
      if (!id) continue;
      // GLTFLoader renames nodes (PropertyBinding.sanitizeNodeName: spaces -> _, drops []./:), so an id like
      // "m2.5-screw-1" is only found under its sanitized name.
      const node = assemblyRoot.getObjectByName(id) || assemblyRoot.getObjectByName(THREE.PropertyBinding.sanitizeNodeName(id));
      if (!node || node === assemblyRoot) {
        if (!missing.includes(id)) missing.push(id);
      } else if (claimed.has(node)) {
        if (!duplicates.includes(id)) duplicates.push(id);
        problems.push(`part "${id}": listed in more than one joint, kept with the first`);
      } else {
        claimed.add(node);
        plan.push([j, node]);
      }
    }
  }

  // Parents have an identity rotation at home, so a child sits at (its origin - parent origin).
  for (const j of byId.values()) j.pivot = Object.assign(new THREE.Object3D(), { name: `mechy_joint_${j.spec.id}` });
  for (const j of byId.values()) {
    const parent = j.parentId ? byId.get(j.parentId) : null;
    j.base.copy(j.origin);
    if (parent) j.base.sub(parent.origin);
    j.pivot.position.copy(j.base);
    (parent ? parent.pivot : assemblyRoot).add(j.pivot);
  }
  assemblyRoot.updateMatrixWorld(true);

  const attached = [];   // original parent and local transform of every moved part
  for (const [j, node] of plan) {
    attached.push({ node, parent: node.parent, position: node.position.clone(),
                    quaternion: node.quaternion.clone(), scale: node.scale.clone() });
    j.pivot.attach(node);
  }

  const joints = [...byId.values()].map((j) => ({
    id: j.spec.id,
    label: typeof j.spec.label === 'string' && j.spec.label ? j.spec.label : j.spec.id,
    type: j.spec.type,
    home: j.home,
    limits: j.spec.limits ?? null,
    coupled: j.coupled.length ? j.coupled : null,
    driven: j.coupled.length > 0,
  }));
  const sliders = joints.filter((j) => !j.driven).map((j) => j.id);
  const current = Object.fromEntries(joints.map((j) => [j.id, j.home]));

  function setValues(values = {}) {
    for (const id of sliders) {
      if (isNum(values?.[id])) current[id] = values[id];
    }
    for (const info of joints) {
      if (!info.driven) continue;
      current[info.id] = info.home + info.coupled.reduce((sum, c) => {
        const driver = byId.get(c.joint);
        return driver ? sum + c.ratio * (current[c.joint] - driver.home) : sum;
      }, 0);
    }
    for (const j of byId.values()) {
      const d = current[j.spec.id] - j.home;
      if (j.prismatic) {
        j.pivot.position.copy(j.base).addScaledVector(j.axis, d * MM);
      } else {
        j.pivot.quaternion.setFromAxisAngle(j.axis, THREE.MathUtils.degToRad(d));
      }
    }
    assemblyRoot.updateMatrixWorld(true);
  }

  const poses = (Array.isArray(rig.poses) ? rig.poses : [])
    .filter((p) => isObj(p) && isObj(p.values))
    .map((p, i) => ({
      name: idOf(p.name) || `pose ${i + 1}`,
      values: Object.fromEntries(Object.entries(p.values).filter(([, v]) => isNum(v))),
    }));

  return {
    joints,
    sliders,
    poses,
    missing,
    duplicates,
    problems,
    setValues,
    values: () => ({ ...current }),
    /** Put every part back where it was before buildRig and remove the pivots. */
    dispose() {
      for (const a of attached) {
        a.parent.add(a.node);
        a.node.position.copy(a.position);
        a.node.quaternion.copy(a.quaternion);
        a.node.scale.copy(a.scale);
      }
      for (const j of byId.values()) j.pivot.removeFromParent();
      assemblyRoot.updateMatrixWorld(true);
    },
  };
}

/**
 * Demo loop through home then each pose in file order, returning to home. Each move is
 * minimum-jerk and takes max(0.8 s, biggest joint delta / 60) followed by a 0.25 s hold.
 * `sample(t)` is periodic; `name` is the waypoint last reached.
 */
export function poseLoop(rig) {
  const homes = {};
  for (const id of rig.sliders) homes[id] = rig.joints.find((j) => j.id === id).home;
  const waypoints = [{ name: 'home', values: { ...homes } }];
  for (const p of rig.poses) {
    waypoints.push({ name: p.name, values: Object.fromEntries(rig.sliders.map((id) => [id, isNum(p.values[id]) ? p.values[id] : homes[id]])) });
  }

  const segments = waypoints.map((from, i) => {
    const to = waypoints[(i + 1) % waypoints.length];
    const delta = Math.max(0, ...rig.sliders.map((id) => Math.abs(to.values[id] - from.values[id])));
    const move = Math.max(MOVE_MIN_S, delta / MOVE_SPEED);
    return { from, to, move, length: move + HOLD_S };
  });
  const duration = segments.reduce((sum, s) => sum + s.length, 0);

  return {
    waypoints,
    duration,
    sample(t) {
      let local = ((t % duration) + duration) % duration;
      for (const s of segments) {
        if (local >= s.length) { local -= s.length; continue; }
        // `target`: the waypoint this segment ends at (the real arm is sent waypoints, not every frame).
        if (local >= s.move) return { name: s.to.name, values: { ...s.to.values }, target: s.to };
        const k = minJerk(local / s.move);
        return {
          name: s.from.name, target: s.to,
          values: Object.fromEntries(rig.sliders.map((id) => [id, s.from.values[id] + (s.to.values[id] - s.from.values[id]) * k])),
        };
      }
      const last = segments[segments.length - 1];   // float round-off at the very end of the loop
      return { name: last.to.name, values: { ...last.to.values } };
    },
  };
}

/**
 * Explode state per named part, captured at the model's current (unexploded) pose:
 * `{offset, base, local, parent}`. `offset` is the world-space move at factor 1, from the
 * model's bounding-box centre to the part's, so at factor 1 the model spans about twice its
 * size; a part at the model centre goes up (assembly +z, world +y). `base` is the part's
 * unexploded position in the model's frame, `local` its position under `parent`. Visibility
 * is ignored. Capture it with nothing exploded, and capture again after the pose changes.
 */
export function explodeOffsets(model, partNames) {
  model.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(model);
  const centre = box.getCenter(new THREE.Vector3());
  const lift = Math.max(...box.getSize(new THREE.Vector3()).toArray()) * 0.5;
  const out = new Map();
  for (const name of partNames) {
    const node = model.getObjectByName(name);
    if (!node) continue;
    const offset = new THREE.Box3().setFromObject(node).getCenter(new THREE.Vector3()).sub(centre);
    if (offset.length() < COINCIDENT) offset.set(0, lift, 0);
    out.set(name, {
      offset,
      base: model.worldToLocal(node.getWorldPosition(new THREE.Vector3())),
      local: node.position.clone(),
      parent: node.parent,
    });
  }
  return out;
}

/**
 * Place each part at its unexploded position plus offset * factor in world space. `state` is
 * what explodeOffsets returned. Factor 0 restores the captured local position exactly while the
 * part still sits under the same parent; after a rig was built or disposed in between, positions
 * are rebuilt from the model-frame base, so nothing stale is reused.
 */
export function applyExplode(model, state, factor) {
  model.updateMatrixWorld(true);
  for (const [name, e] of state) {
    const node = model.getObjectByName(name);
    if (!node) continue;
    if (node.parent === e.parent) {
      if (factor === 0) node.position.copy(e.local);
      else node.position.copy(node.parent.worldToLocal(node.parent.localToWorld(e.local.clone()).addScaledVector(e.offset, factor)));
    } else {
      const world = model.localToWorld(e.base.clone()).addScaledVector(e.offset, factor);
      node.position.copy(node.parent.worldToLocal(world));
    }
    node.updateMatrixWorld(true);
  }
}
