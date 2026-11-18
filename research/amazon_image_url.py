"""Print the main product image URL (landingImage hiRes/src) of an Amazon US listing.
usage: python -I research/amazon_image_url.py <ASIN>
Pages are parsed as text only; nothing downloaded is executed.
"""
import re
import sys
import urllib.request as u

H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
     "Accept-Language": "en-US,en;q=0.9"}
b = u.urlopen(u.Request(f"https://www.amazon.com/dp/{sys.argv[1]}", headers=H), timeout=30).read().decode("utf-8", "ignore")
m = re.search(r'id="landingImage"[^>]*data-old-hires="([^"]+)"', b) or re.search(r'"hiRes":"(https://[^"]+)"', b) \
    or re.search(r'id="landingImage"[^>]*src="([^"]+)"', b)
print(m.group(1) if m else "none")
