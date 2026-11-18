"""Print title, bullets (pack size, width, pitch), price, seller and delivery for Amazon ASINs.
usage: python -I research/asin_details.py ASIN [ASIN ...]
"""
import html
import re
import sys
import time
import urllib.request as u

H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
     "Accept-Language": "en-US,en;q=0.9"}
txt = lambda s: html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()
for a in sys.argv[1:]:
    b = u.urlopen(u.Request(f"https://www.amazon.com/dp/{a}", headers=H), timeout=30).read().decode("utf-8", "ignore")
    t = re.search(r'id="productTitle"[^>]*>(.*?)</span>', b, re.S)
    fb = re.search(r'id="feature-bullets"(.*?)</ul>', b, re.S)
    core = re.search(r'id="corePrice(?:Display_desktop)?_feature_div".*?a-offscreen">\$([0-9.,]+)<', b, re.S)
    av = re.search(r'id="availability"[^>]*>(.*?)</div>', b, re.S)
    msgs = [txt(x) for x in re.findall(r'offer-display-feature-text-message">(.*?)</span>', b, re.S)[:2]]
    deliv = re.findall(r'data-csa-c-delivery-time="([^"]+)"', b)[:2]
    print(f"== {a} ${core.group(1) if core else '?'} | {msgs} | {txt(av.group(1))[:50] if av else '?'} | {deliv}")
    print("   ", txt(t.group(1))[:200] if t else "no title")
    print("   ", (txt(fb.group(1))[:700] if fb else "no bullets"))
    time.sleep(1.2)
