#!/usr/bin/env python3
"""208 Pressbox score alerts.

Runs every few minutes on game nights (GitHub Actions). Looks at every score the app knows about — MaxPreps finals,
the owner's corrections, reporters' live scores and scores two fans agree on — and sends a phone alert for each one
that changed since the last run, to everyone who asked for that team.

Needs one GitHub secret, FIREBASE_SA: the Firebase service account key (JSON). Without it this script does nothing.
On its first run it makes the alert key pair (kept in Firestore secret/vapid, public half in state/push) and only
records the current scores, so nobody gets a pile of old alerts.

Web Push is done by hand (RFC 8291 encryption + VAPID) so the only libraries are cryptography, requests, google-auth.
"""
import base64, datetime, json, os, struct, sys, time
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
SITE = "https://trueclear3-sudo.github.io/208sports/"
LV = {"v": "", "jv": " JV", "fr": " Freshman"}

def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def unb64u(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

# ---------------------------------------------------------------- Web Push
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, hmac, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

def _hmac(key, data):
    h = hmac.HMAC(key, hashes.SHA256()); h.update(data); return h.finalize()

def pub_bytes(k): return k.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)

def encrypt(payload, p256dh, auth, salt=None, eph=None):
    """aes128gcm body for one subscription (RFC 8291 / RFC 8188)."""
    ua_pub = unb64u(p256dh); secret = unb64u(auth)
    eph = eph or ec.generate_private_key(ec.SECP256R1()); as_pub = pub_bytes(eph)
    shared = eph.exchange(ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ua_pub))
    ikm = _hmac(_hmac(secret, shared), b"WebPush: info\x00" + ua_pub + as_pub + b"\x01")
    salt = salt or os.urandom(16); prk = _hmac(salt, ikm)
    cek = _hmac(prk, b"Content-Encoding: aes128gcm\x00\x01")[:16]
    nonce = _hmac(prk, b"Content-Encoding: nonce\x00\x01")[:12]
    body = AESGCM(cek).encrypt(nonce, payload + b"\x02", None)
    return salt + struct.pack("!IB", 4096, len(as_pub)) + as_pub + body

def vapid_header(endpoint, priv):
    from urllib.parse import urlparse
    u = urlparse(endpoint)
    head = b64u(json.dumps({"typ": "JWT", "alg": "ES256"}).encode())
    claims = b64u(json.dumps({"aud": "%s://%s" % (u.scheme, u.netloc), "exp": int(time.time()) + 12 * 3600, "sub": SITE}).encode())
    r, s = decode_dss_signature(priv.sign((head + "." + claims).encode(), ec.ECDSA(hashes.SHA256())))
    jwt = head + "." + claims + "." + b64u(r.to_bytes(32, "big") + s.to_bytes(32, "big"))
    return "vapid t=%s, k=%s" % (jwt, b64u(pub_bytes(priv)))

def send_push(http, sub, msg, priv):
    body = encrypt(json.dumps(msg).encode(), sub["keys"]["p256dh"], sub["keys"]["auth"])
    r = http.post(sub["endpoint"], data=body, timeout=20, headers={
        "Content-Encoding": "aes128gcm", "Content-Type": "application/octet-stream", "TTL": "3600", "Urgency": "high",
        "Authorization": vapid_header(sub["endpoint"], priv)})
    return r.status_code

# ---------------------------------------------------------------- Firestore over REST
def fs_val(v):
    if "stringValue" in v: return v["stringValue"]
    if "integerValue" in v: return int(v["integerValue"])
    if "doubleValue" in v: return v["doubleValue"]
    if "booleanValue" in v: return v["booleanValue"]
    if "nullValue" in v: return None
    if "timestampValue" in v:
        return int(datetime.datetime.fromisoformat(v["timestampValue"].replace("Z", "+00:00")).timestamp() * 1000)
    if "mapValue" in v: return {k: fs_val(x) for k, x in v["mapValue"].get("fields", {}).items()}
    if "arrayValue" in v: return [fs_val(x) for x in v["arrayValue"].get("values", [])]
    return None
