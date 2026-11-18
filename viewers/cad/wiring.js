// Electronics layer for the CAD viewer: which parts are electrical, the harness that connects
// them (Arduino Uno + CNC Shield V3 with A4988 drivers, a 12 V supply, steppers, servos, end
// stops: the stack the engine's hw defaults and BOMs describe), the cables' conductors and pins,
// the harness BOM, and geometry for the boards the GLB does not carry.
//
// Pure planning + geometry with no DOM, so it runs in node tests (app/Tests/viewer). Routing
// through the model (joint anchors, live re-posing) lives in index.html; this file only turns a
// list of route points into a slack curve.
import * as THREE from 'three';

const NOT_ELECTRICAL = /bracket|mount|plate|pulley|spacer|keep-?out|shaft|cable|coupler|horn|gear|collar|hub|clamp|cover|shim|washer|screw|bolt|nut\b|key\b|envelope|clearance/i;
const KINDS = [
  { kind: 'motor', re: /28byj/i },   // before servo: "gripper_motor_(28BYJ; ref arm uses a servo)"
  { kind: 'servo', re: /servo|mg9\d+|sg90/i },
  { kind: 'motor', re: /(^|[^a-z])(motor|nema|stepper|28byj)/i },
  { kind: 'controller', re: /arduino|(^|[^a-z])uno([^a-z]|$)|cnc[-_ ]?shield|controller|mainboard|esp32|rp2040|\bpico\b/i },
  { kind: 'psu', re: /psu|power[-_ ]?supply|battery|lipo/i },
  { kind: 'endstop', re: /end-?stop|limit[-_ ]?switch|micro-?switch/i },
];

/** Electrical role of a part from its node name, or null. Motor *brackets* etc. are not motors. */
export function classify(name) {
  const n = String(name || '');
  if (NOT_ELECTRICAL.test(n) && !/^(motor|servo)[-_ ]?j?\d*$/i.test(n)) return null;
  const k = KINDS.find((x) => x.re.test(n));
  return k ? k.kind : null;
}

// Wire colours (display hex) and conductor sets.
export const WIRE = { black: 0x1E1E1E, red: 0xD0312D, green: 0x2E9E4F, blue: 0x2F6BD8, brown: 0x7A4A24, orange: 0xF08A24,
  yellow: 0xE8C228, pink: 0xE98BB0, white: 0xEDEDED };
const STEPPER_CONDUCTORS = [   // 17HS-style 4-wire, shield header pins 2B 2A 1A 1B
  { signal: 'A+ (coil 1)', color: 'black', pin: '1A' }, { signal: 'A- (coil 1)', color: 'green', pin: '1B' },
  { signal: 'B+ (coil 2)', color: 'red', pin: '2A' }, { signal: 'B- (coil 2)', color: 'blue', pin: '2B' },
];
const BYJ_CONDUCTORS = [       // 28BYJ-48 bipolar-modded (red common lead cut)
  { signal: 'A+ (coil 1)', color: 'orange', pin: '1A' }, { signal: 'A- (coil 1)', color: 'pink', pin: '1B' },
  { signal: 'B+ (coil 2)', color: 'yellow', pin: '2A' }, { signal: 'B- (coil 2)', color: 'blue', pin: '2B' },
];
const SERVO_CONDUCTORS = [
  { signal: 'GND', color: 'brown', pin: 'GND' }, { signal: 'V+ 5 V', color: 'red', pin: '5V' }, { signal: 'PWM', color: 'orange', pin: 'D12 (SpnEn)' },
];
const ENDSTOP_CONDUCTORS = [{ signal: 'Signal (NO)', color: 'white', pin: 'S' }, { signal: 'GND (COM)', color: 'black', pin: 'GND' }];
const POWER_CONDUCTORS = [{ signal: '+12 V', color: 'red', pin: '+' }, { signal: '0 V', color: 'black', pin: '-' }];

// CNC Shield V3 on the Uno: axis headers (STEP / DIR pins on the Uno) and end-stop pins.
export const AXES = [
  { axis: 'Z', step: 'D4', dir: 'D7', endstop: 'Z- (D11)' },
  { axis: 'Y', step: 'D3', dir: 'D6', endstop: 'Y- (D10)' },
  { axis: 'X', step: 'D2', dir: 'D5', endstop: 'X- (D9)' },
  { axis: 'A', step: 'D12', dir: 'D13', endstop: null },   // A clones / uses D12-D13 via jumpers
];

