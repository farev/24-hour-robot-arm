"""Smoke test of tools/motor_bridge.py's HTTP side with no board connected (nothing is opened or moved).
usage: python tools/mpy.py tools/test_motor_bridge.py
"""
import json
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import motor_bridge as mb  # noqa: E402

srv = ThreadingHTTPServer(("127.0.0.1", 0), mb.Handler)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{port}"


def call(path, body=None):
    req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="GET" if body is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read()), r.headers.get("Access-Control-Allow-Origin")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()), e.headers.get("Access-Control-Allow-Origin")


print("status", call("/status"))
s, j, cors = call("/ports")
print("ports", s, [p["device"] for p in j["ports"]][:4], "cors", cors)
print("lines", call("/lines?since=0"))
print("send without board", call("/send", {"line": "PING"}))
srv.shutdown()
