#!/usr/bin/env python3
"""208 Pressbox score updater.

Reads every team's MaxPreps schedule page, cross-checks the games, and rebuilds the app.
Runs on a schedule in GitHub Actions. Standard library only.

    python3 source/updater/update.py              # pull from MaxPreps, rebuild if anything changed
    python3 source/updater/update.py --from-cache # redo the merge from the last pull (no network)

Safety rules, in order of importance:
  1. A page that fails to load never erases anything: that team's existing games are kept.
  2. A score that is already published is never blanked out.
  3. If too many pages fail, or the result looks much smaller than before, nothing is changed.
  4. Rows in overrides.json (the owner's own corrections) win over MaxPreps.
"""
import datetime, json, os, re, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
ROOT = os.path.dirname(SRC)
sys.path.insert(0, HERE)
from mp import fetch

def load(name, default=None):
    p = os.path.join(SRC, name)
    return json.load(open(p)) if os.path.exists(p) else default

CFG, STATIC, OVR = load("config.json"), load("static.json"), load("overrides.json", {})
TEAMS = {t["id"]: t for t in CFG["teams"]}
NAME2ID = {t["name"]: t["id"] for t in CFG["teams"]}
SPORTS = {s["id"]: s for s in CFG["sports"]}
LEVEL_NAME = {"v": "Varsity", "jv": "JV", "fr": "Freshman"}

def school_root(url):
    m = re.match(r"(https://www\.maxpreps\.com/[a-z]{2}/[^/]+/[^/]+/)", url or "")
    return m.group(1) if m else None
ROOT2ID = {t["base"]: t["id"] for t in CFG["teams"]}

def clock(hhmm):
    try:
        h, m = [int(x) for x in hhmm.split(":")]
    except Exception:
        return None
    return "%d:%02d %s" % ((h % 12) or 12, m, "PM" if h >= 12 else "AM")