/**
 * Plan the harness. `parts`: [{ name, kind, depth }] with depth = joints between the part and
 * the ground (0 = on the base). Steppers take driver slots ground-first (Z yaw, Y shoulder,
 * X elbow, A wrist: the order the BAM BOM wires them). Returns { components, cables, notes }.
 */
export function planHarness(parts, opts = {}) {
  const notes = [];
  const ctl = parts.find((p) => p.kind === 'controller');
  const psu = parts.find((p) => p.kind === 'psu');
  const components = [
    { id: 'controller', label: ctl ? ctl.name : 'Arduino Uno R3 + CNC Shield V3', kind: 'controller', node: ctl ? ctl.name : null,
      spec: 'ATmega328P, 4 driver sockets X/Y/Z/A, 12-36 V screw terminal', pins: [] },
    { id: 'psu', label: psu ? psu.name : '12 V 5 A power supply', kind: 'psu', node: psu ? psu.name : null,
      spec: '12 V DC, 5 A (60 W), screw terminals', pins: [{ id: 'V+', signal: '+12 V' }, { id: 'V-', signal: '0 V' }] },
  ];
  const cables = [];
  const steppers = parts.filter((p) => p.kind === 'motor').sort((a, b) => (a.depth - b.depth) || a.name.localeCompare(b.name));
  const servos = parts.filter((p) => p.kind === 'servo').sort((a, b) => a.depth - b.depth);
  const stops = parts.filter((p) => p.kind === 'endstop').sort((a, b) => a.depth - b.depth);

  cables.push({ id: 'power', label: 'Power: supply to shield', from: { comp: 'psu', port: 'V+ / V-' }, to: { comp: 'controller', port: '12 V terminal' },
    conductors: POWER_CONDUCTORS, gauge: '18 AWG', connector: ['spade / ferrule', 'screw terminal'], radiusMM: 2.6, jacket: 0x262626, kind: 'power' });

  steppers.forEach((m, i) => {
    const slot = AXES[i];
    const byj = /28byj/i.test(m.name);
    components.push({ id: m.name, label: m.name, kind: 'motor', node: m.name, depth: m.depth,
      spec: byj ? '28BYJ-48 (bipolar mod)' : 'NEMA 17 bipolar stepper',
      pins: (byj ? BYJ_CONDUCTORS : STEPPER_CONDUCTORS).map((c) => ({ id: c.signal.split(' ')[0], signal: c.signal, color: c.color })) });
    if (!slot) { notes.push(`${m.name}: no free driver socket (the shield has four)`); return; }
    if (byj) notes.push(`${m.name}: 28BYJ-48 on an A4988 needs the bipolar mod (cut the red common lead)`);
    cables.push({ id: `motor-${m.name}`, label: `${slot.axis} axis: ${m.name}`, from: { comp: 'controller', port: `${slot.axis} motor header` },
      to: { comp: m.name, port: byj ? '5-pin JST-XH' : '6-pin JST-PH (4 used)' }, axis: slot.axis,
      conductors: (byj ? BYJ_CONDUCTORS : STEPPER_CONDUCTORS).map((c) => ({ ...c, pin: `${slot.axis}.${c.pin}` })),
      gauge: '22 AWG', connector: ['4-pin Dupont / XH', byj ? 'JST-XH 5' : 'JST-PH 6'], radiusMM: 2.1, jacket: 0x1E1E1E, kind: 'motor',
      logic: `STEP ${slot.step} · DIR ${slot.dir} · EN D8` });
  });

  servos.forEach((s, i) => {
    components.push({ id: s.name, label: s.name, kind: 'servo', node: s.name, depth: s.depth, spec: 'Hobby servo, 3-wire',
      pins: SERVO_CONDUCTORS.map((c) => ({ id: c.signal.split(' ')[0], signal: c.signal, color: c.color })) });
    const sig = i === 0 ? 'D12 (SpnEn)' : i === 1 ? 'D13 (SpnDir)' : 'A0 (Abort)';
    cables.push({ id: `servo-${s.name}`, label: `Servo: ${s.name}`, from: { comp: 'controller', port: `${sig} + 5 V/GND` }, to: { comp: s.name, port: '3-pin servo lead' },
      conductors: SERVO_CONDUCTORS.map((c) => (c.signal === 'PWM' ? { ...c, pin: sig } : c)),
      gauge: '24 AWG', connector: ['3-pin Dupont', 'JR/Futaba 3'], radiusMM: 1.5, jacket: 0x3A3A3A, kind: 'servo' });
    if (/mg99|mg996|ds3218/i.test(s.name)) notes.push(`${s.name}: a metal-gear servo can draw >1 A; power it from a 5-6 V BEC, not the Uno's 5 V`);
  });

  stops.forEach((e, i) => {
    const slot = AXES[i];
    components.push({ id: e.name, label: e.name, kind: 'endstop', node: e.name, depth: e.depth, spec: 'Micro switch, normally open',
      pins: ENDSTOP_CONDUCTORS.map((c) => ({ id: c.pin, signal: c.signal, color: c.color })) });
    if (!slot || !slot.endstop) { notes.push(`${e.name}: no free end-stop input`); return; }
    cables.push({ id: `stop-${e.name}`, label: `End stop ${slot.endstop}: ${e.name}`, from: { comp: 'controller', port: slot.endstop }, to: { comp: e.name, port: '2-pin' },
      conductors: ENDSTOP_CONDUCTORS.map((c) => ({ ...c, pin: c.pin === 'S' ? slot.endstop : 'GND' })),
      gauge: '26 AWG', connector: ['2-pin Dupont', '2-pin Dupont'], radiusMM: 1.2, jacket: 0x5A5A5A, kind: 'endstop' });
  });

  // Controller pin table from the cables that land on it.
  const ctlComp = components[0];
  for (const c of cables) {
    if (c.from.comp !== 'controller' && c.to.comp !== 'controller') continue;
    const peer = c.from.comp === 'controller' ? c.to.comp : c.from.comp;
    for (const k of c.conductors) ctlComp.pins.push({ id: k.pin, signal: k.signal, color: k.color, peer, cable: c.id });
  }
  if (opts.drivers !== false) {
    const n = Math.min(4, steppers.length);
    for (let i = 0; i < n; i++) ctlComp.pins.push({ id: `${AXES[i].axis} driver`, signal: `A4988 · STEP ${AXES[i].step} DIR ${AXES[i].dir}`, peer: null });
  }
  return { components, cables, notes, drivers: Math.min(4, steppers.length) };
}

