/* motor_test - drive ONE motor of the v4 arm at a time from the serial console or the Motor test window.
 *
 * Pick an axis (yaw, shoulder, elbow, wrist), enable, and jog it in joint degrees (through the belt ratio) or raw
 * steps, at a chosen speed with trapezoid acceleration. The gripper servo can be set by pulse width. Nothing moves
 * until ENABLE 1, every move is relative and capped (no homing needed), and STOP / ENABLE 0 end any move at once.
 * Based on firmware/examples/stepper_accel; pins and ratios from firmware/arm_v4 (design/v4/geometry.py).
 *
 * Note: the CNC Shield's EN pin (D8) is shared, so ENABLE 1 powers all four drivers (the other motors hold still,
 * they do not move). Vref, microstep jumpers and the A-axis jumpers must be set first (docs/bring-up.md).
 *
 * Commands (115200 baud, one per line, case-insensitive):
 *   PING | STATUS | AXES | STREAM 0|1
 *   AXIS <yaw|shoulder|elbow|wrist|X|Y|Z|A>   select the motor (only while stopped)
 *   ENABLE 0|1                                 drivers off / on (all four, shared EN)
 *   JOG <deg>          relative move of the selected joint, degrees at the joint (|deg| <= 180)
 *   MJOG <deg>         relative move in MOTOR shaft degrees (|deg| <= 720), for a motor not yet on the arm
 *   STEPS <n>          relative move in raw steps (|n| <= 20000)
 *   SPEED <deg/s> | ACCEL <deg/s^2>             joint units; capped so the step rate stays <= MAX_STEP_HZ
 *   STOP | ZERO | INVERT 0|1 (selected axis)
 *   SERVO <us> | SERVO 0                        gripper servo pulse 900-2100 us on A3; 0 detaches it
 * Replies: OK ... / ERR <CODE> ...; DONE MOVE when a move ends; DATA k=v telemetry at 10 Hz with STREAM 1, sent only
 * while stopped (printing during a move would stall the step pulses).
 */
// mechy-lib: arduino-libraries/Servo
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
#include <string.h>
#include <stdlib.h>
#include <Servo.h>
#include "mechy_control.h"

struct Axis {
  const char *name;
  char socket;
  uint8_t stepPin, dirPin;
  float ratio;       // joint turns per motor turn = 1 / ratio (belt reduction, design/v4/geometry.py)
  float micro;       // microstep jumpers (firmware/arm_v4 MICRO)
  bool invert;
};
#define SHOULDER_PULLEY_T 20   // 20 as built, 16 after the torque upgrade (17.5:1); must match firmware/arm_v4
Axis AX[] = {
  {"yaw", 'Z', 4, 7, 6.0f, 16, false},
  {"shoulder", 'Y', 3, 6, (72.0f / SHOULDER_PULLEY_T) * (140.0f / 36.0f), 8, false},
  {"elbow", 'X', 2, 5, 7.0f, 16, false},
  {"wrist", 'A', 12, 13, 3.0f, 16, false},
};
const uint8_t NAX = 4;
const uint8_t EN_PIN = 8, YAW_SW_PIN = 11, GRIP_PIN = A3;
const float MAX_STEP_HZ = 4000.0f;   // estimate: one axis stepped from loop() on an Uno, with margin
const float JOG_MAX = 180.0f, MJOG_MAX = 720.0f;
const long STEPS_MAX = 20000;
const int SERVO_MIN = 900, SERVO_MAX = 2100;   // MG996R safe pulse range; the gripper uses ~1250-1920

uint8_t sel = 0;
float vMax = 15.0f, aMax = 40.0f;    // joint deg/s, deg/s^2 (gentle defaults)
long stepPos[NAX] = {0, 0, 0, 0};
long startSteps = 0, deltaSteps = 0;
bool enabled = false, moving = false, streaming = false;
mc::Trapezoid prof;
uint32_t moveStartUs = 0;
mc::FixedRate teleTick(100000);
Servo grip;
int servoUs = 0;

float stepsPerJointDeg(uint8_t i) { return 200.0f * AX[i].micro * AX[i].ratio / 360.0f; }
float stepsPerMotorDeg(uint8_t i) { return 200.0f * AX[i].micro / 360.0f; }
float jointDeg(uint8_t i) { return stepPos[i] / stepsPerJointDeg(i); }
float vCap(uint8_t i) { return MAX_STEP_HZ / stepsPerJointDeg(i); }   // joint deg/s the step rate allows
bool yawSwitch() { return digitalRead(YAW_SW_PIN) == LOW; }