# ---------------------------------------------------------------- reading one page
def parse_page(page):
    """MaxPreps ships the schedule as JSON inside the page. Each game is a positional list:
       [3] deleted  [4] has a result  [11] local date-time  [37] this team  [38] the opponent
       team: [3] 'W 32-7'  [6] score  [11] 1 = away, 0 = home  [12] 0 conference, 1 non-conference, other = postseason
             [13] team link  [14] school name  [16] state"""
    m = re.search(r'(?s)<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page)
    if not m: raise ValueError("page has no schedule data block")
    pp = json.loads(m.group(1))["props"]["pageProps"]
    contests = pp.get("contests")
    if contests is None: raise ValueError("page has no game list")
    rows = []
    for r in contests:
        if len(r) < 39: raise ValueError("game record has %d fields, expected 39 or more" % len(r))
        if r[3]: continue
        me, op = r[37], r[38]
        if not me or not op or not op[14] or not r[11]: continue
        played = bool(r[4]) and isinstance(me[6], int) and isinstance(op[6], int)
        note = re.search(r"\(([^)]*)\)", me[3] or "")
        name = op[14] + (" (%s)" % op[16] if op[16] and op[16] != "ID" else "")
        rows.append(dict(date=r[11][:10], time=clock(r[11][11:16]), ha={0: "H", 1: "A"}.get(me[11], "N"),
                         opp=name, oid=ROOT2ID.get(school_root(op[13])), sc=[me[6], op[6]] if played else None,
                         type=me[12], note=note.group(1) if note else ""))
    sd = (pp.get("teamContext") or {}).get("standingsData") or {}
    stated = dict(overall=(sd.get("overallStanding") or {}).get("overallWinLossTies"),
                  conf=(sd.get("leagueStanding") or {}).get("conferenceWinLossTies"))
    return rows, stated

def parse_roster(page):
    """Roster rows are positional too: [8] jersey  [12] position  [33] full name  [36] grade ('Sr.')."""
    m = re.search(r'(?s)<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page)
    if not m: raise ValueError("page has no roster data block")
    rows = json.loads(m.group(1))["props"]["pageProps"].get("athleteData")
    if rows is None: raise ValueError("page has no roster list")
    out = []
    for r in rows:
        if len(r) < 37: raise ValueError("roster record has %d fields, expected 37" % len(r))
        name = (r[33] or "").strip()
        if not name or re.match(r"Player #", name): continue
        out.append(dict(n=str(r[8] or ""), name=name, pos=(r[12] or "").strip(), gr=(r[36] or "").strip(". ")))
    return out

def pull_rosters(out):
    """Varsity rosters for sports that ask for them. If this season's is empty, last season's is used and labeled."""
    for sp in CFG["sports"]:
        if not sp.get("on") or not sp.get("roster"): continue
        for t in CFG["teams"]:
            key = "roster|%s|%s" % (sp["id"], t["id"])
            res = dict(ok=True, rows=[], stated={}, players=[], season="")
            try:
                for season in ("", sp["roster"].get("lastSeason", "")):
                    status, page = fetch(t["base"] + sp["paths"]["v"] + (season + "/" if season else "") + "roster/")
                    if status != 200: raise ValueError("could not load (%s)" % str(page)[:80])
                    res["players"], res["season"] = parse_roster(page), season
                    time.sleep(0.6)
                    if res["players"] or not sp["roster"].get("lastSeason"): break
            except Exception as e:
                res = dict(ok=False, error=str(e)[:200], rows=[], stated={}, players=[], season="")
            out[key] = res
            print(("ok  " if res["ok"] else "FAIL"), key, len(res["players"]), res.get("season"), res.get("error", ""))

def pull():
    out = {}
    for sp in CFG["sports"]:
        if not sp.get("on"): continue
        for lv in sp["levels"]:
            for t in CFG["teams"]:
                key = "%s|%s|%s" % (sp["id"], lv, t["id"])
                url = t["base"] + sp["paths"][lv] + "schedule/"
                status, page = fetch(url)
                try:
                    if status != 200: raise ValueError("could not load (%s)" % str(page)[:80])
                    rows, stated = parse_page(page)
                    out[key] = dict(ok=True, rows=rows, stated=stated)
                except Exception as e:
                    out[key] = dict(ok=False, error=str(e)[:200], rows=[], stated={})
                print(("ok  " if out[key]["ok"] else "FAIL"), key, len(out[key]["rows"]), out[key].get("error", ""))
                time.sleep(0.6)
    pull_rosters(out)
    return out

# ---------------------------------------------------------------- putting games together
def dnum(iso): return datetime.date.fromisoformat(iso).toordinal()

def merge(sport, level, pulled, flags):
    """A game between two app teams is listed on both schools' pages. Pair the two listings and cross-check."""
    rows = []
    for t in CFG["teams"]:
        key = "%s|%s|%s" % (sport, level, t["id"])
        if key in OVR:
            for o in OVR[key]["rows"]:
                rows.append(dict(tid=t["id"], date=o["date"], time=o.get("time"), ha=o["ha"], opp=o["opp"], oid=NAME2ID.get(o["opp"]),
                                 sc=o.get("sc"), type=o.get("type"), note=o.get("note", ""), auth=True, used=False))
        else:
            for r in pulled.get(key, {}).get("rows", []):
                rows.append(dict(r, tid=t["id"], auth=False, used=False))
    label = SPORTS[sport]["name"] + ("" if level == "v" else " " + LEVEL_NAME[level])
    games = []
    for r in rows:
        if r["used"]: continue
        r["used"] = True
        tid, oid = r["tid"], r["oid"]
        types = [r["type"]]
        if not oid:
            home = r["ha"] != "A"
            g = dict(home=tid if home else None, away=None if home else tid, outside=r["opp"], hs=None)
            g["as"] = None
            if r["sc"]: g["hs"], g["as"] = (r["sc"][0], r["sc"][1]) if home else (r["sc"][1], r["sc"][0])
            if r["ha"] == "N": g["siteUnknown"] = True
            date_, tm, note = r["date"], r["time"], r["note"]
        else:
            cands = sorted([x for x in rows if not x["used"] and x["tid"] == oid and x["oid"] == tid and abs(dnum(x["date"]) - dnum(r["date"])) <= 3],
                           key=lambda x: abs(dnum(x["date"]) - dnum(r["date"])))
            p = cands[0] if cands else None
            if p: p["used"] = True; types.append(p["type"])
            lead = r if (r["auth"] or not p or not p["auth"]) else p      # an owner-corrected row leads
            other = p if lead is r else r
            a, b = lead["tid"], lead["oid"]
            home, away = (a, b) if lead["ha"] != "A" else (b, a)
            g = dict(home=home, away=away)
            name = "%s %s: %s at %s" % (label, lead["date"], TEAMS[away]["name"], TEAMS[home]["name"])
            mine = {a: lead["sc"][0], b: lead["sc"][1]} if lead["sc"] else None
            theirs = {b: other["sc"][0], a: other["sc"][1]} if other and other["sc"] else None
            if mine and theirs and mine != theirs and not lead["auth"]:
                flags.append(name + " — the two schools' pages show different scores (%d-%d and %d-%d)" % (mine[away], mine[home], theirs[away], theirs[home]))
            if other and not lead["auth"] and (other["ha"] == lead["ha"] or "N" in (other["ha"], lead["ha"])):
                g["siteUnknown"] = True
            sc = mine or theirs
            g["hs"], g["as"] = (sc[home], sc[away]) if sc else (None, None)
            src = lead if (lead["auth"] or lead["sc"] or not other or not other["sc"]) else other
            date_, tm = src["date"], lead["time"] or (other["time"] if other else None)
            note = lead["note"] or (other["note"] if other else "")
        known = [x for x in types if x is not None]
        conf = any(x == 0 for x in known)
        post = bool(known) and not conf and any(x not in (0, 1) for x in known)
        ids = sorted(x for x in (g["home"], g["away"]) if x)
        g.update(sport=sport, level=level, date=date_, time=tm, note=note, conf=conf, post=post, sponsors=[], sponsorMode="winner")
        g["id"] = (level if sport == "football" else sport if level == "v" else sport + "-" + level) + ":" + date_ + ":" + ":".join(ids) + (":x" if len(ids) == 1 else "")
        games.append(g)
    seen = {}
    for g in games:
        seen[g["id"]] = seen.get(g["id"], 0) + 1
        if seen[g["id"]] > 1: g["id"] += ":" + str(seen[g["id"]])
    return games

def record(games, tid):
    r = dict(w=0, l=0, t=0, cw=0, cl=0, ct=0)
    for g in games:
        if tid not in (g["home"], g["away"]) or g["hs"] is None: continue
        mine, theirs = (g["hs"], g["as"]) if g["home"] == tid else (g["as"], g["hs"])
        k = "w" if mine > theirs else "l" if mine < theirs else "t"
        r[k] += 1
        if g["conf"]: r["c" + k] += 1
    f = lambda w, l, t: "%d-%d" % (w, l) + ("-%d" % t if t else "")
    return f(r["w"], r["l"], r["t"]), f(r["cw"], r["cl"], r["ct"])

def same_record(a, b):
    n = lambda s: [int(x) for x in (s or "").split("-") if x.isdigit()] + [0]
    return (n(a) + [0, 0])[:3] == (n(b) + [0, 0])[:3]

# ---------------------------------------------------------------- main
def main():
    cache = os.path.join(HERE, "last-pull.json")
    if "--from-cache" in sys.argv:
        pulled = json.load(open(cache))
    else:
        pulled = pull()
    pages = len(pulled); failed = [k for k, v in pulled.items() if not v["ok"]]
    print("\n%d pages read, %d failed" % (pages - len(failed), len(failed)))
    if pages == 0 or len(failed) > pages * 0.25:
        print("STOPPING: too many pages failed. Nothing was changed."); sys.exit(1)

    prev = load("data.json", {"games": []})
    prev_by_id = {g["id"]: g for g in prev.get("games", [])}
    flags, games, changes = [], [], []
    for sp in CFG["sports"]:
        if not sp.get("on"): continue
        for lv in sp["levels"]:
            new = merge(sp["id"], lv, pulled, flags)
            ids = {g["id"] for g in new}
            for t in CFG["teams"]:                       # rule 1: a failed page keeps that team's old games
                key = "%s|%s|%s" % (sp["id"], lv, t["id"])
                if key in pulled and not pulled[key]["ok"] and key not in OVR:
                    for p in prev.get("games", []):
                        if p.get("sport", "football") == sp["id"] and p.get("level", "v") == lv and t["id"] in (p["home"], p["away"]) and p["id"] not in ids:
                            new.append(p); ids.add(p["id"])
            for g in new:
                p = prev_by_id.get(g["id"])
                if not p: continue
                g["sponsors"], g["sponsorMode"] = p.get("sponsors", []), p.get("sponsorMode", "winner")
                if g["hs"] is None and p.get("hs") is not None:      # rule 2: never blank a published score
                    g["hs"], g["as"] = p["hs"], p["as"]
            label = sp["name"] + ("" if lv == "v" else " " + LEVEL_NAME[lv])
            for g in new:
                p = prev_by_id.get(g["id"])
                if g["hs"] is not None and (not p or p.get("hs") is None):
                    changes.append("%s: %s %d, %s %d" % (label, TEAMS[g["away"]]["name"] if g["away"] else g.get("outside"), g["as"],
                                                        TEAMS[g["home"]]["name"] if g["home"] else g.get("outside"), g["hs"]))
                elif p and g["hs"] is not None and (g["hs"], g["as"]) != (p.get("hs"), p.get("as")):
                    changes.append("%s: score corrected on %s" % (label, g["date"]))
            diffs = []
            for t in CFG["teams"]:
                key = "%s|%s|%s" % (sp["id"], lv, t["id"])
                st = pulled.get(key, {}).get("stated") or {}
                if not pulled.get(key, {}).get("ok") or not st.get("overall"): continue
                calc = record(new, t["id"])
                if not same_record(calc[0], st["overall"]):
                    diffs.append("%s app %s, MaxPreps %s" % (t["name"], calc[0], st["overall"]))
                elif lv == "v" and st.get("conf") and not same_record(calc[1], st["conf"]):
                    diffs.append("%s conference: app %s, MaxPreps %s" % (t["name"], calc[1], st["conf"]))
            if diffs: flags.append(label + " records that differ from MaxPreps: " + "; ".join(diffs))
            games += sorted(new, key=lambda g: (g["date"], g["id"]))
    for k in failed: flags.append("Could not read the MaxPreps page for %s — kept what the app already had" % k.replace("|", " / "))
    flags += CFG.get("notes", [])

    if len(prev.get("games", [])) and len(games) < 0.7 * len(prev["games"]):
        print("STOPPING: only %d games found, the app has %d. Nothing was changed." % (len(games), len(prev["games"]))); sys.exit(1)

    teams = []
    for t in CFG["teams"]:
        st = STATIC["teams"].get(t["id"], {})
        rosters, note = json.loads(json.dumps(st.get("rosters", {}))), {}
        old = next((x for x in prev.get("teams", []) if x["id"] == t["id"]), {})
        for sp in CFG["sports"]:
            r = pulled.get("roster|%s|%s" % (sp["id"], t["id"]))
            if r and r["ok"] and r["players"]:
                rosters.setdefault(sp["id"], {})["v"] = r["players"]
                if r["season"]: note[sp["id"]] = "20" + r["season"].replace("-", "-")
            elif sp.get("roster") and (old.get("rosters", {}).get(sp["id"], {}).get("v")):   # a failed page keeps the roster the app had
                rosters.setdefault(sp["id"], {})["v"] = old["rosters"][sp["id"]]["v"]
                if old.get("rosterNote", {}).get(sp["id"]): note[sp["id"]] = old["rosterNote"][sp["id"]]
        teams.append(dict(id=t["id"], name=t["name"], mascot=t["mascot"], conf=t["conf"],
                          links={s["id"]: t["base"] + s["paths"]["v"] for s in CFG["sports"]},
                          rosters=rosters, rosterNote=note, stats=st.get("stats", {}), favBiz=[]))
    sports = [dict(id=s["id"], name=s["name"], on=s.get("on", True), levels=s["levels"]) for s in CFG["sports"]]
    body = dict(season=CFG["season"], statsDate=STATIC.get("statsDate"), sports=sports, teams=teams, games=games,
                businesses=prev.get("businesses", []), flags=flags)
    old_body = {k: prev.get(k) for k in body}
    print("%d games, %d with scores, %d notes for the admin" % (len(games), sum(1 for g in games if g["hs"] is not None), len(flags)))
    for f in flags: print("  NOTE", f)
    if "--from-cache" not in sys.argv:
        json.dump(pulled, open(cache, "w"), separators=(",", ":"))
    if body == old_body and "--force" not in sys.argv:
        print("\nNo changes."); return
    body["pulled"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    json.dump(body, open(os.path.join(SRC, "data.json"), "w"), separators=(",", ":"))
    subprocess.run([sys.executable, "build.py"], cwd=SRC, check=True)
    shutil.copy(os.path.join(SRC, "dist", "index.html"), os.path.join(ROOT, "index.html"))
    summary = "%d new or changed results" % len(changes) if changes else "schedule or notes changed"
    open(os.path.join(HERE, "last-run.txt"), "w").write(body["pulled"] + "\n" + summary + "\n" + "\n".join(changes[:200]) + "\n")
    print("\nUpdated: " + summary); [print("  ", c) for c in changes[:60]]

if __name__ == "__main__":
    main()
