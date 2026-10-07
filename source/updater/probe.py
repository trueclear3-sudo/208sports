"""One-off check: can GitHub's servers read MaxPreps, and what do the pages look like as text?"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from mp import fetch, lines
B = "https://www.maxpreps.com/id/idaho-falls/hillcrest-knights/"
PAGES = {"football-v": B + "football/schedule/", "football-jv": B + "football/jv/schedule/",
         "football-fr": B + "football/freshman/schedule/", "soccer-girls": B + "soccer/girls/schedule/",
         "soccer-boys": "https://www.maxpreps.com/id/twin-falls/twin-falls-bruins/soccer/schedule/"}
out = os.path.join(os.path.dirname(__file__), "probe"); os.makedirs(out, exist_ok=True)
for name, url in PAGES.items():
    status, page = fetch(url)
    L = lines(page) if status == 200 else []
    nd = re.search(r'(?s)<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page) if status == 200 else None
    with open(os.path.join(out, name + ".txt"), "w") as f:
        f.write("URL %s\nSTATUS %s\nBYTES %d\nTEXT LINES %d\nNEXT_DATA %s\n" % (url, status, len(page), len(L), len(nd.group(1)) if nd else "none"))
        if status != 200: f.write("ERROR " + page[:500] + "\n")
        f.write("\n".join(L[:700]))
    if nd and name in ("football-v", "soccer-boys"):
        open(os.path.join(out, name + ".next.json"), "w").write(nd.group(1)[:400000])
    print(name, status, len(page), len(L))
