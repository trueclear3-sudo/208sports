"""One-off probe: roster row layout. Prints only; changes nothing."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from mp import fetch
CFG = json.load(open(os.path.join(os.path.dirname(HERE), "config.json")))
def props(url):
    st, page = fetch(url)
    m = re.search(r'(?s)<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page) if st == 200 else None
    return st, (json.loads(m.group(1))["props"]["pageProps"] if m else None)
for tid, path in [("hil", "basketball/25-26/roster/"), ("rig", "basketball/girls/25-26/roster/"), ("hil", "football/roster/"), ("hil", "basketball/roster/"), ("hil", "basketball/jv/25-26/roster/")]:
    t = next(x for x in CFG["teams"] if x["id"] == tid)
    st, pp = props(t["base"] + path)
    a = (pp or {}).get("athleteData") or []
    print("=====", tid, path, st, "athletes", len(a))
    for r in a[:3]: print(json.dumps(r))
