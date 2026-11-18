// Inspection maths for the CAD viewer: part geometry stats, project data lookup (print_list.csv,
// bom.csv, mass_props.json), edge measurement (straight edges, arcs, holes) and the gravity
// bending-moment estimate behind the Load study.
//
// Pure scene-graph / array logic with no DOM, so it runs in node tests (app/Tests/viewer).
// Everything here is read-only: the viewer inspects the design, it never edits it.
import * as THREE from 'three';

// g/cm^3. Printed parts use the filament's density; bought kinds use an effective density for
// the simplified shape the GLB carries (a NEMA 17 drawn as a solid block is ~4 g/cm^3 overall).
export const DENSITY = [
  { re: /petg/i, rho: 1.27, label: 'PETG' },
  { re: /\basa\b/i, rho: 1.07, label: 'ASA' },
  { re: /\babs\b/i, rho: 1.04, label: 'ABS' },
  { re: /tpu/i, rho: 1.21, label: 'TPU' },
  { re: /nylon|\bpa\d*\b/i, rho: 1.14, label: 'Nylon' },
  { re: /pla/i, rho: 1.24, label: 'PLA' },
  { re: /alu|6061|7075/i, rho: 2.70, label: 'Aluminium' },
  { re: /steel|stainless/i, rho: 7.85, label: 'Steel' },
];
export const KIND_MATERIAL = {
  Motors: { material: 'Steel / copper (motor)', rho: 4.0 },
  Pulleys: { material: 'Aluminium', rho: 2.7 },
  Hardware: { material: 'Steel', rho: 7.85 },
  Belts: { material: 'Rubber, glass-fibre cord', rho: 1.2 },
};
const PRINT_FILL = 0.45;   // skin + 20 % infill, as a fraction of solid (engine/mechy/cad/outputs.py)

export const normName = (s) => String(s || '').toLowerCase().replace(/\.(stl|step|glb)$/, '').replace(/[^a-z0-9]+/g, '');

/**
 * The BOM entry linked to a node: `links` is {parts: {<partId>: {component, name, status, price, vendor, url,
 * image, drift, chosen, placeholder}}} (the app's BomLinks.viewerJSON); the node name matches a part id by
 * normName. null when there are no links or the node has none.
 */
export function linkFor(links, nodeName) {
  const parts = links && links.parts;
  if (!parts) return null;
  if (Object.prototype.hasOwnProperty.call(parts, nodeName)) return parts[nodeName];
  const key = normName(nodeName);
  if (!key) return null;
  const id = Object.keys(parts).find((k) => normName(k) === key);
  return id ? parts[id] : null;
}

/** Minimal RFC 4180 CSV -> array of row objects keyed by the header. */
export function parseCSV(text) {
  const rows = [];
  let row = [], cell = '', q = false;
  const s = String(text || '');
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (q) {
      if (c === '"' && s[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') q = false;
      else cell += c;
    } else if (c === '"') q = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && s[i + 1] === '\n') i++;
      row.push(cell); cell = '';
      if (row.some((v) => v !== '')) rows.push(row);
      row = [];
    } else cell += c;
  }
  row.push(cell);
  if (row.some((v) => v !== '')) rows.push(row);
  if (rows.length < 2) return [];
  const head = rows[0].map((h) => h.trim());
  return rows.slice(1).map((r) => Object.fromEntries(head.map((h, i) => [h, (r[i] || '').trim()])));
}

export function densityOf(material) {
  const d = DENSITY.find((x) => x.re.test(material || ''));
  return d ? d.rho : null;
}
export function materialFamily(material) {
  const d = DENSITY.find((x) => x.re.test(material || ''));
  return d ? d.label : (material ? String(material) : 'Unknown');
}

/**
 * Volume (signed tetrahedra; exact for a closed mesh), area and volume centroid, in world units.
 * A part split over several primitives is only closed as a whole, so callers add `signed`
 * (and `moment`) across a part's meshes before taking the absolute value.
 */
export function meshStats(mesh) {
  const g = mesh.geometry;
  const pos = g.attributes.position;
  const idx = g.index;
  const n = idx ? idx.count : pos.count;
  mesh.updateWorldMatrix(true, false);
  const m = mesh.matrixWorld;
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
  const ab = new THREE.Vector3(), ac = new THREE.Vector3();
  let vol = 0, area = 0, cx = 0, cy = 0, cz = 0;
  for (let i = 0; i + 2 < n; i += 3) {
    const i0 = idx ? idx.getX(i) : i, i1 = idx ? idx.getX(i + 1) : i + 1, i2 = idx ? idx.getX(i + 2) : i + 2;
    a.fromBufferAttribute(pos, i0).applyMatrix4(m);
    b.fromBufferAttribute(pos, i1).applyMatrix4(m);
    c.fromBufferAttribute(pos, i2).applyMatrix4(m);
    const v = a.dot(ab.copy(b).cross(c)) / 6;
    vol += v;
    cx += v * (a.x + b.x + c.x) / 4; cy += v * (a.y + b.y + c.y) / 4; cz += v * (a.z + b.z + c.z) / 4;
    area += ab.subVectors(b, a).cross(ac.subVectors(c, a)).length() / 2;
  }
  const centroid = Math.abs(vol) > 1e-18 ? new THREE.Vector3(cx / vol, cy / vol, cz / vol) : null;
  return { volume: Math.abs(vol), signed: vol, moment: new THREE.Vector3(cx, cy, cz), area, centroid, tris: Math.floor(n / 3) };
}

