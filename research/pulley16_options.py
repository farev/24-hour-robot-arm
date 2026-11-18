"""Amazon listings for a GT2 16-tooth pulley, 5 mm bore, 6 mm belt (shoulder motor upgrade, 2026-11-16).
usage: python -I research/pulley16_options.py   -> research/pulley16_options.json
"""
import html
import json
import re
import time
import urllib.request as u
from pathlib import Path

H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
     "Accept-Language": "en-US,en;q=0.9"}
txt = lambda s: html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()
get = lambda url: u.urlopen(u.Request(url, headers=H), timeout=30).read().decode("utf-8", "ignore")
asins = []
for q in ["GT2 16 teeth pulley 5mm bore 6mm belt", "GT2 16T timing pulley 5mm bore", "16 tooth GT2 pulley 5mm"]:
    try:
        for a in re.findall(r'data-asin="(B0[A-Z0-9]{8})"', get("https://www.amazon.com/s?k=" + q.replace(" ", "+"))):
            if a not in asins:
                asins.append(a)
    except Exception as e:  # noqa: BLE001
        print("search failed", q, e)
    time.sleep(1.5)
rows = []
for a in asins[:30]:
    try:
        b = get(f"https://www.amazon.com/dp/{a}")
    except Exception:  # noqa: BLE001
        continue
    t = re.search(r'id="productTitle"[^>]*>(.*?)</span>', b, re.S)
    title = txt(t.group(1)) if t else ""
    if not (re.search(r"GT2|2GT", title, re.I) and re.search(r"\b16\s*(T|teeth|tooth)", title, re.I)
            and re.search(r"5\s*mm", title, re.I)):
        continue
    core = re.search(r'id="corePrice(?:Display_desktop)?_feature_div".*?a-offscreen">\$([0-9.,]+)<', b, re.S)
    av = re.search(r'id="availability"[^>]*>(.*?)</div>', b, re.S)
    msgs = [txt(x) for x in re.findall(r'offer-display-feature-text-message">(.*?)</span>', b, re.S)[:2]]
    rows.append({"asin": a, "url": f"https://www.amazon.com/dp/{a}", "title": title[:150],
                 "price_usd": float(core.group(1).replace(",", "")) if core else None,
                 "availability": txt(av.group(1))[:50] if av else None, "ships_sold": msgs,
                 "delivery": re.findall(r'data-csa-c-delivery-time="([^"]+)"', b)[:2]})
    time.sleep(1.2)
Path(__file__).with_name("pulley16_options.json").write_text(json.dumps(rows, indent=1))
for r in sorted(rows, key=lambda r: (r["ships_sold"][:1] != ["Amazon"], r["price_usd"] or 99)):
    print(r["asin"], r["price_usd"], r["ships_sold"], r["availability"], r["delivery"], "|", r["title"][:90])
