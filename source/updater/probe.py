"""One-off probe: what does MaxPreps have for winter sports? Prints only; changes nothing."""
import json, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from mp import fetch
CFG = json.load(open(os.path.join(os.path.dirname(HERE), "config.json")))
def props(url):
    st, page = fetch(url)
    if st != 200: return st, None
    m = re.search(r'(?s)<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page)
    return st, (json.loads(m.group(1))["props"]["pageProps"] if m else None)
SCHED = ["basketball/", "basketball/jv/", "basketball/freshman/", "basketball/girls/", "basketball/girls/jv/", "basketball/girls/freshman/",
         "basketball/25-26/", "basketball/girls/25-26/", "wrestling/", "wrestling/25-26/", "wrestling/girls/", "volleyball/"]
for t in CFG["teams"]:
    for p in SCHED:
        st, pp = props(t["base"] + p + "schedule/")
        c = (pp or {}).get("contests")
        n = len(c) if c is not None else -1
        done = sum(1 for r in (c or []) if len(r) > 38 and r[4])
        sd = ((pp or {}).get("teamContext") or {}).get("standingsData") or {}
        print("SCHED", t["id"], p, st, "games", n, "played", done, "rec", (sd.get("overallStanding") or {}).get("overallWinLossTies"), flush=True)
        time.sleep(0.4)
def shape(x, d=0, mx=3):
    if d > mx: return "…"
    if isinstance(x, dict): return {k: shape(v, d + 1, mx) for k, v in list(x.items())[:40]}
    if isinstance(x, list): return ["len=%d" % len(x)] + [shape(v, d + 1, mx) for v in x[:2]]
    return x if not isinstance(x, str) else x[:60]
for name, url in [("BB-ROSTER", "basketball/25-26/roster/"), ("BB-STATS", "basketball/25-26/stats/"), ("WR-ROSTER", "wrestling/25-26/roster/"),
                  ("FB-ROSTER", "football/roster/"), ("BB-SCHED-SAMPLE", "basketball/25-26/schedule/"), ("WR-SCHED-SAMPLE", "wrestling/25-26/schedule/")]:
    for tid in ("hil", "rig"):
        t = next(x for x in CFG["teams"] if x["id"] == tid)
        st, pp = props(t["base"] + url)
        print("=====", name, tid, st)
        if not pp: continue
        if "SAMPLE" in name:
            c = pp.get("contests") or []
            print(json.dumps(c[:2])[:3000])
        else:
            print(json.dumps(shape({k: v for k, v in pp.items() if k not in ("teamContext",)}, mx=4))[:6000])
            tc = pp.get("teamContext") or {}
            print("teamContext keys", list(tc.keys())[:60])
