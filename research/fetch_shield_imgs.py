"""Download CNC Shield V3 reference images (CMU 16-375 course page) into research/cnc_shield_ref/ for viewing only.
usage: python -I research/fetch_shield_imgs.py
"""
import urllib.request as u
from pathlib import Path

BASE = "https://courses.ideate.cmu.edu/16-375/f2024/text/_images/"
NAMES = ["CNC_shield_top_view.jpg", "Arduino-CNC-Shield-V3-Layout.jpg", "A-axis-drivers.jpg"]
OUT = Path(__file__).with_name("cnc_shield_ref")
OUT.mkdir(exist_ok=True)
for n in NAMES:
    b = u.urlopen(u.Request(BASE + n, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
    (OUT / n).write_bytes(b)
    print(n, len(b))