def fs_doc(d): return dict({k: fs_val(v) for k, v in d.get("fields", {}).items()}, id=d["name"].rsplit("/", 1)[1])

class Store:
    def __init__(self, info):
        from google.oauth2 import service_account
        from google.auth.transport.requests import AuthorizedSession
        cred = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/datastore"])
        self.s = AuthorizedSession(cred)
        self.base = "https://firestore.googleapis.com/v1/projects/%s/databases/(default)/documents" % info["project_id"]
    def get(self, path):
        r = self.s.get(self.base + "/" + path, timeout=20)
        if r.status_code == 404: return None
        r.raise_for_status(); return fs_doc(r.json())
    def put(self, path, fields):
        enc = {k: {"stringValue": v} if isinstance(v, str) else {"integerValue": str(v)} for k, v in fields.items()}
        r = self.s.patch(self.base + "/" + path, json={"fields": enc}, timeout=20); r.raise_for_status()
    def delete(self, path): self.s.delete(self.base + "/" + path, timeout=20)
    def list(self, col):
        out, tok = [], None
        while True:
            r = self.s.get(self.base + "/" + col, params={"pageSize": 300, **({"pageToken": tok} if tok else {})}, timeout=30)
            r.raise_for_status(); j = r.json(); out += [fs_doc(d) for d in j.get("documents", [])]
            tok = j.get("nextPageToken")
            if not tok: return out
    def query(self, col, eq):
        f = [{"fieldFilter": {"field": {"fieldPath": k}, "op": "EQUAL", "value": {"stringValue": v}}} for k, v in eq.items()]
        q = {"structuredQuery": {"from": [{"collectionId": col}], "where": {"compositeFilter": {"op": "AND", "filters": f}}, "limit": 500}}
        r = self.s.post(self.base + ":runQuery", json=q, timeout=30); r.raise_for_status()
        return [fs_doc(x["document"]) for x in r.json() if "document" in x]

# ---------------------------------------------------------------- what the scores are right now
def fan_agree(reports):
    """Same rule as the app: two different phones reporting the same score."""
    by, out = {}, {}
    for r in reports:
        if r.get("status") != "new" or r.get("as") is None or r.get("hs") is None: continue
        g = by.setdefault(r["game"], {})
        if r["uid"] not in g or (g[r["uid"]].get("at") or 0) < (r.get("at") or 0): g[r["uid"]] = r
    for gid, rs in by.items():
        grp = {}
        for r in rs.values(): grp.setdefault((r["as"], r["hs"]), []).append(r)
        for (a, h), l in grp.items():
            if len(l) < 2: continue
            last = max(l, key=lambda r: r.get("at") or 0); fin = next((r for r in l if str(r.get("st", "")).startswith("Final")), None)
            e = dict(**{"as": a, "hs": h}, st=fin["st"] if fin else last["st"], at=last.get("at") or 0)
            if gid not in out or out[gid]["at"] < e["at"]: out[gid] = e
    return out

def current_scores(data, patch, live, fans, days):
    out = {}
    pscores = (patch or {}).get("scores") or {}
    for g in data["games"]:
        if g["date"] not in days: continue
        ps = pscores.get(g["id"])
        if ps and ps[0] is not None and ps[1] is not None: out[g["id"]] = (ps[0], ps[1], "Final"); continue
        if g.get("hs") is not None: out[g["id"]] = (g["as"], g["hs"], "Final/OT" if g.get("note") == "OT" else "Final"); continue
        cands = [x for x in ((live or {}).get(g["id"]), fans.get(g["id"])) if x and x.get("as") is not None]
        if cands:
            x = max(cands, key=lambda c: (str(c.get("st", "")).startswith("Final"), c.get("at") or 0))
            out[g["id"]] = (x["as"], x["hs"], x.get("st") or "")
    return out

