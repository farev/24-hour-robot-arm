"""Find M3 (+ M4) socket-head screw + nut kits on Amazon that cover the v4 screw list in one box.
usage: python -I research/screw_kit_options.py   -> research/screw_kit_options.json
Needed (docs/screw-list.md): M3 x6 4, x8 14, x10 12, x16 8, x20 4, x30 3; M4 x30 2; M3 nuts 11, M4 nuts 5.
"""
import html
import json
import re
import time
import urllib.request as u
from pathlib import Path

H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
     "Accept-Language": "en-US,en;q=0.9"}
import sys
OUT = Path(__file__).with_name(sys.argv[1] if len(sys.argv) > 1 else "screw_kit_options.json")
QUERIES = sys.argv[2].split("|") if len(sys.argv) > 2 else ["M3 M4 socket head cap screw assortment kit nuts", "M3 M4 M5 socket head screw assortment kit nuts",
           "M3 socket head cap screws assortment 6mm 8mm 10mm 16mm 20mm 30mm nuts",
           "metric socket head cap screw kit M2 M3 M4 M5 nuts washers", "M3 M4 hex socket screws bolts nuts set 3D printer"]
txt = lambda s: html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def get(url):
    return u.urlopen(u.Request(url, headers=H), timeout=30).read().decode("utf-8", "ignore")


asins = []
for q in QUERIES:
    try:
        b = get("https://www.amazon.com/s?k=" + q.replace(" ", "+"))
    except Exception as e:  # noqa: BLE001
        print("search failed", q, e)
        continue
    for a in re.findall(r'data-asin="(B0[A-Z0-9]{8})"', b):
        if a not in asins:
            asins.append(a)
    time.sleep(1.5)
print(len(asins), "listings")
rows = []
for a in asins[:60]:
    try:
        b = get(f"https://www.amazon.com/dp/{a}")
    except Exception:  # noqa: BLE001
        continue
    t = re.search(r'id="productTitle"[^>]*>(.*?)</span>', b, re.S)
    title = txt(t.group(1)) if t else ""
    if not re.search(sys.argv[3] if len(sys.argv) > 3 else r"M3", title) or not re.search(r"socket|cap|hex", title, re.I):
        continue
    fb = re.search(r'id="feature-bullets"(.*?)</ul>', b, re.S)
    bullets = txt(fb.group(1)) if fb else ""
    core = re.search(r'id="corePrice(?:Display_desktop)?_feature_div".*?a-offscreen">\$([0-9.,]+)<', b, re.S)
    av = re.search(r'id="availability"[^>]*>(.*?)</div>', b, re.S)
    msgs = [txt(x) for x in re.findall(r'offer-display-feature-text-message">(.*?)</span>', b, re.S)[:2]]
    deliv = re.findall(r'data-csa-c-delivery-time="([^"]+)"', b)[:2]
    blob = title + " " + bullets
    rows.append({"asin": a, "url": f"https://www.amazon.com/dp/{a}", "title": title[:200],
                 "price_usd": float(core.group(1).replace(",", "")) if core else None,
                 "availability": txt(av.group(1))[:60] if av else None, "ships_sold": msgs, "delivery": deliv,
                 "has_m4": bool(re.search(r"M4", blob)), "has_nuts": bool(re.search(r"\bnuts?\b", blob, re.I)),
                 "has_30": bool(re.search(r"30\s*mm", blob)), "bullets": bullets[:900]})
    time.sleep(1.2)
OUT.write_text(json.dumps(rows, indent=1))
for r in sorted(rows, key=lambda r: (r["ships_sold"][:1] != ["Amazon"], not (r["has_m4"] and r["has_nuts"] and r["has_30"]),
                                     r["price_usd"] or 99)):
    print(f'{r["asin"]} ${r["price_usd"]} M4={r["has_m4"]} nuts={r["has_nuts"]} 30mm={r["has_30"]} | {r["ships_sold"]} | '
          f'{r["availability"]} | {r["delivery"]} | {r["title"][:90]}')
