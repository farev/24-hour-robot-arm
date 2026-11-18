"""Read title, price, availability and seller from Amazon US product pages (and search results).
usage: python -I research/amazon_prices.py  -> research/amazon_prices.json
Pages are parsed as text only; nothing downloaded is executed.
"""
import html
import json
import re
import sys
import time
import urllib.request as u
from pathlib import Path

H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
     "Accept-Language": "en-US,en;q=0.9", "Accept": "text/html,application/xhtml+xml"}
OUT = Path(__file__).with_name("amazon_prices.json")
ASINS = {
    "f624zz": ["B09HPHW3PP", "B0FNR2MMX8", "B08LKTRKPX", "B0DBH1YKF8", "B09NTQMKSJ"],
    "gt2-belt-320": ["B0DR35HQX1", "B0G2GLVF8Y"],
    "gt2-belt-200": ["B014R38TC6"],
    "gt2-20t-pulley": ["B078Z6YZCY", "B0DJQBZ6R1"],
    "mg996r-servo": ["B0DCK462XZ", "B0BZ4LVH4J"],
    "xl4015-buck": ["B0D1G4C28P", "B089GNFF5K"],
    "kw12-3-switch": ["B07X142VGC"],
    "m3-m4-kit": ["B0CKYTQZKB", "B08HHZHXTP"],
    "m4x70-shcs": ["B01H25KBRM", "B01BDPH2FG"],
    "m4x60-shcs": ["B00C1GJD2C", "B01H25K7VW"],
    "stepper-cable": ["B09928BXK3", "B0D4VNRQNB"],
    "dc-inline-switch": ["B0FY6XD73N", "B07J2FC2X7"],
    "dupont-jumpers": ["B07GCZ52WF"],
}
SEARCHES = {"servo-extension": "servo extension cable 500mm male female"}


def get(url):
    return u.urlopen(u.Request(url, headers=H), timeout=30).read().decode("utf-8", "ignore")


def text(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def product(asin):
    b = get(f"https://www.amazon.com/dp/{asin}")
    if "captcha" in b.lower() and "productTitle" not in b:
        return {"asin": asin, "error": "captcha"}
    title = re.search(r'id="productTitle"[^>]*>(.*?)</span>', b, re.S)
    core = re.search(r'id="corePrice(?:Display_desktop)?_feature_div".*?a-offscreen">\$([0-9.,]+)<', b, re.S)
    price = core.group(1) if core else (re.findall(r'a-offscreen">\$([0-9.,]+)<', b) or [None])[0]
    avail = re.search(r'id="availability"[^>]*>(.*?)</div>', b, re.S)
    ships = re.search(r'offer-display-feature-text-message">(.*?)</span>', b, re.S)
    sold = re.findall(r'offer-display-feature-text-message">(.*?)</span>', b, re.S)
    variant = re.search(r'id="variation_size_name".*?selection">(.*?)</span>', b, re.S)
    return {"asin": asin, "url": f"https://www.amazon.com/dp/{asin}", "title": text(title.group(1)) if title else None,
            "price_usd": float(price.replace(",", "")) if price else None,
            "availability": text(avail.group(1))[:80] if avail else None,
            "ships_sold": [text(x) for x in sold[:2]], "variant": text(variant.group(1)) if variant else None}


def search(q):
    b = get("https://www.amazon.com/s?k=" + q.replace(" ", "+"))
    res = []
    for m in re.finditer(r'data-asin="(B0[A-Z0-9]{8})".*?<h2[^>]*>(.*?)</h2>.*?a-offscreen">\$([0-9.]+)<', b, re.S):
        res.append({"asin": m.group(1), "title": text(m.group(2))[:120], "price_usd": float(m.group(3))})
        if len(res) >= 6:
            break
    return res


data = {"checked": time.strftime("%Y-%m-%d"), "items": {}, "searches": {}}
for slug, asins in ASINS.items():
    data["items"][slug] = []
    for a in asins:
        try:
            data["items"][slug].append(product(a))
        except Exception as e:  # noqa: BLE001
            data["items"][slug].append({"asin": a, "error": str(e)[:80]})
        time.sleep(1.5)
for slug, q in SEARCHES.items():
    try:
        data["searches"][slug] = search(q)
    except Exception as e:  # noqa: BLE001
        data["searches"][slug] = [{"error": str(e)[:80]}]
OUT.write_text(json.dumps(data, indent=1))
for slug, rows in data["items"].items():
    for r in rows:
        print(slug, "|", r.get("asin"), "|", r.get("price_usd"), "|", (r.get("availability") or r.get("error") or "")[:40],
              "|", (r.get("variant") or "")[:30], "|", (r.get("title") or "")[:70], "|", r.get("ships_sold"))
for slug, rows in data["searches"].items():
    for r in rows:
        print("SEARCH", slug, "|", r)
