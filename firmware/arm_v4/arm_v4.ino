/* arm_v4 - 24-hour robot arm v4 (design/v4 = v3 arm + parallel-jaw gripper): Arduino Uno R3 + CNC Shield V3 + 4x A4988.
 *
 * Sockets: Z = yaw (XY42, 20T->120T, 6:1), Y = shoulder (XY42, 20T->72T | 36T->140T, 14:1),
 * X = elbow (XY42 on the lower shank, 20T->140T, 7:1, drives th2 - th1),
 * A = wrist (HEM 34 mm on the upper shank, 20T->60T, 3:1, drives wr - th2).
 * Socket A: set the shield's A-axis jumpers to D12 (STEP) / D13 (DIR) (the SpnEn/SpnDir pins).
 * Gripper servo (MG996R) on CoolEn = A3. Yaw home switch (KW12-3, NO to GND) on the Z limit = D11.
 * Microstepping: 1/8 on the shoulder (Y: remove its MS3 jumper), 1/16 on the others: keeps the
 * Uno's software step rate near 4 k steps/s at the default 20 deg/s.
 * Shoulder, elbow and wrist have no switches: put the arm in the REST pose by hand with the motors off
 * (lower shank vertical, upper shank level, gripper pointing down: th1 90, th2 0, wr -90) and send HOME.
 *
 * Commands (degrees / mm, newline-terminated, 115200 baud):
 *   PING | STATUS | STREAM 0|1 | ENABLE 0|1 | STOP | REST | HOME
 *   J <yaw> <th1> <th2> <wr>   joint move, absolute pitches (wr = gripper axis, -90 = down)
 *   P <x> <y> <z> [pitch]      fingertip centre (mm above the table), gripper pitch default -90
 *   GRIP <0..100>              0 = closed, 100 = open
 *   SPEED <deg/s> | ACCEL <deg/s^2>
 * Rule breaks: none (delayMicroseconds(2) is the A4988 step pulse).
 */
// mechy-lib: arduino-libraries/Servo
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <Servo.h>
#include "mechy_control.h"

// Pins as wired in hw/wiring.yaml (checked by `mechy wiring check`):
// mechy-pin: uno.D4 -> shield.Z_STEP
// mechy-pin: uno.D7 -> shield.Z_DIR
// mechy-pin: uno.D3 -> shield.Y_STEP
// mechy-pin: uno.D6 -> shield.Y_DIR
// mechy-pin: uno.D2 -> shield.X_STEP
// mechy-pin: uno.D5 -> shield.X_DIR
// mechy-pin: uno.D12 -> shield.A_STEP
// mechy-pin: uno.D13 -> shield.A_DIR
// mechy-pin: uno.D8 -> shield.EN
// mechy-pin: uno.D11 -> yaw_switch.NO
// mechy-pin: uno.A3 -> servo.SIG
const uint8_t N = 4;                                   // 0 yaw, 1 shoulder, 2 elbow, 3 wrist
const uint8_t STEP_PIN[N] = {4, 3, 2, 12};             // Z, Y, X, A (A via the shield jumpers)
const uint8_t DIR_PIN[N] = {7, 6, 5, 13};
const uint8_t EN_PIN = 8, YAW_SW_PIN = 11, GRIP_PIN = A3;
const bool DIR_INVERT[N] = {false, false, false, false};   // flip on the bench if an axis runs backwards

// ---- mechanics (design/v3/geometry.py) ----
const float MICRO[N] = {16, 8, 16, 16};
// Shoulder motor pulley teeth: 20 (as built) or 16 (torque upgrade 2026-11-16: 72/16 x 140/36 = 17.5:1). Set it to
// the pulley actually on the shoulder motor, or every shoulder move is off by 25 %.
#define SHOULDER_PULLEY_T 20
const float RATIO[N] = {6.0f, (72.0f / SHOULDER_PULLEY_T) * (140.0f / 36.0f), 7.0f, 3.0f};
const float L1 = 150.0f, L2 = 150.0f, S_X = 10.0f, S_Z = 116.0f, TOOL = 89.0f;
const float YAW_MIN = -150, YAW_MAX = 150, TH1_MIN = 20, TH1_MAX = 140;
const float Q2_MIN = -135, Q2_MAX = 100, Q3_MIN = -95, Q3_MAX = 95;   // design/v4/geometry.py (CAD pose checks)
// reach rule: wrist point W >= 45 mm above the table, >= 95 mm within 200 mm of the yaw axis; tip >= 3 mm
const float W_Z_MIN = 45, W_Z_NEAR = 95, NEAR_R = 200, TIP_Z_MIN = 3;
const float REST_J[N] = {0.0f, 90.0f, 0.0f, -90.0f};   // yaw, th1, th2, wr at the rest pose
const int GRIP_US_CLOSED = 1250, GRIP_US_OPEN = 1920;  // [est] ~60 deg of crank travel (-10..+50); calibrate