/** Project data for one node: its print_list row, mass_props body and (for bought kinds) BOM rows. */
export function lookupPart(data, nodeName, kindRe) {
  const key = normName(nodeName);
  const out = { print: null, body: null, bom: [] };
  if (!data) return out;
  const rows = data.print || [];
  out.print = rows.find((r) => normName(r.part) === key)
    || rows.find((r) => normName(r.stl).endsWith(key) && key.length > 3)
    || rows.find((r) => { const k = normName(r.part); return k.length > 3 && (key.startsWith(k) || k.startsWith(key)); })
    || null;
  const bodies = data.mass && data.mass.bodies;
  if (bodies) {
    const hit = Object.keys(bodies).find((b) => normName(b) === key);
    if (hit) out.body = { name: hit, ...bodies[hit] };
  }
  if (kindRe && data.bom) out.bom = data.bom.filter((r) => kindRe.test(r.item) && !/driver|cable|wire|capacitor|shield|board/i.test(r.item));
  else if (data.bom) out.bom = data.bom.filter((r) => normName(r.item) === key);
  return out;
}

/**
 * Mass of a part in grams with where it came from: the print list's estimate, else the
 * mass_props body, else volume x density (printed parts at a typical fill).
 */
export function estimateMass({ print, body }, volumeCm3, kind) {
  const nGrams = (v) => { const x = parseFloat(v); return Number.isFinite(x) && x > 0 ? x : null; };
  if (print) {
    const g = nGrams(print.est_grams);
    if (g) return { grams: g, source: 'print list', material: print.material || null };
  }
  if (body && Number.isFinite(body.mass) && body.mass > 0 && !(body.parts > 1)) {
    return { grams: body.mass * 1000, source: 'mass props', material: print ? print.material : null };
  }
  const km = kind && KIND_MATERIAL[kind];
  const material = (print && print.material) || (km ? km.material : null);
  const rho = (km && material === km.material ? km.rho : densityOf(material)) || (km ? km.rho : null);
  if (!rho || !volumeCm3) return { grams: null, source: null, material };
  const fill = km ? 1 : PRINT_FILL;
  return { grams: volumeCm3 * rho * fill, source: km ? 'volume × density' : 'volume × density, 45 % fill', material };
}

// Edge measurement ----------------------------------------------------------

/** World-space segment endpoints of an EdgesGeometry (or any LineSegments) under `matrixWorld`. */
export function worldSegments(lineSegments) {
  const pos = lineSegments.geometry.attributes.position;
  lineSegments.updateWorldMatrix(true, false);
  const m = lineSegments.matrixWorld;
  const out = new Float32Array(pos.count * 3);
  const v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) {
    v.fromBufferAttribute(pos, i).applyMatrix4(m);
    out[i * 3] = v.x; out[i * 3 + 1] = v.y; out[i * 3 + 2] = v.z;
  }
  return out;
}