def message(g, sc, teams, sports):
    nm = lambda w: teams[g[w]]["name"] if g.get(w) else g.get("outside", "")
    a, h, st = sc; final = st.startswith("Final")
    sport = sports.get(g.get("sport", "football"), "") + LV.get(g.get("level", "v"), "")
    lead = "" if a == h else (" · %s %s" % (nm("away") if a > h else nm("home"), "wins" if final else "leads"))
    return {"title": "%s · %s" % (st.upper() if final else st, sport), "body": "%s %d, %s %d%s" % (nm("away"), a, nm("home"), h, lead),
            "tag": g["id"], "url": SITE + "?g=" + g["id"]}, final

def main():
    raw = os.environ.get("FIREBASE_SA", "").strip()
    if not raw: print("No FIREBASE_SA secret yet, so score alerts are off."); return
    db = Store(json.loads(raw))
    import requests
    http = requests.Session()

    keys = db.get("secret/vapid")
    if not keys:
        k = ec.generate_private_key(ec.SECP256R1())
        pem = k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
        db.put("secret/vapid", {"pem": pem}); keys = {"pem": pem}; print("Made the alert keys.")
    priv = serialization.load_pem_private_key(keys["pem"].encode(), None)
    pub = b64u(pub_bytes(priv))
    pushdoc = db.get("state/push")
    if not pushdoc or pushdoc.get("key") != pub: db.put("state/push", {"key": pub}); print("Published the public alert key.")

    now = datetime.datetime.now(ZoneInfo("America/Boise"))
    days = {now.date().isoformat(), (now.date() - datetime.timedelta(days=1)).isoformat()}
    data = json.load(open(os.path.join(SRC, "data.json")))
    teams = {t["id"]: t for t in data["teams"]}; sports = {s["id"]: s["name"] for s in data["sports"]}
    games = {g["id"]: g for g in data["games"]}
    patch = db.get("state/admin"); live = db.get("state/live") or {}
    live.pop("id", None)
    reports = []
    for d in days: reports += db.query("reports", {"day": d})
    scores = current_scores(data, patch, live, fan_agree(reports), days)

    sentdoc = db.get("secret/sent")
    first = sentdoc is None
    sent = json.loads(sentdoc.get("map", "{}")) if sentdoc else {}
    sent = {k: v for k, v in sent.items() if k.startswith("rep:") or (games.get(k) and games[k]["date"] in days)}
    events, admin_events = [], []
    for gid, sc in scores.items():
        sig = "%s-%s-%s" % sc
        if sent.get(gid) == sig: continue
        sent[gid] = sig
        if not first: events.append((games[gid], message(games[gid], sc, teams, sports)))
    for r in reports:
        if r.get("status") != "new" or ("rep:" + r["id"]) in sent: continue
        sent["rep:" + r["id"]] = 1
        if not first: admin_events.append({"title": "Score report", "body": "%s · %s-%s %s · from %s" % (r.get("label", ""), r.get("as"), r.get("hs"), r.get("st", ""), r.get("name", "")),
                                           "tag": "rep", "url": SITE + "#admin"})
    if first: print("First run: recorded %d current scores, no alerts sent." % len(scores))
    print("%d score changes, %d new reports" % (len(events), len(admin_events)))

    if events or admin_events:
        subs = db.list("push"); n = gone = 0
        for s in subs:
            sub = s.get("sub") or {}
            if not sub.get("endpoint") or not (sub.get("keys") or {}).get("p256dh"): continue
            msgs = []
            for g, (msg, final) in events:
                if not (s.get("all") or g.get("home") in (s.get("teams") or []) or g.get("away") in (s.get("teams") or [])): continue
                if not final and not s.get("every"): continue
                msgs.append(msg)
            if s.get("admin"): msgs += admin_events
            for msg in msgs[:8]:
                try: code = send_push(http, sub, msg, priv)
                except Exception as e: print("send failed:", str(e)[:120]); continue
                if code in (404, 410): db.delete("push/" + s["id"]); gone += 1; break
                if code >= 400: print("push service said", code, "for", s["id"][:6])
                else: n += 1
        print("sent %d alerts to %d phones; %d phones had turned alerts off" % (n, len(subs), gone))
    db.put("secret/sent", {"map": json.dumps(sent, separators=(",", ":"))})

if __name__ == "__main__":
    main()