float stepsPerDeg(uint8_t i) { return 200.0f * MICRO[i] * RATIO[i] / 360.0f; }

// motor coordinates from joint angles: yaw, th1, q2 = th2 - th1, q3 = wr - th2
void toMotor(const float j[N], float m[N]) { m[0] = j[0]; m[1] = j[1]; m[2] = j[2] - j[1]; m[3] = j[3] - j[2]; }

long stepPos[N] = {0, 0, 0, 0};                        // steps from the rest pose (yaw: from the switch edge)
long startSteps[N], deltaSteps[N];
float jStart[N], jTarget[N];
float vMax = 20.0f, aMax = 40.0f;
bool enabled = false, armZeroed = false, yawHomed = false, moving = false, streaming = false;
mc::Trapezoid prof;
uint32_t moveStartUs = 0;
mc::FixedRate teleTick(100000);
Servo grip;
enum HomeState { H_IDLE, H_SEEK, H_BACKOFF, H_SLOW } homeState = H_IDLE;
int homeDir = 1;

float motorDeg(uint8_t i) {
  float r[N]; toMotor(REST_J, r);
  return stepPos[i] / stepsPerDeg(i) + r[i];
}
void joints(float j[N]) {                              // current joint angles from the motor positions
  j[0] = motorDeg(0); j[1] = motorDeg(1); j[2] = j[1] + motorDeg(2); j[3] = j[2] + motorDeg(3);
}
bool yawSwitch() { return digitalRead(YAW_SW_PIN) == LOW; }
bool yawEdge() { return homeDir > 0 ? !yawSwitch() : yawSwitch(); }

void stepOnce(uint8_t i, int dir) {
  digitalWrite(DIR_PIN[i], (dir > 0) != DIR_INVERT[i] ? HIGH : LOW);
  digitalWrite(STEP_PIN[i], HIGH);
  delayMicroseconds(2);
  digitalWrite(STEP_PIN[i], LOW);
  stepPos[i] += dir;
}

void setEnabled(bool on) {
  enabled = on;
  digitalWrite(EN_PIN, on ? LOW : HIGH);
  if (!on) { moving = false; homeState = H_IDLE; }
}

/* Keeps the gripper off the table, base, turret and Uno: wrist point and fingertip in the arm plane. */
bool clearOk(const float j[N]) {
  float a1 = j[1] / 57.29578f, a2 = j[2] / 57.29578f, a3 = j[3] / 57.29578f;
  float wr = S_X + L1 * cosf(a1) + L2 * cosf(a2), wz = S_Z + L1 * sinf(a1) + L2 * sinf(a2);
  if (wz < W_Z_MIN || (fabsf(wr) < NEAR_R && wz < W_Z_NEAR)) return false;
  return wz + TOOL * sinf(a3) >= TIP_Z_MIN;
}

bool jointsOk(const float j[N]) {
  float q2 = j[2] - j[1], q3 = j[3] - j[2];
  return j[0] >= YAW_MIN && j[0] <= YAW_MAX && j[1] >= TH1_MIN && j[1] <= TH1_MAX
         && q2 >= Q2_MIN && q2 <= Q2_MAX && q3 >= Q3_MIN && q3 <= Q3_MAX && clearOk(j);
}

/* Moves are straight lines in joint space: check 16 points along the way, not only the target. */
bool pathOk(const float tgt[N]) {
  float cur[N], p[N]; joints(cur);
  for (uint8_t k = 1; k <= 16; k++) {
    for (uint8_t i = 0; i < N; i++) p[i] = cur[i] + (tgt[i] - cur[i]) * k / 16.0f;
    if (!jointsOk(p)) return false;
  }
  return true;
}

