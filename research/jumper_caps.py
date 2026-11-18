"""Find 2.54 mm jumper caps (shunts) on Amazon US: search, then read price, stock, seller and delivery for the top hits.
usage: python -I research/jumper_caps.py  -> research/jumper_caps.json
Pages are parsed as text only; nothing downloaded is executed.
"""
import html
import json
import re
import time
import urllib.request as u
from pathlib import Path

H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
     "Accept-Language": "en-US,en;q=0.9", "Accept": "text/html,application/xhtml+xml"}
OUT = Path(__file__).with_name("jumper_caps.json")
QUERIES = ["2.54mm jumper caps", "jumper shunt 2.54mm 100 pcs"]


def get(url):
    return u.urlopen(u.Request(url, headers=H), timeout=30).read().decode("utf-8", "ignore")


def text(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def search(q):
    b = get("https://www.amazon.com/s?k=" + q.replace(" ", "+"))
    res = []
    for m in re.finditer(r'data-asin="(B0[A-Z0-9]{8})".*?<h2[^>]*>(.*?)</h2>.*?a-offscreen">\$([0-9.]+)<', b, re.S):
        res.append({"asin": m.group(1), "title": text(m.group(2))[:120], "price_usd": float(m.group(3))})
        if len(res) >= 8:
            break
    return res


def product(asin):
    b = get(f"https://www.amazon.com/dp/{asin}")
    if "captcha" in b.lower() and "productTitle" not in b:
        return {"asin": asin, "error": "captcha"}
    title = re.search(r'id="productTitle"[^>]*>(.*?)</span>', b, re.S)
    core = re.search(r'id="corePrice(?:Display_desktop)?_feature_div".*?a-offscreen">\$([0-9.,]+)<', b, re.S)
    avail = re.search(r'id="availability"[^>]*>(.*?)</div>', b, re.S)
    sold = re.findall(r'offer-display-feature-text-message">(.*?)</span>', b, re.S)
    deliv = re.findall(r'data-csa-c-delivery-time="([^"]+)"', b)
    return {"asin": asin, "url": f"https://www.amazon.com/dp/{asin}", "title": text(title.group(1))[:140] if title else None,
            "price_usd": float(core.group(1).replace(",", "")) if core else None,
            "availability": text(avail.group(1))[:80] if avail else None,
            "ships_sold": [text(x) for x in sold[:2]], "delivery": deliv[:2]}


data = {"checked": time.strftime("%Y-%m-%d"), "searches": {}, "products": []}
seen = []
for q in QUERIES:
    try:
        data["searches"][q] = search(q)
    except Exception as e:  # noqa: BLE001
        data["searches"][q] = [{"error": str(e)[:80]}]
    for r in data["searches"][q]:
        t = (r.get("title") or "").lower()
        if r.get("asin") and r["asin"] not in seen and ("jumper" in t or "shunt" in t) and "wire" not in t:
            seen.append(r["asin"])
    time.sleep(1.5)
for a in seen[:6]:
    try:
        data["products"].append(product(a))
    except Exception as e:  # noqa: BLE001
        data["products"].append({"asin": a, "error": str(e)[:80]})
    time.sleep(1.5)
OUT.write_text(json.dumps(data, indent=1))
for q, rows in data["searches"].items():
    for r in rows:
        print("S |", r.get("asin"), "|", r.get("price_usd"), "|", (r.get("title") or r.get("error") or "")[:90])
for r in data["products"]:
    print("P |", r.get("asin"), "|", r.get("price_usd"), "|", (r.get("availability") or r.get("error") or "")[:30], "|",
          r.get("ships_sold"), "|", r.get("delivery"), "|", (r.get("title") or "")[:80])
