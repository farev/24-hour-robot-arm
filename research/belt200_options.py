"""Find GT2 6 mm closed belts 196-204 mm on Amazon that arrive soon (the 200 mm BEMONOC pack is too slow).
usage: python -I research/belt200_options.py   -> research/belt200_options.json
Search pages give ASINs; each product page gives title, price, seller and the delivery dates.
"""
import html
import json
import re
import time
import urllib.request as u
from pathlib import Path

H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
     "Accept-Language": "en-US,en;q=0.9"}
OUT = Path(__file__).with_name("belt200_options.json")
QUERIES = ["GT2 200mm closed loop timing belt 6mm", "GT2 timing belt 200mm 6mm width closed",
           "GT2 202mm closed timing belt 6mm", "GT2 198mm closed loop belt 6mm",
           "GT2 closed loop belt 200-2GT-6", "GT2 belt 196mm closed 6mm", "GT2 204mm closed belt 6mm",
           "GT2 closed loop belt assortment 6mm 200mm"]
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
for a in asins[:70]:
    try:
        b = get(f"https://www.amazon.com/dp/{a}")
    except Exception as e:  # noqa: BLE001
        continue
    t = re.search(r'id="productTitle"[^>]*>(.*?)</span>', b, re.S)
    title = txt(t.group(1)) if t else ""
    lens = [int(x) for x in re.findall(r"\b(19[6-9]|20[0-4])\s*mm", title, re.I)]
    if not (re.search(r"GT2|2GT", title, re.I) and re.search(r"close|loop|endless|ring", title, re.I) and lens):
        continue
    if re.search(r"\b(9|10|15)\s*mm\s*wid", title, re.I) and not re.search(r"6\s*mm", title, re.I):
        continue
    core = re.search(r'id="corePrice(?:Display_desktop)?_feature_div".*?a-offscreen">\$([0-9.,]+)<', b, re.S)
    av = re.search(r'id="availability"[^>]*>(.*?)</div>', b, re.S)
    msgs = [txt(x) for x in re.findall(r'offer-display-feature-text-message">(.*?)</span>', b, re.S)[:2]]
    deliv = re.findall(r'data-csa-c-delivery-time="([^"]+)"', b)
    var = re.search(r'id="variation_size_name".*?selection">(.*?)</span>', b, re.S)
    rows.append({"asin": a, "url": f"https://www.amazon.com/dp/{a}", "title": title[:150], "lengths_mm": sorted(set(lens)),
                 "variant": txt(var.group(1)) if var else None,
                 "price_usd": float(core.group(1).replace(",", "")) if core else None,
                 "availability": txt(av.group(1))[:60] if av else None, "ships_sold": msgs,
                 "delivery": deliv[:2]})
    time.sleep(1.2)
OUT.write_text(json.dumps(rows, indent=1))
for r in sorted(rows, key=lambda r: (r["ships_sold"][:1] != ["Amazon"], r["price_usd"] or 99)):
    print(f'{r["asin"]} ${r["price_usd"]} {r["lengths_mm"]} var={r["variant"]} | {r["ships_sold"]} | {r["availability"]} | '
          f'{r["delivery"]} | {r["title"][:80]}')
