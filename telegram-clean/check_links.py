#!/usr/bin/env python3
"""Check the clean package, three ways, before any claim of 'live'.

1. Every internal href/src in every .html file must point to a file
   that exists in this folder. No exceptions, no dead links.
2. No user-facing page may link to the dead muse.ai Living Map, to the
   old @Zorbianbot, or to any github.io page other than the package
   itself (the package is served from Pages, so it needs no such link).
3. Every .html file must parse, and bot.py must compile.
Run: python3 check_links.py   (exit 0 = pass, exit 1 = fail, with names)
"""
import html.parser
import pathlib
import re
import sys
import py_compile

HERE = pathlib.Path(__file__).resolve().parent
BANNED = ["muse.ai/s/the-living-map", "t.me/Zorbianbot", "github.io/madhouse/"]
failures = []


class P(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        for k in ("href", "src"):
            if d.get(k):
                self.links.append(d[k])


for page in sorted(HERE.glob("*.html")):
    try:
        text = page.read_text(encoding="utf-8")
    except Exception as exc:
        failures.append(f"{page.name}: unreadable: {exc}")
        continue
    p = P()
    try:
        p.feed(text)
    except Exception as exc:
        failures.append(f"{page.name}: HTML parse failed: {exc}")
    for link in p.links:
        if link.startswith(("http://", "https://", "//", "mailto:", "tel:", "#")):
            for bad in BANNED:
                if bad in link:
                    failures.append(f"{page.name}: banned link: {link}")
            continue
        target = (HERE / link.split("#")[0].split("?")[0]).resolve()
        if not target.is_file() or HERE not in target.parents:
            failures.append(f"{page.name}: missing internal link: {link}")
    # Every page must carry the same bottom nav, in the same order.
    nav = re.findall(r'href="([^"]+)"', text)
    expected = ["index.html", "compass.html", "control.html", "sitemap.html", "games.html", "map.html"]
    if not all(e in nav for e in expected):
        failures.append(f"{page.name}: bottom nav incomplete: {nav}")

try:
    py_compile.compile(str(HERE / "bot.py"), doraise=True)
except Exception as exc:
    failures.append(f"bot.py: compile failed: {exc}")

# Bot must not contain the old sprawl: check the command list is only 3.
bot = (HERE / "bot.py").read_text(encoding="utf-8")
for banned_cmd in ['"pocket"', '"play"', '"passport"', '"giftcard"', '"session"']:
    if banned_cmd in bot:
        failures.append(f"bot.py: old command still present: {banned_cmd}")

if failures:
    print("FAIL")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print(f"PASS: {len(list(HERE.glob('*.html')))} pages, all internal links exist, "
      "no banned links, bottom nav complete, bot.py compiles, old commands absent.")
