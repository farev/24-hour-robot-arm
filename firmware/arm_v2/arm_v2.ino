/* arm_v2 - 24-hour robot arm v2 (design/v2): Arduino Uno R3 + CNC Shield V3 + 3x A4988.
 *
 * Axes (CNC shield sockets): X = elbow motor (lever pulley -> upper shank ABSOLUTE pitch th2),
 * Y = shoulder motor (lower shank pitch th1), Z = base yaw. All GT2 belts: 20T -> 140T (7:1) on
 * shoulder/elbow, 20T -> 120T (6:1) on yaw. Parallel linkage: each motor sets one absolute angle,
 * no coupling maths. Wrist servo (MG996R) on SpnEn = D12, gripper servo on SpnDir = D13.
 * Yaw home switch (KW12-3, NO to GND) on the Z limit header = D11; its cam presses it for yaw < 0,
 * so HOME finds the edge at yaw = 0 from either side.
 * Shoulder/elbow have no switches: put the arm in the REST pose by hand with the motors off
 * (lower shank vertical, upper shank level: th1 = 90, th2 = 0) and send REST, or HOME (= yaw homing + REST).
 *
 * Commands (degrees and mm at this boundary, newline-terminated, 115200 baud):
 *   PING | STATUS | STREAM 0|1 | ENABLE 0|1 | STOP
 *   REST                    arm is at th1=90 th2=0 (hand-placed): sets shoulder/elbow zero
 *   HOME                    REST + yaw homing on the switch (motors must be enabled)
 *   J <yaw> <th1> <th2>     joint move, absolute degrees (gripper kept pointing down)
 *   P <x> <y> <z>           fingertip centre, mm, gripper pointing down (z above the table)
 *   GRIP <0..100>           0 = closed, 100 = open
 *   WRIST <deg>             gripper axis pitch: -90 = down (default), 0 = forward
 *   SPEED <deg/s> | ACCEL <deg/s^2>   joint-space limits
 * Rule breaks: none. delayMicroseconds(2) in stepOnce is the A4988 STEP pulse width (>= 1 us).
 */
// mechy-lib: arduino-libraries/Servo
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <Servo.h>
#include "mechy_control.h"

// ---- pins: CNC Shield V3 on an Uno (Protoneer pinout) ----
const uint8_t STEP_PIN[3] = {4, 3, 2};    // yaw = Z, shoulder = Y, elbow = X
const uint8_t DIR_PIN[3] = {7, 6, 5};
const uint8_t EN_PIN = 8;                 // shared, active low
const uint8_t YAW_SW_PIN = 11;            // Z limit header (Z+ / Z- are both D11 on V3)
const uint8_t WRIST_PIN = 12, GRIP_PIN = 13;
const bool DIR_INVERT[3] = {false, false, false};   // flip on the bench if an axis runs backwards

// ---- mechanics (design/v2/geometry.py) ----
const float MICROSTEP = 16.0f;            // all three MS jumpers fitted on the shield
const float RATIO[3] = {6.0f, 7.0f, 7.0f};
const float STEPS_PER_DEG[3] = {200.0f * MICROSTEP * RATIO[0] / 360.0f,
                                200.0f * MICROSTEP * RATIO[1] / 360.0f,
                                200.0f * MICROSTEP * RATIO[2] / 360.0f};
const float L1 = 150.0f, L2 = 150.0f, S_X = 10.0f, S_Z = 116.0f, TOOL = 105.0f;   // mm
const float YAW_MIN = -150, YAW_MAX = 150, TH1_MIN = 20, TH1_MAX = 140, TH2_MIN = -80, TH2_MAX = 60;
const float INT_MIN = 40, INT_MAX = 150;  // elbow interior angle limits (deg)
const float TH2_MAX_GRIP_DOWN = 30;       // gripper-down hits the upper shank above this (CAD pose check)
const float REST[3] = {0.0f, 90.0f, 0.0f};
// wrist servo: 1500 us = gripper on the upper shank axis... calibrate WRIST_US_PER_DEG / WRIST_US_0 on the bench
const float WRIST_US_0 = 1500.0f, WRIST_US_PER_DEG = -10.0f;   // [est] MG996R ~10 us/deg
const int GRIP_US_CLOSED = 1300, GRIP_US_OPEN = 1800;             // [est] calibrate