/** Least-squares circle through 3D points: best-fit plane, then a Kasa fit in that plane. */
export function fitCircle(points) {
  const n = points.length;
  if (n < 3) return null;
  const c = new THREE.Vector3();
  for (const p of points) c.add(p);
  c.divideScalar(n);
  // Plane normal from the summed cross products around the centroid (Newell-style, fine for loops/arcs).
  const nrm = new THREE.Vector3(), t = new THREE.Vector3();
  for (let i = 0; i < n; i++) nrm.add(t.subVectors(points[i], c).cross(new THREE.Vector3().subVectors(points[(i + 1) % n], c)));
  if (nrm.lengthSq() < 1e-30) return null;
  nrm.normalize();
  const u = new THREE.Vector3().subVectors(points[0], c);
  u.addScaledVector(nrm, -u.dot(nrm));
  if (u.lengthSq() < 1e-30) return null;
  u.normalize();
  const w = new THREE.Vector3().crossVectors(nrm, u);
  // Kasa: minimise sum (x^2 + y^2 + D x + E y + F)^2.
  let sx = 0, sy = 0, sxx = 0, syy = 0, sxy = 0, sxz = 0, syz = 0, sz = 0;
  const xy = points.map((p) => { const d = t.subVectors(p, c); return [d.dot(u), d.dot(w)]; });
  for (const [x, y] of xy) {
    const z = x * x + y * y;
    sx += x; sy += y; sxx += x * x; syy += y * y; sxy += x * y; sxz += x * z; syz += y * z; sz += z;
  }
  const M = [[sxx, sxy, sx], [sxy, syy, sy], [sx, sy, n]];
  const R = [-sxz, -syz, -sz];
  const det = (A) => A[0][0] * (A[1][1] * A[2][2] - A[1][2] * A[2][1]) - A[0][1] * (A[1][0] * A[2][2] - A[1][2] * A[2][0]) + A[0][2] * (A[1][0] * A[2][1] - A[1][1] * A[2][0]);
  const D0 = det(M);
  if (Math.abs(D0) < 1e-30) return null;
  const col = (k) => M.map((row, i) => row.map((v, j) => (j === k ? R[i] : v)));
  const D = det(col(0)) / D0, E = det(col(1)) / D0, F = det(col(2)) / D0;
  const cx = -D / 2, cy = -E / 2;
  const r2 = cx * cx + cy * cy - F;
  if (!(r2 > 0)) return null;
  const r = Math.sqrt(r2);
  let worst = 0, planar = 0;
  for (let i = 0; i < n; i++) {
    worst = Math.max(worst, Math.abs(Math.hypot(xy[i][0] - cx, xy[i][1] - cy) - r));
    planar = Math.max(planar, Math.abs(t.subVectors(points[i], c).dot(nrm)));
  }
  const center = c.clone().addScaledVector(u, cx).addScaledVector(w, cy);
  return { center, radius: r, normal: nrm, error: Math.max(worst, planar) / r };
}

/**
 * The model edge a picked segment belongs to. `segs` is a flat [ax, ay, az, bx, by, bz, ...] array.
 * Straight runs of collinear segments give a length; smoothly turning chains give an arc (radius,
 * length) or, when they close, a circle (diameter). Returns { kind, length, points, ... }.
 */
export function edgeChain(segs, pick, opts = {}) {
  const count = segs.length / 6;
  const tol = opts.weld || 1e-6;
  const q = (i) => `${Math.round(segs[i] / tol)},${Math.round(segs[i + 1] / tol)},${Math.round(segs[i + 2] / tol)}`;
  const at = new Map();   // endpoint key -> [segment index * 2 + end]
  for (let s = 0; s < count; s++) {
    for (const e of [0, 1]) {
      const k = q(s * 6 + e * 3);
      if (!at.has(k)) at.set(k, []);
      at.get(k).push(s * 2 + e);
    }
  }
  const P = (s, e) => new THREE.Vector3(segs[s * 6 + e * 3], segs[s * 6 + e * 3 + 1], segs[s * 6 + e * 3 + 2]);
  const dirOf = (s, from) => P(s, 1 - from).sub(P(s, from)).normalize();
  const used = new Set([pick]);
  const maxTurn = THREE.MathUtils.degToRad(opts.maxTurnDeg || 32);
  const straightTurn = THREE.MathUtils.degToRad(opts.straightDeg || 1.5);

  // Walk from the picked segment's end `e` while the turn per step stays under `limit`.
  function walk(e, limit) {
    const pts = [];
    let s = pick, end = e, dir = dirOf(pick, 1 - e);
    for (let guard = 0; guard < 4096; guard++) {
      const near = at.get(q(s * 6 + end * 3)).filter((x) => (x >> 1) !== s);
      if (near.length !== 1) break;
      const ns = near[0] >> 1, nFrom = near[0] & 1;
      if (ns === pick) return { pts, closed: true };
      if (used.has(ns)) break;
      const nd = dirOf(ns, nFrom);
      if (dir.angleTo(nd) > limit) break;
      used.add(ns);
      pts.push(P(ns, 1 - nFrom));
      s = ns; end = 1 - nFrom; dir = nd;
    }
    return { pts, closed: false };
  }

  const a = P(pick, 0), b = P(pick, 1);
  // Straight edge first: collinear neighbours only.
  const fwd = walk(1, straightTurn), back = walk(0, straightTurn);
  const line = [...back.pts.reverse(), a, b, ...fwd.pts];
  const lineLen = line[0].distanceTo(line[line.length - 1]);
  // Then a curve: neighbours that turn gently.
  used.clear(); used.add(pick);
  const f2 = walk(1, maxTurn);
  const b2 = f2.closed ? { pts: [] } : walk(0, maxTurn);
  const curve = [...b2.pts.reverse(), a, b, ...f2.pts];
  if (curve.length >= 5) {
    const ring = f2.closed ? curve.slice(0, -1) : curve;
    const fit = fitCircle(ring);
    let len = 0;
    for (let i = 1; i < curve.length; i++) len += curve[i - 1].distanceTo(curve[i]);
    if (fit && fit.error < 0.06) {
      if (f2.closed) return { kind: 'circle', radius: fit.radius, diameter: fit.radius * 2, center: fit.center, normal: fit.normal, length: 2 * Math.PI * fit.radius, points: curve };
      if (len > lineLen * 1.02) {
        const sweep = THREE.MathUtils.radToDeg(len / fit.radius);
        return { kind: 'arc', radius: fit.radius, center: fit.center, normal: fit.normal, length: len, sweepDeg: sweep, points: curve };
      }
    }
    if (len > lineLen * 1.02 && !fit) return { kind: 'path', length: len, points: curve };
  }
  return { kind: 'line', length: lineLen, points: [line[0], line[line.length - 1]], a: line[0], b: line[line.length - 1] };
}

