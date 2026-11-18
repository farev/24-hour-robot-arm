"""Start tools/motor_bridge.py detached (its own session, output to tools/motor_bridge.log) and return at once.
Does nothing if a bridge already answers on 127.0.0.1:8765. Stop it with:  python3 tools/start_bridge.py --stop
usage: python3 tools/start_bridge.py [--stop]
"""
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENV_PY = "/Users/fabianarevalo/Documents/Mechy/engine/.venv/bin/python"
PIDFILE = HERE / "motor_bridge.pid"


def status():
    try:
        return json.loads(urllib.request.urlopen("http://127.0.0.1:8765/status", timeout=1.5).read())
    except Exception:  # noqa: BLE001
        return None


if "--stop" in sys.argv:
    if PIDFILE.exists():
        try:
            os.kill(int(PIDFILE.read_text()), signal.SIGINT)   # Ctrl-C path: STOP + ENABLE 0, close port
            print("stop signal sent")
        except (ProcessLookupError, ValueError):
            print("no bridge process with the saved pid")
        PIDFILE.unlink(missing_ok=True)
    else:
        print("no pid file; if a bridge still answers, it was started another way")
    sys.exit(0)

s = status()
if s is not None:
    print("bridge already running:", s)
    sys.exit(0)
log = open(HERE / "motor_bridge.log", "ab")
p = subprocess.Popen([VENV_PY, "-u", str(HERE / "motor_bridge.py")], stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                     start_new_session=True, cwd=str(HERE.parent))
PIDFILE.write_text(str(p.pid))
for _ in range(20):
    time.sleep(0.25)
    s = status()
    if s is not None:
        print("bridge started, pid", p.pid, s)
        break
else:
    print("bridge did not answer yet; see tools/motor_bridge.log")