/**
 * Plan the harness from the project's own wiring.json (next to the GLB) instead of guessing from part
 * names. spec: { controller: {label, spec, node, owned}, psu: {label, spec, node, owned, pins},
 * drivers: {count, owned, sockets: [{axis, step, dir, current, microstep}]},
 * components: [{id, label, kind, node, spec, pins}], cables: [{id, label, kind, axis, from: {comp, port},
 * to: {comp, port}, conductors: [{signal, color, pin}], gauge, connector: [a, b], logic}], notes: [] }.
 * `hasNode(name)` tells which model nodes exist; a component whose node is missing is placed like a board
 * (controller / psu) or has its cables skipped (others), with a note.
 */
export function planFromSpec(spec, hasNode = () => true) {
  const notes = [...(spec.notes || [])];
  const node = (n, label) => {
    if (!n) return null;
    if (hasNode(n)) return n;
    notes.push(`${label}: model part "${n}" not found; drawn without it`);
    return null;
  };
  const JACKET = { power: 0x262626, motor: 0x1E1E1E, servo: 0x3A3A3A, endstop: 0x5A5A5A, signal: 0x5A5A5A };
  const RADIUS = { power: 2.6, motor: 2.1, servo: 1.5, endstop: 1.2, signal: 1.2 };
  const comp = (c, kind) => ({ id: c.id || kind, label: c.label || c.id || kind, kind: c.kind || kind, node: node(c.node, c.label || c.id),
    spec: c.spec || '', owned: !!c.owned, depth: c.depth || 0,
    pins: (c.pins || []).map((p) => (typeof p === 'string' ? { id: p, signal: p } : p)) });
  const components = [comp({ ...(spec.controller || {}), id: 'controller' }, 'controller'), comp({ ...(spec.psu || {}), id: 'psu' }, 'psu')];
  for (const c of spec.components || []) components.push(comp(c, c.kind || 'part'));
  const ids = new Set(components.map((c) => c.id));
  const cables = [];
  for (const c of spec.cables || []) {
    if (!ids.has(c.from.comp) || !ids.has(c.to.comp)) { notes.push(`${c.label || c.id}: unknown end ${ids.has(c.from.comp) ? c.to.comp : c.from.comp}`); continue; }
    const kind = c.kind || 'signal';
    cables.push({ id: c.id, label: c.label || c.id, from: c.from, to: c.to, axis: c.axis, kind, logic: c.logic,
      conductors: (c.conductors || []).map((k) => ({ signal: k.signal, color: k.color in WIRE ? k.color : 'black', pin: k.pin })),
      gauge: c.gauge || '22 AWG', connector: c.connector || ['', ''], radiusMM: c.radiusMM || RADIUS[kind] || 1.5,
      jacket: c.jacket != null ? c.jacket : (JACKET[kind] || 0x3A3A3A) });
  }
  const ctl = components[0];
  for (const c of cables) {
    if (c.from.comp !== 'controller' && c.to.comp !== 'controller') continue;
    const peer = c.from.comp === 'controller' ? c.to.comp : c.from.comp;
    for (const k of c.conductors) ctl.pins.push({ id: k.pin, signal: k.signal, color: k.color, peer, cable: c.id });
  }
  const d = spec.drivers || {};
  for (const s of d.sockets || []) {
    ctl.pins.push({ id: `${s.axis} driver`, signal: `A4988 · STEP ${s.step} DIR ${s.dir}${s.current ? ` · ${s.current}` : ''}${s.microstep ? ` · ${s.microstep}` : ''}`, peer: null });
  }
  return { components, cables, notes, drivers: d.count != null ? d.count : (d.sockets || []).length, driversOwned: !!d.owned, fromSpec: true };
}