// Load study ------------------------------------------------------------------

/**
 * Area-weighted surface samples of a mesh in its local frame, at most `max` of them, each
 * carrying an equal share of `grams`. Taken once per part; posing just re-transforms them.
 */
export function massSamples(mesh, grams, max = 1500) {
  const g = mesh.geometry, pos = g.attributes.position, idx = g.index;
  const n = Math.floor((idx ? idx.count : pos.count) / 3);
  if (!n || !(grams > 0)) return new Float32Array(0);
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), t = new THREE.Vector3();
  const areas = new Float64Array(n);
  let total = 0;
  const tri = (i) => {
    const i0 = idx ? idx.getX(i * 3) : i * 3, i1 = idx ? idx.getX(i * 3 + 1) : i * 3 + 1, i2 = idx ? idx.getX(i * 3 + 2) : i * 3 + 2;
    a.fromBufferAttribute(pos, i0); b.fromBufferAttribute(pos, i1); c.fromBufferAttribute(pos, i2);
  };
  for (let i = 0; i < n; i++) {
    tri(i);
    areas[i] = t.subVectors(b, a).cross(c.clone().sub(a)).length() / 2;
    total += areas[i];
  }
  const k = Math.min(max, n);
  const out = new Float32Array(k * 4);
  // Systematic sampling along the cumulative area: deterministic and evenly spread.
  let acc = 0, i = 0;
  for (let s = 0; s < k; s++) {
    const target = (s + 0.5) / k * total;
    while (i < n - 1 && acc + areas[i] < target) { acc += areas[i]; i++; }
    tri(i);
    out[s * 4] = (a.x + b.x + c.x) / 3; out[s * 4 + 1] = (a.y + b.y + c.y) / 3; out[s * 4 + 2] = (a.z + b.z + c.z) / 3;
    out[s * 4 + 3] = grams / k;
  }
  return out;
}

/**
 * Static gravity bending moment along the load path (y up, metres, grams in, N·m out).
 * Path coordinate s = distance from `anchor` (where the structure meets the ground). Every
 * cross-section at s carries the weight of everything farther out; its moment about the
 * section's own centroid is g·|H - M·c| (H = sum of m·horizontal position beyond s,
 * M = mass beyond s, c = horizontal centroid of the section's band). Returns per-bin moments.
 */
export function gravityMoments(points, anchor, bins = 64) {
  const n = points.length / 4;
  let sMax = 1e-9;
  const s = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    s[i] = Math.hypot(points[i * 4] - anchor.x, points[i * 4 + 1] - anchor.y, points[i * 4 + 2] - anchor.z);
    sMax = Math.max(sMax, s[i]);
  }
  const m = new Float64Array(bins), hx = new Float64Array(bins), hz = new Float64Array(bins);
  for (let i = 0; i < n; i++) {
    const b = Math.min(bins - 1, Math.floor(s[i] / sMax * bins));
    const w = points[i * 4 + 3] / 1000;   // kg
    m[b] += w; hx[b] += w * points[i * 4]; hz[b] += w * points[i * 4 + 2];
  }
  const moment = new Float32Array(bins);
  let M = 0, HX = 0, HZ = 0;
  for (let b = bins - 1; b >= 0; b--) {
    // Section at the inner edge of band b carries band b and everything beyond it.
    M += m[b]; HX += hx[b]; HZ += hz[b];
    const cx = m[b] > 0 ? hx[b] / m[b] : (M > 0 ? HX / M : 0);
    const cz = m[b] > 0 ? hz[b] / m[b] : (M > 0 ? HZ / M : 0);
    moment[b] = 9.81 * Math.hypot(HX - M * cx, HZ - M * cz);
  }
  let peak = 0, peakBin = 0;
  for (let b = 0; b < bins; b++) if (moment[b] > peak) { peak = moment[b]; peakBin = b; }
  return { moment, sMax, peak, peakS: (peakBin + 0.5) / bins * sMax };
}
