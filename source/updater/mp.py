"""Fetch a MaxPreps page and turn it into plain text lines. Standard library only."""
import re, urllib.request, html, gzip, time, random

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15"

def fetch(url, tries=3):
    """Returns (status, text). Never raises: a failed fetch is reported, not hidden."""
    last = "no attempt"
    for i in range(tries):
        try:
            req = urllib.request.Request(url + ("&" if "?" in url else "?") + "r=%d" % random.randint(1, 10**9), headers={
                "User-Agent": UA, "Accept": "text/html,application/xhtml+xml", "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip", "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip": raw = gzip.decompress(raw)
                return r.status, raw.decode("utf-8", "replace")
        except Exception as e:  # HTTPError carries a code; anything else is a network failure
            last = "%s %s" % (getattr(e, "code", "ERR"), e)
            time.sleep(2 + 3 * i)
    return 0, last

def lines(page):
    """Visible text, one fragment per line, scripts and styles removed."""
    page = re.sub(r"(?is)<(script|style|noscript|svg)\b.*?</\1>", " ", page)
    page = re.sub(r"(?i)<br\s*/?>|</(td|th|tr|li|div|p|a|span|h\d)>", "\n", page)
    page = html.unescape(re.sub(r"<[^>]+>", " ", page))
    return [l for l in (re.sub(r"\s+", " ", x).strip() for x in page.split("\n")) if l]