// ---- state ----
long stepPos[3] = {0, 0, 0};
long startSteps[3], deltaSteps[3];
float vMax = 30.0f, aMax = 60.0f;         // deg/s, deg/s^2 (joint space, on the largest joint change)
bool enabled = false, armZeroed = false, yawHomed = false, moving = false, streaming = false;
float wristPitch = -90.0f;                // absolute gripper axis pitch, deg
mc::Trapezoid prof;                       // normalised 0..1 along the move
uint32_t moveStartUs = 0;
mc::FixedRate servoTick(20000), teleTick(100000);   // 50 Hz servo update, 10 Hz telemetry
Servo wrist, grip;
enum HomeState { H_IDLE, H_SEEK, H_BACKOFF, H_SLOW } homeState = H_IDLE;
int homeDir = 1;

float jointDeg(uint8_t i) { return stepPos[i] / STEPS_PER_DEG[i] + REST[i]; }   // REST[0] = 0 (yaw zero = switch edge)
bool yawSwitch() { return digitalRead(YAW_SW_PIN) == LOW; }
bool yawEdge() { return homeDir > 0 ? !yawSwitch() : yawSwitch(); }   // the cam edge reached in the seek direction

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

bool jointsOk(float yaw, float t1, float t2) {
  float inter = 180.0f - (t1 - t2);
  return yaw >= YAW_MIN && yaw <= YAW_MAX && t1 >= TH1_MIN && t1 <= TH1_MAX && t2 >= TH2_MIN && t2 <= TH2_MAX
         && inter >= INT_MIN && inter <= INT_MAX;
}