void stepOnce(int dir) {
  Axis &a = AX[sel];
  digitalWrite(a.dirPin, (dir > 0) != a.invert ? HIGH : LOW);
  digitalWrite(a.stepPin, HIGH);
  delayMicroseconds(2);   // A4988 needs >= 1 us high
  digitalWrite(a.stepPin, LOW);
  stepPos[sel] += dir;
}

void setEnabled(bool on) {
  enabled = on;
  digitalWrite(EN_PIN, on ? LOW : HIGH);   // active low
  if (!on) moving = false;
}

/* Relative move of `steps` on the selected axis; the profile runs in steps with the joint limits converted. */
void startSteps_(long steps) {
  float spd = stepsPerJointDeg(sel);
  float v = mc::clampf(vMax, 0.1f, vCap(sel)) * spd, a = aMax * spd;
  startSteps = stepPos[sel];
  deltaSteps = steps;
  prof.plan(0.0f, (float)labs(steps), v, a);
  moveStartUs = micros();
  moving = steps != 0;
  Serial.print(F("OK MOVE axis=")); Serial.print(AX[sel].name);
  Serial.print(F(" steps=")); Serial.print(steps);
  Serial.print(F(" T=")); Serial.println(prof.duration, 2);
  if (!moving) Serial.println(F("DONE MOVE"));
}

void runProfile() {
  if (!moving) return;
  float t = (micros() - moveStartUs) * 1e-6f;
  long done = lround(prof.position(t));
  long want = startSteps + (deltaSteps >= 0 ? done : -done);
  int budget = 4;
  while (stepPos[sel] != want && budget--) stepOnce(want > stepPos[sel] ? 1 : -1);
  if (t >= prof.duration && stepPos[sel] == startSteps + deltaSteps) {
    moving = false;
    Serial.println(F("DONE MOVE"));
  }
}

void printStatus(bool data) {
  Serial.print(data ? F("DATA ") : F("OK STATUS "));
  Serial.print(F("axis=")); Serial.print(AX[sel].name);
  Serial.print(F(" socket=")); Serial.print(AX[sel].socket);
  Serial.print(F(" deg=")); Serial.print(jointDeg(sel), 2);
  Serial.print(F(" steps=")); Serial.print(stepPos[sel]);
  Serial.print(F(" en=")); Serial.print(enabled);
  Serial.print(F(" moving=")); Serial.print(moving);
  Serial.print(F(" speed=")); Serial.print(vMax, 1);
  Serial.print(F(" inv=")); Serial.print(AX[sel].invert);
  Serial.print(F(" yaw_sw=")); Serial.print(yawSwitch());
  Serial.print(F(" servo=")); Serial.println(servoUs);
}

int axisIndex(const char *s) {
  for (uint8_t i = 0; i < NAX; i++) {
    if (!strcasecmp(s, AX[i].name)) return i;
    if (strlen(s) == 1 && (s[0] == AX[i].socket || s[0] == AX[i].socket + 32)) return i;
  }
  return -1;
}

