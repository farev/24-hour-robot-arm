"""Serial bridge for the Motor test window: connects to the Arduino running firmware/motor_test and lets the window
(windows/motor-test) talk to it over http://127.0.0.1:8765. Only this computer can reach it.

Run it yourself (it moves real hardware):   python3 tools/mpy.py tools/motor_bridge.py [--port /dev/cu.usbmodemXXXX]
Stop it with Ctrl-C (or SIGTERM): it sends STOP and ENABLE 0 before closing the port.

Safety: if the window stops polling for 3 s (closed, crashed, laptop asleep) while the drivers are enabled, the bridge
sends STOP and ENABLE 0 on its own.

Endpoints (JSON): GET /status, GET /ports, POST /connect {port?}, POST /disconnect, POST /send {line},
GET /lines?since=<n>.
"""
from __future__ import annotations

import argparse
import json
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import serial
import serial.tools.list_ports

HOST, PORT = "127.0.0.1", 8765
DEADMAN_S = 3.0


class Board:
    def __init__(self):
        self.ser = None
        self.port = None
        self.banner = ""
        self.lines: list[str] = []          # every line from the board, numbered by index
        self.lock = threading.Lock()
        self.cmd_lock = threading.Lock()
        self.last_poll = time.monotonic()
        self.enabled = False

    # ---- port
    @staticmethod
    def ports():
        out = []
        for p in serial.tools.list_ports.comports():
            likely = any(k in (p.device + " " + (p.description or "")).lower()
                         for k in ("usbmodem", "usbserial", "wchusb", "arduino", "ch340", "ttyacm", "ttyusb"))
            out.append({"device": p.device, "description": p.description or "", "likely": likely})
        return sorted(out, key=lambda p: not p["likely"])

    def connect(self, port: str | None):
        self.disconnect()
        if not port:
            likely = [p["device"] for p in self.ports() if p["likely"]]
            if not likely:
                raise RuntimeError("no Arduino found on USB: plug it in (data cable) and try again")
            port = likely[0]
        self.ser = serial.Serial(port, 115200, timeout=0.1)
        self.port = port
        self.banner = ""
        threading.Thread(target=self._reader, daemon=True).start()
        end = time.monotonic() + 4.0                  # opening the port resets an Uno: wait for its banner
        while time.monotonic() < end and not self.banner:
            time.sleep(0.05)
        if not self.banner:
            self._write("PING")                       # banner missed (board did not reset): check it answers
        return {"port": port, "banner": self.banner}

    def disconnect(self):
        if self.ser:
            try:
                self._write("STOP")
                self._write("ENABLE 0")
                self.ser.flush()
                time.sleep(0.1)
            finally:
                try:
                    self.ser.close()
                except Exception:   # noqa: BLE001
                    pass
        self.ser, self.port, self.enabled = None, None, False

    # ---- io
    def _reader(self):
        ser = self.ser
        while ser is not None and ser is self.ser and ser.is_open:
            try:
                raw = ser.readline()
            except Exception:   # noqa: BLE001  (unplugged, or closed by disconnect)
                if ser is self.ser:                   # a reconnect already replaced this port: leave the new one alone
                    self._add("ERR BRIDGE serial port lost")
                    self.ser = None
                return
            if raw:
                self._add(raw.decode("utf-8", "replace").strip())

    def _add(self, line: str):
        if not line:
            return
        with self.lock:
            self.lines.append(line)
            if len(self.lines) > 5000:
                self.lines = self.lines[-4000:]
        if line.startswith("READY"):
            self.banner = line
        if line.startswith("OK ENABLE"):
            self.enabled = line.endswith("1")

    def _write(self, line: str):
        if self.ser:
            self.ser.write((line.strip() + "\n").encode())

    def send(self, line: str, timeout: float = 1.5):
        if not self.ser:
            raise RuntimeError("not connected")
        with self.cmd_lock:
            with self.lock:
                start = len(self.lines)
            self._write(line)
            end = time.monotonic() + timeout
            while time.monotonic() < end:
                with self.lock:
                    new = self.lines[start:]
                for ln in new:
                    if ln.startswith(("OK", "ERR")):
                        return ln
                time.sleep(0.01)
        return "ERR TIMEOUT no reply from the board"

    def since(self, n: int):
        with self.lock:
            total = len(self.lines)
            n = max(0, min(n, total))
            return total, self.lines[n:][-400:]

    # ---- dead-man: the window must keep polling while the drivers are on
    def watchdog(self):
        while True:
            time.sleep(0.5)
            if self.ser and self.enabled and time.monotonic() - self.last_poll > DEADMAN_S:
                self._add("ERR BRIDGE window stopped polling: STOP + ENABLE 0 sent")
                self._write("STOP")
                self._write("ENABLE 0")
                self.enabled = False


BOARD = Board()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):   # keep the terminal quiet
        pass

    def _send(self, code: int, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204, {})

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/status":
            self._send(200, {"connected": bool(BOARD.ser), "port": BOARD.port, "banner": BOARD.banner,
                             "enabled": BOARD.enabled})
        elif u.path == "/ports":
            self._send(200, {"ports": BOARD.ports()})
        elif u.path == "/lines":
            BOARD.last_poll = time.monotonic()
            n = int(parse_qs(u.query).get("since", ["0"])[0])
            total, lines = BOARD.since(n)
            self._send(200, {"next": total, "lines": lines, "connected": bool(BOARD.ser), "enabled": BOARD.enabled})
        else:
            self._send(404, {"error": "unknown path"})

    def do_POST(self):
        u = urlparse(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            body = {}
        try:
            if u.path == "/connect":
                self._send(200, BOARD.connect(body.get("port")))
            elif u.path == "/disconnect":
                BOARD.disconnect()
                self._send(200, {"ok": True})
            elif u.path == "/send":
                BOARD.last_poll = time.monotonic()
                self._send(200, {"reply": BOARD.send(str(body.get("line", "")))})
            else:
                self._send(404, {"error": "unknown path"})
        except Exception as e:   # noqa: BLE001
            self._send(400, {"error": str(e)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=None, help="serial port (default: first Arduino-looking port)")
    args = ap.parse_args()
    threading.Thread(target=BOARD.watchdog, daemon=True).start()
    if args.port:
        print("connected:", BOARD.connect(args.port))
    srv = ThreadingHTTPServer((HOST, PORT), Handler)

    def stop(*_):    # Mechy and the app end it with SIGTERM: disable the drivers then too, as Ctrl-C does
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGHUP, stop)
    print(f"motor bridge on http://{HOST}:{PORT} - open the Motor test window. Ctrl-C to stop (drivers off).")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        BOARD.disconnect()
        srv.server_close()
        print("stopped: STOP + ENABLE 0 sent, port closed")


if __name__ == "__main__":
    main()
