# Assembles the single-file app from app.src.html + data.json + logos + the inlined Preact/htm library.
# Output: dist/preview.html (for the Claude preview) and dist/index.html (the deployable page).
import base64, json, os, glob
src = open("app.src.html").read()
lib = open("package/preact/standalone.umd.js").read()
data = open("data.json").read()
logos = {os.path.basename(p)[:-5]: "data:image/webp;base64," + base64.b64encode(open(p, "rb").read()).decode()
         for p in sorted(glob.glob("logos/*.webp"))}
def uri(p, mime): return "data:%s;base64,%s" % (mime, base64.b64encode(open(p, "rb").read()).decode())
brand = {"icon": uri("brand/icon-96.webp", "image/webp")}
# Playoff brackets are kept by hand in brackets.json and travel with the data.
d = json.loads(data); d["brackets"] = json.load(open("brackets.json")) if os.path.exists("brackets.json") else []
data = json.dumps(d, separators=(",", ":"))
# firebase.json holds the shared database's web config. Without it the app keeps admin changes on one device.
fb = open("firebase.json").read().strip() if os.path.exists("firebase.json") else "null"
out = src.replace("/*BRAND*/", json.dumps(brand)).replace("/*LIB*/", lib).replace("/*DATA*/", data).replace("/*LOGOS*/", json.dumps(logos)).replace("/*FIREBASE*/null", fb)
os.makedirs("dist", exist_ok=True)
open("dist/preview.html", "w").write(out)
out = out.replace("/*ADMIN*/true", "location.hash==='#admin'").replace("/*PREVIEW*/true", "false")
out = out.replace('<meta charset="utf-8">\n', '', 1)
head, body = out.split('<div id="app">', 1)
full = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="theme-color" content="#0E1116"><meta name="apple-mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-title" content="208 Pressbox"><link rel="manifest" href="manifest.json">'
        '<link rel="apple-touch-icon" href="apple-touch-icon.png"><link rel="icon" type="image/png" sizes="192x192" href="icon-192.png">'
        + head + '</head><body><div id="app">' + body + '</body></html>')
open("dist/index.html", "w").write(full)
import shutil
for f in ("icon-192.png", "icon-512.png", "apple-touch-icon.png"): shutil.copy("brand/" + f, "dist/" + f)
json.dump({"name": "208 Pressbox", "short_name": "208 Pressbox", "start_url": ".", "scope": ".", "display": "standalone",
           "background_color": "#0E1116", "theme_color": "#0E1116",
           "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                     {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}]},
          open("dist/manifest.json", "w"), indent=1)
print("built", len(out) // 1024, "KB")

open("dist/.nojekyll", "w").write("")