void handleLine(char *line) {
  char *name = strtok(line, " \t");
  if (!name) return;
  for (char *p = name; *p; p++) if (*p >= 'a' && *p <= 'z') *p -= 32;
  char *arg = strtok(NULL, " \t");
  float x = arg ? atof(arg) : 0;
  if (!strcmp(name, "PING")) Serial.println(F("OK PONG"));
  else if (!strcmp(name, "STATUS")) printStatus(false);
  else if (!strcmp(name, "STREAM") && arg) { streaming = atoi(arg) != 0; Serial.println(F("OK STREAM")); }
  else if (!strcmp(name, "AXES")) {
    Serial.print(F("OK AXES"));
    for (uint8_t i = 0; i < NAX; i++) {
      Serial.print(' '); Serial.print(AX[i].name); Serial.print(':'); Serial.print(AX[i].socket);
      Serial.print(':'); Serial.print(AX[i].ratio, 0); Serial.print(':'); Serial.print((int)AX[i].micro);
      Serial.print(':'); Serial.print(vCap(i), 0);
    }
    Serial.println();
  } else if (!strcmp(name, "AXIS") && arg) {
    if (moving) { Serial.println(F("ERR BUSY")); return; }
    int i = axisIndex(arg);
    if (i < 0) { Serial.println(F("ERR AXIS use yaw|shoulder|elbow|wrist")); return; }
    sel = i; vMax = mc::clampf(vMax, 0.1f, vCap(sel));
    Serial.print(F("OK AXIS ")); Serial.println(AX[sel].name);
  } else if (!strcmp(name, "ENABLE") && arg) {
    setEnabled(atoi(arg) != 0);
    Serial.print(F("OK ENABLE ")); Serial.println(enabled);
  } else if (!strcmp(name, "STOP")) { moving = false; Serial.println(F("OK STOP")); }
  else if (!strcmp(name, "ZERO")) {
    if (moving) { Serial.println(F("ERR BUSY")); return; }
    stepPos[sel] = 0; Serial.println(F("OK ZERO"));
  } else if (!strcmp(name, "INVERT") && arg) {
    if (moving) { Serial.println(F("ERR BUSY")); return; }
    AX[sel].invert = atoi(arg) != 0; Serial.print(F("OK INVERT ")); Serial.println(AX[sel].invert);
  } else if (!strcmp(name, "SPEED") && x > 0) {
    vMax = mc::clampf(x, 0.1f, vCap(sel)); Serial.print(F("OK SPEED ")); Serial.println(vMax, 1);
  } else if (!strcmp(name, "ACCEL") && x > 0) {
    aMax = mc::clampf(x, 1.0f, 500.0f); Serial.print(F("OK ACCEL ")); Serial.println(aMax, 1);
  } else if (!strcmp(name, "JOG") || !strcmp(name, "MJOG") || !strcmp(name, "STEPS")) {
    if (!arg) { Serial.println(F("ERR ARG")); return; }
    if (!enabled) { Serial.println(F("ERR DISABLED send ENABLE 1")); return; }
    if (moving) { Serial.println(F("ERR BUSY")); return; }
    long steps;
    if (!strcmp(name, "JOG")) {
      if (fabs(x) > JOG_MAX) { Serial.println(F("ERR LIMIT |deg| <= 180")); return; }
      steps = lround(x * stepsPerJointDeg(sel));
    } else if (!strcmp(name, "MJOG")) {
      if (fabs(x) > MJOG_MAX) { Serial.println(F("ERR LIMIT |deg| <= 720")); return; }
      steps = lround(x * stepsPerMotorDeg(sel));
    } else {
      steps = atol(arg);
      if (labs(steps) > STEPS_MAX) { Serial.println(F("ERR LIMIT |steps| <= 20000")); return; }
    }
    startSteps_(steps);
  } else if (!strcmp(name, "SERVO") && arg) {
    int us = atoi(arg);
    if (us == 0) { grip.detach(); servoUs = 0; Serial.println(F("OK SERVO off")); return; }
    if (us < SERVO_MIN || us > SERVO_MAX) { Serial.println(F("ERR LIMIT 900-2100 us")); return; }
    if (!grip.attached()) grip.attach(GRIP_PIN);
    grip.writeMicroseconds(us); servoUs = us;
    Serial.print(F("OK SERVO ")); Serial.println(us);
  } else { Serial.print(F("ERR UNKNOWN ")); Serial.println(name); }
}

void readSerial() {
  static char buf[40];
  static uint8_t len = 0;
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') { buf[len] = '\0'; if (len) handleLine(buf); len = 0; }
    else if (len < sizeof(buf) - 1) buf[len++] = c;
  }
}

void setup() {
  for (uint8_t i = 0; i < NAX; i++) { pinMode(AX[i].stepPin, OUTPUT); pinMode(AX[i].dirPin, OUTPUT); }
  pinMode(EN_PIN, OUTPUT);
  pinMode(YAW_SW_PIN, INPUT_PULLUP);
  setEnabled(false);   // boot safe: drivers off, servo detached
  Serial.begin(115200);
  uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 2000) {}
  Serial.println(F("READY motor_test proto=1"));
}

void loop() {
  readSerial();
  bool wasMoving = moving;
  runProfile();
  // Telemetry only while stopped: a ~110-char DATA line overfills the 64-byte TX buffer, and Serial.print then blocks
  // for several ms, which leaves gaps in the step pulses (uneven, rough-sounding motion). One line when a move ends.
  if (streaming && ((!moving && teleTick.due(micros())) || (wasMoving && !moving))) printStatus(true);
}