/** Harness BOM lines (with lengths in mm from the routed cables) and whether bom.csv has them. */
export function harnessBOM(plan, lengthsMM, bomRows = []) {
  const items = [];
  const has = (re) => bomRows.some((r) => re.test(`${r.item || ''} ${r.spec || ''}`));
  const add = (item, qty, spec, usedFor, usd, re) => items.push({ item, qty, spec, used_for: usedFor, est_unit_usd: usd, inBOM: has(re) });
  const ctl = plan.components.find((c) => c.id === 'controller');
  const psu = plan.components.find((c) => c.id === 'psu');
  if (!ctl.node && !ctl.owned) {
    add('Arduino Uno R3', 1, 'ATmega328P, USB-B', 'controller', 12, /arduino|\buno\b/i);
    add('CNC Shield V3', 1, '4 driver sockets X/Y/Z/A', 'controller', 5, /cnc\s*shield/i);
  }
  if (plan.drivers && !plan.driversOwned) add('A4988 stepper driver', plan.drivers, 'with heatsink; Vref for the motor current', 'X/Y/Z/A sockets', 2, /a4988|drv8825|tmc2\d{3}|stepper driver/i);
  if (!psu.node && !psu.owned) add('12 V 5 A power supply', 1, '60 W, screw terminals', 'motor power', 11, /power supply|psu|12\s*v.*\d\s*a/i);
  if (!plan.fromSpec) add('Electrolytic capacitor 100 uF 50 V', 1, 'across the shield power input', 'supply decoupling', 0.3, /capacitor/i);
  const byGauge = new Map();
  const conn = new Map();
  for (const c of plan.cables) {
    const L = (lengthsMM[c.id] || 0) * c.conductors.length;
    byGauge.set(c.gauge, (byGauge.get(c.gauge) || 0) + L);
    for (const k of c.connector) conn.set(k, (conn.get(k) || 0) + 1);
  }
  for (const [g, L] of byGauge) {
    const m = Math.ceil(L / 500) / 2;   // to the next 0.5 m
    if (m > 0) add(`Hook-up wire ${g}`, m, `${m} m total across conductors, stranded`, 'harness', g === '18 AWG' ? 0.8 : 0.4, new RegExp(`${g.replace(' ', '\\s*')}|hook-?up wire|stepper cable|motor cable`, 'i'));
  }
  for (const [k, n] of conn) {
    if (/screw terminal|spade/i.test(k)) continue;
    add(`${k} connector`, n, 'housing + crimp pins', 'harness ends', 0.15, new RegExp(k.split(' ')[0].replace(/[-/]/g, '.?'), 'i'));
  }
  const sleeve = Math.max(0, ...Object.values(lengthsMM));
  if (sleeve > 0) add('Spiral cable wrap 6 mm', Math.ceil(sleeve / 500) / 2, 'bundles the arm run, leaves slack at joints', 'harness', 1.5, /spiral|wrap|sleev|braid/i);
  return items;
}