/* Straight line in joint space; every motor arrives together; trapezoid on the largest joint change. */
void startMove(const float tgt[N], float v, float a) {
  float m[N], r[N], cur[N];
  toMotor(tgt, m); toMotor(REST_J, r); joints(cur);
  float maxd = 0;
  for (uint8_t i = 0; i < N; i++) {
    startSteps[i] = stepPos[i];
    deltaSteps[i] = lround((m[i] - r[i]) * stepsPerDeg(i)) - stepPos[i];
    maxd = max(maxd, fabsf(tgt[i] - cur[i]));
  }
  prof.plan(0.0f, maxd, v, a);
  moveStartUs = micros();
  moving = maxd > 0;
}

void runProfile() {
  if (!moving) return;
  float t = (micros() - moveStartUs) * 1e-6f;
  float s = prof.dist > 0 ? prof.position(t) / prof.dist : 1.0f;
  bool done = t >= prof.duration;
  for (uint8_t i = 0; i < N; i++) {
    long want = startSteps[i] + lround(s * deltaSteps[i]);
    int budget = 3;
    while (stepPos[i] != want && budget--) stepOnce(i, want > stepPos[i] ? 1 : -1);
    if (stepPos[i] != startSteps[i] + deltaSteps[i]) done = false;
  }
  if (done) { moving = false; if (homeState == H_IDLE) Serial.println(F("DONE MOVE")); }
}

void yawMove(float dYaw, float v) {
  float j[N]; joints(j); j[0] += dYaw; startMove(j, v, aMax);
}

/* Yaw homing on the half-moon cam (pressed for yaw < 0): seek the edge, back off, slow seek. */
void runHoming() {
  if (homeState == H_IDLE) return;
  if ((homeState == H_SEEK || homeState == H_SLOW) && yawEdge()) {
    moving = false;
    if (homeState == H_SEEK) { homeState = H_BACKOFF; yawMove(-homeDir * 5.0f, 10.0f); }
    else { stepPos[0] = 0; yawHomed = true; homeState = H_IDLE; Serial.println(F("DONE HOME")); }
    return;
  }
  if (moving) return;
  if (homeState == H_BACKOFF) { homeState = H_SLOW; yawMove(homeDir * 10.0f, 3.0f); }
  else { homeState = H_IDLE; Serial.println(F("ERR HOME_FAIL yaw switch edge not found")); }
}

/* Fingertip (x, y, z) with gripper pitch p (deg) -> joints. Elbow-up solution. */
bool ik(float x, float y, float z, float p, float j[N]) {
  j[0] = atan2f(y, x) * 57.29578f;
  float pr = p / 57.29578f;
  float r = sqrtf(x * x + y * y) - TOOL * cosf(pr) - S_X;
  float h = z - TOOL * sinf(pr) - S_Z;
  float c = (r * r + h * h - L1 * L1 - L2 * L2) / (2 * L1 * L2);
  if (c < -1 || c > 1) return false;
  float q2 = -acosf(c);
  float q1 = atan2f(h, r) - atan2f(L2 * sinf(q2), L1 + L2 * cosf(q2));
  j[1] = q1 * 57.29578f; j[2] = (q1 + q2) * 57.29578f; j[3] = p;
  return true;
}

void reply(const __FlashStringHelper *s) { Serial.println(s); }

bool readyToMove() {
  if (!enabled) { reply(F("ERR DISABLED")); return false; }
  if (!armZeroed || !yawHomed) { reply(F("ERR NOT_HOMED send HOME")); return false; }
  if (moving || homeState != H_IDLE) { reply(F("ERR BUSY")); return false; }
  return true;
}

