"""Runs the built app in a real browser against the real Firebase project and checks that the database rules behave.
Leaves two clearly labeled test rows (a score report and a trusted-source application) for the owner to dismiss."""
import asyncio, json, subprocess, sys, time, os
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = r"""async () => {
  const out = [];
  const t = async (name, want, fn) => { let got, extra = ''; try { const r = await fn(); got = 'ok'; extra = r === undefined ? '' : JSON.stringify(r).slice(0, 80); } catch (e) { got = 'denied'; extra = (e.code || '') + ' ' + String(e.message || e).slice(0, 120); }
    out.push((got === want ? 'PASS' : 'FAIL') + ' | ' + name + ' | expected ' + want + ', got ' + got + ' | ' + extra); };
  try { await Promise.race([dbReady, new Promise((_, r) => setTimeout(() => r(new Error('timed out after 25s')), 25000))]); } catch (e) { return ['FAIL | connect | ' + e.message]; }
  out.push((DB.kind === 'fire' ? 'PASS' : 'FAIL') + ' | connected to Firebase with anonymous sign-in | engine ' + DB.kind + ', signed in ' + !!DB.me.uid + ', admin ' + DB.me.admin + ', trusted ' + DB.me.trusted);
  if (DB.kind !== 'fire') return out;
  const u = DB.me.uid, id = newId();
  await t('read shared admin edits', 'ok', () => DB.get('state', 'admin').then(x => x ? 'exists' : 'empty'));
  await t('read live scores', 'ok', () => DB.get('state', 'live').then(x => x ? 'exists' : 'empty'));
  await t('fan cannot change admin edits', 'denied', () => DB.set('state', 'admin', {look: 'score'}));
  await t('untrusted fan cannot post a live score', 'denied', () => DB.set('state', 'live', {x: {as: 1, hs: 2}}, true));
  await t('fan cannot pass the admin check', 'denied', () => DB.get('adminCheck', 'x'));
  await t('send a score report', 'ok', () => DB.add('reports', {game: 'TEST', label: 'TEST from Claude - dismiss me', sport: 'Test', as: 1, hs: 2, st: 'Final', name: 'Claude test', uid: u, status: 'new', at: DB.stamp()}));
  await t('fan cannot read other reports', 'denied', () => DB.list('reports', [['status', '==', 'new']]));
  await t('apply to be trusted', 'ok', () => DB.set('applications', u, {name: 'Claude test - decline me', contact: 'none', team: 'hil', role: 'Fan', note: 'automatic test', uid: u, status: 'new', at: DB.stamp()}));
  await t('read my own application', 'ok', () => DB.get('applications', u).then(x => x.status));
  await t('fan cannot approve themselves', 'denied', () => DB.set('trusted', u, {name: 'x'}));
  await t('check my trusted status', 'ok', () => DB.get('trusted', u).then(x => x ? 'yes' : 'no'));
  await t('save a pick', 'ok', () => DB.set('picks', 'testgame__' + u, {week: 'test', game: 'testgame', pick: 'home', uid: u, name: 'Claude test', at: DB.stamp()}));
  await t('read my picks', 'ok', () => DB.list('picks', [['uid', '==', u], ['week', '==', 'test']]).then(r => r.length + ' pick, time stamped ' + (typeof r[0].at)));
  await t('cannot save a pick with a made-up time', 'denied', () => DB.set('picks', 'testgame2__' + u, {week: 'test', game: 'testgame2', pick: 'home', uid: u, name: 'x', at: 1}));
  await t('cannot read everyone\'s picks', 'denied', () => DB.list('picks', [['week', '==', 'test']]));
  await t('cast a vote', 'ok', () => DB.set('votes', 'testpoll__' + u + '__2026-01-01', {poll: 'testpoll', nom: 'n1', uid: u, day: '2026-01-01', at: DB.stamp()}));
  await t('count votes', 'ok', () => DB.count('votes', [['poll', '==', 'testpoll'], ['nom', '==', 'n1']]));
  await t('cannot change a vote', 'denied', () => DB.set('votes', 'testpoll__' + u + '__2026-01-01', {poll: 'testpoll', nom: 'n2', uid: u, day: '2026-01-01', at: DB.stamp()}));
  const px = 'data:image/jpeg;base64,' + 'A'.repeat(2000);
  await t('send a photo for approval', 'ok', async () => { await DB.set('photoFull', id, {img: px, uid: u}); await DB.set('photos', id, {team: 'hil', cap: 'test', credit: 'test', uid: u, status: 'pending', thumb: px, w: 1, h: 1, at: DB.stamp()}); });
  await t('fan cannot publish their own photo', 'denied', () => DB.set('photos', newId(), {team: 'hil', cap: 't', credit: 't', uid: u, status: 'ok', thumb: px, w: 1, h: 1, at: DB.stamp()}));
  await t('list approved photos', 'ok', () => DB.list('photos', [['status', '==', 'ok'], ['team', '==', 'hil']], {limit: 60}).then(r => r.length));
  await t('open a full photo', 'ok', () => DB.get('photoFull', id).then(x => x.img.length));
  await t('remove my own photo', 'ok', async () => { await DB.del('photos', id); await DB.del('photoFull', id); });
  await t('count a visit', 'ok', () => DB.set('visits', todayISO() + '__' + u, {day: todayISO(), uid: u, home: false, test: true}));
  await t('count a team page view', 'ok', () => DB.inc('stats', '2026-01-01', {team: {test: 1}}));
  await t('fan cannot read reach numbers', 'denied', () => DB.get('stats', '2026-01-01'));
  await t('read a leaderboard', 'ok', () => DB.get('boards', 'football:season').then(x => x ? 'exists' : 'empty'));
  return out;
}"""
async def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1"], cwd=os.path.join(ROOT, "dist"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()
            pg = await (await b.new_context(viewport={"width": 390, "height": 844})).new_page()
            logs = []
            pg.on("console", lambda m: logs.append(m.type + ": " + m.text[:300]) if m.type in ("error", "warning") else None)
            pg.on("pageerror", lambda e: logs.append("pageerror: " + str(e)[:300]))
            await pg.goto("http://localhost:8765/index.html")
            await pg.wait_for_timeout(1500)
            res = await pg.evaluate(JS)
            tabs = await pg.eval_on_selector_all("button.tab", "els => els.map(e => e.textContent)")
            print("\n".join(res)); print("TABS", tabs); print("CONSOLE", json.dumps(logs[:12], indent=1))
            print("SUMMARY %d passed, %d failed" % (sum(r.startswith("PASS") for r in res), sum(r.startswith("FAIL") for r in res)))
            await b.close()
    finally:
        srv.terminate()
asyncio.run(main())