/**
 * Route curve with slack: a sag midpoint (down, along -y) on every span, deepest where the
 * cable crosses a joint (the service loop), then a centripetal Catmull-Rom through all of it.
 */
export function slackCurve(points, { sag = 0.06, maxSag = Infinity, loops = [] } = {}) {
  const pts = [];
  for (let i = 0; i < points.length; i++) {
    if (i > 0) {
      const a = points[i - 1], b = points[i];
      const d = a.distanceTo(b);
      const k = loops.includes(i - 1) || loops.includes(i) ? sag * 1.8 : sag;
      if (d > 1e-9) pts.push(a.clone().lerp(b, 0.5).add(new THREE.Vector3(0, -Math.min(d * k, maxSag), 0)));
    }
    pts.push(points[i].clone());
  }
  return new THREE.CatmullRomCurve3(pts, false, 'centripetal');
}

// Geometry for parts the GLB lacks (sizes in mm; `s` converts mm to model units) -------------

function box(w, h, d, color, s, opts = {}) {
  // Emissive = its own colour: line mode has no lights, so the viewer drives emissiveIntensity instead.
  const m = new THREE.Mesh(new THREE.BoxGeometry(w * s, h * s, d * s),
    new THREE.MeshStandardMaterial({ color, emissive: color, roughness: 0.6, metalness: opts.metal || 0 }));
  m.userData.wiringPart = true;
  return m;
}
function at(o, x, y, z, s) { o.position.set(x * s, y * s, z * s); return o; }

/** Arduino Uno with a CNC Shield V3 stacked on top and A4988 drivers; y up, origin at the bottom centre. */
export function makeController(s, drivers = 4) {
  const g = new THREE.Group();
  g.name = 'Arduino Uno R3 + CNC Shield V3';
  g.add(at(box(68.6, 1.6, 53.4, 0x1F6FB2, s), 0, 4.8, 0, s));             // Uno PCB (blue)
  g.add(at(box(16, 11, 12, 0xB8BCC2, s, { metal: 0.6 }), -30, 11, -14, s));    // USB-B
  g.add(at(box(14, 11, 9, 0x1A1A1A, s), -30, 11, 16, s));                     // barrel jack
  for (const [x, z] of [[-31, -24], [31, -24], [-31, 24], [31, 24]]) g.add(at(box(3, 4, 3, 0xC0C0C0, s), x, 2, z, s));   // standoffs
  g.add(at(box(68.6, 1.6, 53.4, 0x1C1C1C, s), 0, 16.8, 0, s));            // shield PCB (black)
  for (let i = 0; i < 4; i++) {
    const x = -24 + i * 16;
    g.add(at(box(15.5, 1.6, 20.5, i < drivers ? 0x2E7D32 : 0x333333, s), x, 24, -6, s));   // driver board
    if (i < drivers) g.add(at(box(9, 8, 9, 0xC7CBD1, s, { metal: 0.7 }), x, 29, -6, s));   // heatsink
    g.add(at(box(10, 2.5, 2.5, 0x111111, s), x, 19.5, 12, s));                // motor header
  }
  g.add(at(box(9, 9, 7, 0x2E8B57, s), 28, 22, 21, s));                       // power screw terminal
  g.add(at(box(6, 11, 6, 0x111111, s), 18, 23, 21, s));                      // 100 uF capacitor
  return g;
}
/** Enclosed 12 V switching supply with its terminal strip. */
export function makePSU(s) {
  const g = new THREE.Group();
  g.name = '12 V 5 A power supply';
  g.add(at(box(110, 36, 78, 0xB9BDC3, s, { metal: 0.55 }), 0, 18, 0, s));
  g.add(at(box(14, 14, 70, 0x1A1A1A, s), 58, 9, 0, s));
  for (let i = 0; i < 6; i++) g.add(at(box(6, 4, 6, 0xD9A441, s, { metal: 0.6 }), 60, 18, -27 + i * 11, s));
  return g;
}
