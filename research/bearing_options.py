"""Read each candidate bearing listing: title, price, pack size, seller / ships-from, delivery estimate.
Keeps only 4 x 13 x 5 mm bearings (F624 / 624). usage: python -I research/bearing_options.py
Input: research/store_raw/bearing_asins.json. Output: research/bearing_options.json (text parsing only).
"""
import html
import json
import re
import time
import urllib.request as u
from pathlib import Path

H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
     "Accept-Language": "en-US,en;q=0.9"}
HERE = Path(__file__).parent
asins = list(json.loads((HERE / "store_raw/bearing_asins.json").read_text()))
txt = lambda s: html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()
rows = []
for a in asins:
    try:
        b = u.urlopen(u.Request(f"https://www.amazon.com/dp/{a}", headers=H), timeout=30).read().decode("utf-8", "ignore")
    except Exception as e:  # noqa: BLE001
        rows.append({"asin": a, "error": str(e)[:60]}); continue
    t = re.search(r'id="productTitle"[^>]*>(.*?)</span>', b, re.S)
    title = txt(t.group(1)) if t else ""
    if not re.search(r"\b(F?624|4\s*[x*]\s*13\s*[x*]\s*5)", title, re.I):
        continue
    core = re.search(r'id="corePrice(?:Display_desktop)?_feature_div".*?a-offscreen">\$([0-9.,]+)<', b, re.S)
    av = re.search(r'id="availability"[^>]*>(.*?)</div>', b, re.S)
    msgs = [txt(x) for x in re.findall(r'offer-display-feature-text-message">(.*?)</span>', b, re.S)[:2]]
    deliv = re.search(r'data-csa-c-delivery-time="([^"]+)"', b) or re.search(r'id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE".*?<span[^>]*>(.*?)</span>', b, re.S)
    fastest = re.search(r'data-csa-c-delivery-time="[^"]+".*?data-csa-c-delivery-time="([^"]+)"', b, re.S)
    pack = re.search(r"(\d+)\s*(?:pcs|pc|pieces|pack|-pack|Pack)", title, re.I)
    rows.append({"asin": a, "url": f"https://www.amazon.com/dp/{a}", "title": title[:120],
                 "price_usd": float(core.group(1).replace(",", "")) if core else None,
                 "pack": int(pack.group(1)) if pack else None,
                 "availability": txt(av.group(1))[:60] if av else ("out of stock" if 'id="outOfStock"' in b else None),
                 "ships_from_sold_by": msgs, "delivery": txt(deliv.group(1)) if deliv else None,
                 "prime": ("isPrimeExclusive" in b or "a-icon-prime" in b) and msgs[:1] == ["Amazon"],
                 "flanged": bool(re.search(r"\bF624|flange", title, re.I))})
    time.sleep(1.2)
(HERE / "bearing_options.json").write_text(json.dumps(rows, indent=1))
for r in sorted([r for r in rows if r.get("price_usd")], key=lambda r: (r["ships_from_sold_by"][:1] != ["Amazon"], r["price_usd"])):
    per = r["price_usd"] / r["pack"] if r.get("pack") else None
    print(f'{r["asin"]} ${r["price_usd"]:>6} pack {r["pack"]} ({"$%.2f/ea" % per if per else "?"}) flanged={r["flanged"]} '
          f'| {r["ships_from_sold_by"]} | {r["availability"]} | {r["delivery"]} | {r["title"][:70]}')