void handleLine(char *line) {
  char *name = strtok(line, " \t");
  if (!name) return;
  for (char *c = name; *c; c++) if (*c >= 'a' && *c <= 'z') *c -= 32;
  char *a[4];
  float v[4];
  uint8_t n = 0;
  for (; n < 4; n++) { a[n] = strtok(NULL, " \t"); if (!a[n]) break; v[n] = atof(a[n]); }
  bool busy = moving || homeState != H_IDLE;
  if (!strcmp(name, "PING")) reply(F("OK PONG"));
  else if (!strcmp(name, "ENABLE") && n >= 1) {
    setEnabled(v[0] != 0);
    if (enabled && !grip.attached()) grip.attach(GRIP_PIN);
    Serial.print(F("OK ENABLE ")); Serial.println(enabled);
  } else if (!strcmp(name, "STOP")) { moving = false; homeState = H_IDLE; reply(F("OK STOP")); }
  else if (!strcmp(name, "STREAM") && n >= 1) { streaming = v[0] != 0; reply(F("OK STREAM")); }
  else if (!strcmp(name, "SPEED") && n >= 1 && v[0] > 0) { vMax = mc::clampf(v[0], 1, 40); reply(F("OK SPEED")); }
  else if (!strcmp(name, "ACCEL") && n >= 1 && v[0] > 0) { aMax = mc::clampf(v[0], 1, 150); reply(F("OK ACCEL")); }
  else if (!strcmp(name, "REST")) {
    if (busy) { reply(F("ERR BUSY")); return; }
    stepPos[1] = stepPos[2] = stepPos[3] = 0; armZeroed = true; reply(F("OK REST th1=90 th2=0 wr=-90"));
  } else if (!strcmp(name, "HOME")) {
    if (!enabled) { reply(F("ERR DISABLED")); return; }
    if (busy) { reply(F("ERR BUSY")); return; }
    stepPos[1] = stepPos[2] = stepPos[3] = 0; armZeroed = true; yawHomed = false;
    homeDir = yawSwitch() ? 1 : -1;
    homeState = H_SEEK;
    yawMove(homeDir * 170.0f, 15.0f);                  // the cam edge is at most 150 deg away
    reply(F("OK HOME"));
  } else if (!strcmp(name, "J") && n >= 4) {
    if (!readyToMove()) return;
    if (!jointsOk(v)) { reply(F("ERR LIMIT")); return; }
    if (!pathOk(v)) { reply(F("ERR PATH")); return; }
    startMove(v, vMax, aMax);
    Serial.print(F("OK J T=")); Serial.println(prof.duration, 2);
  } else if (!strcmp(name, "P") && n >= 3) {
    if (!readyToMove()) return;
    float j[N];
    if (!ik(v[0], v[1], v[2], n >= 4 ? v[3] : -90.0f, j) || !jointsOk(j)) { reply(F("ERR UNREACHABLE")); return; }
    if (!pathOk(j)) { reply(F("ERR PATH")); return; }
    startMove(j, vMax, aMax);
    Serial.print(F("OK P th1=")); Serial.print(j[1], 1); Serial.print(F(" th2=")); Serial.println(j[2], 1);
  } else if (!strcmp(name, "GRIP") && n >= 1) {
    float f = mc::clampf(v[0], 0, 100) / 100.0f;
    grip.writeMicroseconds((int)(GRIP_US_CLOSED + f * (GRIP_US_OPEN - GRIP_US_CLOSED)));
    reply(F("OK GRIP"));
  } else if (!strcmp(name, "STATUS")) {
    float j[N]; joints(j);
    Serial.print(F("OK STATUS yaw=")); Serial.print(j[0], 2); Serial.print(F(" th1=")); Serial.print(j[1], 2);
    Serial.print(F(" th2=")); Serial.print(j[2], 2); Serial.print(F(" wr=")); Serial.print(j[3], 2);
    Serial.print(F(" en=")); Serial.print(enabled); Serial.print(F(" homed=")); Serial.print(armZeroed && yawHomed);
    Serial.print(F(" moving=")); Serial.print(moving); Serial.print(F(" yaw_sw=")); Serial.println(yawSwitch());
  } else { Serial.print(F("ERR UNKNOWN ")); Serial.println(name); }
}

void readSerial() {
  static char buf[56];
  static uint8_t len = 0;
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') { buf[len] = '\0'; if (len) handleLine(buf); len = 0; }
    else if (len < sizeof(buf) - 1) buf[len++] = c;
    else len = 0;
  }
}

void setup() {
  for (uint8_t i = 0; i < N; i++) { pinMode(STEP_PIN[i], OUTPUT); pinMode(DIR_PIN[i], OUTPUT); }
  pinMode(EN_PIN, OUTPUT);
  pinMode(YAW_SW_PIN, INPUT_PULLUP);
  setEnabled(false);                                   // drivers off until ENABLE 1
  Serial.begin(115200);
  uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 2000) {}
  Serial.println(F("READY arm_v4 proto=1"));
}

void loop() {
  readSerial();
  runHoming();
  runProfile();
  // print only when the 64-byte TX buffer has room for the whole line: a blocking print would stall the steps
  if (streaming && teleTick.due(micros()) && Serial.availableForWrite() >= 60) {
    float j[N]; joints(j);
    Serial.print(F("DATA yaw=")); Serial.print(j[0], 2); Serial.print(F(" th1=")); Serial.print(j[1], 2);
    Serial.print(F(" th2=")); Serial.print(j[2], 2); Serial.print(F(" wr=")); Serial.println(j[3], 2);
  }
}
