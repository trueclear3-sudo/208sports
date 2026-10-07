"""One-off probe: stat page layout and volleyball levels. Prints only; changes nothing."""
import json, os, re, sys, time, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from mp import fetch
CFG = json.load(open(os.path.join(os.path.dirname(HERE), "config.json")))
def props(url):
    st, page = fetch(url)
    m = re.search(r'(?s)<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page) if st == 200 else None
    return st, (json.loads(m.group(1))["props"]["pageProps"] if m else None)
for t in CFG["teams"]:
    for p in ("volleyball/jv/", "volleyball/freshman/"):
        st, pp = props(t["base"] + p + "schedule/"); c = (pp or {}).get("contests")
        print("SCHED", t["id"], p, st, "games", len(c) if c is not None else -1, flush=True); time.sleep(0.4)
for tid, path in [("hil", "football/stats/"), ("sky", "football/stats/"), ("hil", "basketball/25-26/stats/"), ("hil", "soccer/girls/stats/"), ("sky", "soccer/girls/stats/"), ("hil", "volleyball/stats/"), ("bon", "volleyball/stats/"), ("rig", "football/stats/")]:
    t = next(x for x in CFG["teams"] if x["id"] == tid)
    st, pp = props(t["base"] + path)
    d = (pp or {}).get("playerStatLeadersData") or {}
    L = d.get("leaders") or []
    print("=====", tid, path, st, "leaders", len(L), "keys", list(d.keys()))
    print("cats", dict(collections.Counter((x.get("stat") or {}).get("displayName") for x in L)))
    for x in L[:3]: print(json.dumps(x)[:700])
    print("minimums", d.get("minimums"), "updated", (d.get("lastUpdated") or {}).get("timeStamp"))
    extra = {k: (type(v).__name__, len(v) if hasattr(v, "__len__") else v) for k, v in (pp or {}).items() if "tat" in k}
    print("stat-ish keys", extra)