/* Joint-space straight line: every axis reaches its target together, trapezoid on the largest change. */
void startMove(float yaw, float t1, float t2, float v, float a) {
  float tgt[3] = {yaw, t1, t2};
  float maxd = 0;
  for (uint8_t i = 0; i < 3; i++) {
    startSteps[i] = stepPos[i];
    long want = lround((tgt[i] - REST[i]) * STEPS_PER_DEG[i]);
    deltaSteps[i] = want - stepPos[i];
    maxd = max(maxd, fabsf(tgt[i] - jointDeg(i)));
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
  for (uint8_t i = 0; i < 3; i++) {
    long want = startSteps[i] + lround(s * deltaSteps[i]);
    int budget = 3;                       // a few steps per call keeps the loop and serial responsive
    while (stepPos[i] != want && budget--) stepOnce(i, want > stepPos[i] ? 1 : -1);
    if (stepPos[i] != startSteps[i] + deltaSteps[i]) done = false;
  }
  if (done) {
    moving = false;
    if (homeState == H_IDLE) Serial.println(F("DONE MOVE"));
  }
}

/* Yaw homing: the cam presses the switch for yaw < 0, so the edge at yaw = 0 is found from either side
 * within 150 deg. Seek the edge, back off 5 deg, seek again slowly, call that zero. */
void runHoming() {
  if (homeState == H_IDLE) return;
  if ((homeState == H_SEEK || homeState == H_SLOW) && yawEdge()) {
    moving = false;
    if (homeState == H_SEEK) {
      homeState = H_BACKOFF;
      startMove(jointDeg(0) - homeDir * 5.0f, jointDeg(1), jointDeg(2), 10.0f, aMax);
    } else {
      stepPos[0] = 0; yawHomed = true; homeState = H_IDLE;
      Serial.println(F("DONE HOME"));
    }
    return;
  }
  if (moving) return;
  if (homeState == H_BACKOFF) {
    homeState = H_SLOW;
    startMove(jointDeg(0) + homeDir * 10.0f, jointDeg(1), jointDeg(2), 3.0f, aMax);
  } else {                               // a seek ended without finding the edge
    homeState = H_IDLE;
    Serial.println(F("ERR HOME_FAIL yaw switch edge not found"));
  }
}

/* Gripper-down IK: fingertip (x, y, z) mm -> yaw, th1, th2 (deg). Elbow-up solution. */
bool ikDown(float x, float y, float z, float &yaw, float &t1, float &t2) {
  yaw = atan2f(y, x) * 57.29578f;
  float r = sqrtf(x * x + y * y) - S_X;
  float h = z + TOOL - S_Z;              // wrist W above S
  float d2 = r * r + h * h;
  float c = (d2 - L1 * L1 - L2 * L2) / (2 * L1 * L2);
  if (c < -1 || c > 1) return false;
  float q2 = -acosf(c);                  // elbow above the line S-W
  float q1 = atan2f(h, r) - atan2f(L2 * sinf(q2), L1 + L2 * cosf(q2));
  t1 = q1 * 57.29578f;
  t2 = (q1 + q2) * 57.29578f;
  return true;
}

void updateServos() {
  float rel = wristPitch - jointDeg(2);  // gripper axis relative to the upper shank
  wrist.writeMicroseconds((int)mc::clampf(WRIST_US_0 + WRIST_US_PER_DEG * (rel + 90.0f), 600, 2400));
}

void reply(const __FlashStringHelper *s) { Serial.println(s); }

void handleLine(char *line) {
  char *name = strtok(line, " \t");
  if (!name) return;
  for (char *p = name; *p; p++) if (*p >= 'a' && *p <= 'z') *p -= 32;
  char *a1 = strtok(NULL, " \t"), *a2 = strtok(NULL, " \t"), *a3 = strtok(NULL, " \t");
  float x = a1 ? atof(a1) : 0, y = a2 ? atof(a2) : 0, z = a3 ? atof(a3) : 0;
  bool busy = moving || homeState != H_IDLE;
  if (!strcmp(name, "PING")) reply(F("OK PONG"));
  else if (!strcmp(name, "ENABLE") && a1) { setEnabled(atoi(a1)); Serial.print(F("OK ENABLE ")); Serial.println(enabled); }
  else if (!strcmp(name, "STOP")) { moving = false; homeState = H_IDLE; reply(F("OK STOP")); }
  else if (!strcmp(name, "STREAM") && a1) { streaming = atoi(a1); reply(F("OK STREAM")); }
  else if (!strcmp(name, "SPEED") && x > 0) { vMax = mc::clampf(x, 1, 60); reply(F("OK SPEED")); }
  else if (!strcmp(name, "ACCEL") && x > 0) { aMax = mc::clampf(x, 1, 200); reply(F("OK ACCEL")); }
  else if (!strcmp(name, "REST")) {
    if (busy) { reply(F("ERR BUSY")); return; }
    stepPos[1] = stepPos[2] = 0; armZeroed = true; reply(F("OK REST th1=90 th2=0"));
  } else if (!strcmp(name, "HOME")) {
    if (!enabled) { reply(F("ERR DISABLED")); return; }
    if (busy) { reply(F("ERR BUSY")); return; }
    stepPos[1] = stepPos[2] = 0; armZeroed = true; yawHomed = false;
    homeDir = yawSwitch() ? 1 : -1;      // pressed -> we are at yaw < 0 -> seek +
    homeState = H_SEEK;
    startMove(jointDeg(0) + homeDir * 170.0f, jointDeg(1), jointDeg(2), 15.0f, aMax);   // edge is <= 150 deg away
    reply(F("OK HOME"));
  } else if (!strcmp(name, "J") && a3) {
    if (!enabled) { reply(F("ERR DISABLED")); return; }
    if (!armZeroed || !yawHomed) { reply(F("ERR NOT_HOMED send HOME")); return; }
    if (busy) { reply(F("ERR BUSY")); return; }
    if (!jointsOk(x, y, z)) { reply(F("ERR LIMIT")); return; }
    if (wristPitch < -60 && z > TH2_MAX_GRIP_DOWN) { reply(F("ERR LIMIT gripper-down needs th2<=30")); return; }
    startMove(x, y, z, vMax, aMax);
    Serial.print(F("OK J T=")); Serial.println(prof.duration, 2);
  } else if (!strcmp(name, "P") && a3) {
    if (!enabled) { reply(F("ERR DISABLED")); return; }
    if (!armZeroed || !yawHomed) { reply(F("ERR NOT_HOMED send HOME")); return; }
    if (busy) { reply(F("ERR BUSY")); return; }
    float yw, t1, t2;
    if (!ikDown(x, y, z, yw, t1, t2) || !jointsOk(yw, t1, t2) || t2 > TH2_MAX_GRIP_DOWN) { reply(F("ERR UNREACHABLE")); return; }
    wristPitch = -90.0f;
    startMove(yw, t1, t2, vMax, aMax);
    Serial.print(F("OK P yaw=")); Serial.print(yw, 1); Serial.print(F(" th1=")); Serial.print(t1, 1);
    Serial.print(F(" th2=")); Serial.println(t2, 1);
  } else if (!strcmp(name, "GRIP") && a1) {
    float f = mc::clampf(x, 0, 100) / 100.0f;
    grip.writeMicroseconds((int)(GRIP_US_CLOSED + f * (GRIP_US_OPEN - GRIP_US_CLOSED)));
    reply(F("OK GRIP"));
  } else if (!strcmp(name, "WRIST") && a1) {
    wristPitch = mc::clampf(x, -90, 30); reply(F("OK WRIST"));
  } else if (!strcmp(name, "STATUS")) {
    Serial.print(F("OK STATUS yaw=")); Serial.print(jointDeg(0), 2);
    Serial.print(F(" th1=")); Serial.print(jointDeg(1), 2); Serial.print(F(" th2=")); Serial.print(jointDeg(2), 2);
    Serial.print(F(" en=")); Serial.print(enabled); Serial.print(F(" homed=")); Serial.print(armZeroed && yawHomed);
    Serial.print(F(" moving=")); Serial.print(moving); Serial.print(F(" yaw_sw=")); Serial.print(yawSwitch());
    Serial.print(F(" overruns=")); Serial.println(servoTick.overruns);
  } else { Serial.print(F("ERR UNKNOWN ")); Serial.println(name); }
}

void readSerial() {
  static char buf[48];
  static uint8_t len = 0;
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') { buf[len] = '\0'; if (len) handleLine(buf); len = 0; }
    else if (len < sizeof(buf) - 1) buf[len++] = c;
    else len = 0;                        // over-long line: drop it
  }
}

void setup() {
  for (uint8_t i = 0; i < 3; i++) { pinMode(STEP_PIN[i], OUTPUT); pinMode(DIR_PIN[i], OUTPUT); }
  pinMode(EN_PIN, OUTPUT);
  pinMode(YAW_SW_PIN, INPUT_PULLUP);
  setEnabled(false);                     // drivers off until ENABLE 1: nothing holds or moves at boot
  Serial.begin(115200);
  uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 2000) {}
  // servos are attached only once the user enables the arm, so they do not twitch on USB power
  Serial.println(F("READY arm_v2 proto=1"));
}

void loop() {
  readSerial();
  runHoming();
  runProfile();
  uint32_t now = micros();
  if (servoTick.due(now) && enabled) {
    if (!wrist.attached()) { wrist.attach(WRIST_PIN); grip.attach(GRIP_PIN); }
    updateServos();
  }
  if (streaming && teleTick.due(now)) {
    Serial.print(F("DATA yaw=")); Serial.print(jointDeg(0), 2); Serial.print(F(" th1=")); Serial.print(jointDeg(1), 2);
    Serial.print(F(" th2=")); Serial.println(jointDeg(2), 2);
  }
}
