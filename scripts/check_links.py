"""בדיקת קישורים חיצוניים באתר הבנוי (site/). רצה פעם בחודש ב-.github/workflows/links.yml.

כל קישור http(s) שבדפים (חוץ מהאתר עצמו) נבדק פעם אחת. התוצאה מתחלקת לשלושה:
  broken   — הקישור בוודאות שבור: 404, 410, או שהשרת לא קיים (DNS).
  unsure   — לא ברור: 401/403/429 (אתרים רבים חוסמים בוטים), 5xx, פסק זמן, שגיאת SSL.
             כאן צריך לפתוח בדפדפן ולבדוק ידנית.
  ok       — עובד (כולל הפניות שמסתיימות ב-2xx).
פלט: link-report.md (טבלה לפי דפים), וקוד יציאה 1 אם יש קישורים שבורים.
"""

import concurrent.futures as cf
import re
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = ROOT / "link-report.md"
UA = {"User-Agent": "Mozilla/5.0 (riftmemory link check; https://github.com/nadaval56/riftmemory)",
      "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8"}
SKIP_HOSTS = {"nadaval56.github.io", "quake.co.il", "www.quake.co.il"}
HREF = re.compile(r'href="(https?://[^"]+)"')


def collect():
    """{url: [דפים שבהם הוא מופיע]}"""
    found = {}
    for path in sorted(SITE.rglob("*.html")):
        page = "/" + str(path.relative_to(SITE)).removesuffix("index.html")
        for url in HREF.findall(path.read_text(encoding="utf-8")):
            url = url.replace("&amp;", "&").split("#")[0]
            if urlparse(url).hostname in SKIP_HOSTS:
                continue
            found.setdefault(url, [])
            if page not in found[url]:
                found[url].append(page)
    return found


def check(url):
    """(סוג, תיאור קצר)"""
    try:
        r = requests.head(url, headers=UA, timeout=25, allow_redirects=True)
        # שרתים רבים לא תומכים ב-HEAD או עונים עליו אחרת: במקרה של שגיאה, GET
        if r.status_code >= 400:
            r = requests.get(url, headers=UA, timeout=25, allow_redirects=True, stream=True)
            r.close()
    except requests.exceptions.ConnectionError as exc:
        host = urlparse(url).hostname
        try:
            socket.getaddrinfo(host, 443)
        except socket.gaierror:
            return "broken", "השרת לא קיים (DNS)"
        return "unsure", f"שגיאת חיבור: {type(exc).__name__}"
    except requests.exceptions.Timeout:
        return "unsure", "פסק זמן"
    except requests.exceptions.RequestException as exc:
        return "unsure", type(exc).__name__
    code = r.status_code
    if code in (404, 410):
        return "broken", f"HTTP {code}"
    if code >= 400:
        return "unsure", f"HTTP {code}"
    return "ok", f"HTTP {code}"


def main():
    if not SITE.exists():
        sys.exit("site/ לא קיים. קודם: build_events.py ו-build_site.py")
    found = collect()
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        results = dict(zip(found, pool.map(check, found)))
    broken = {u: r for u, r in results.items() if r[0] == "broken"}
    unsure = {u: r for u, r in results.items() if r[0] == "unsure"}

    lines = [f"# בדיקת קישורים חיצוניים", "",
             f"נבדקו {len(found)} קישורים: {len(broken)} שבורים, {len(unsure)} לא ברורים (לבדוק בדפדפן), "
             f"{len(found) - len(broken) - len(unsure)} תקינים.", ""]
    for title, group in (("שבורים", broken), ("לא ברורים", unsure)):
        if not group:
            continue
        lines += [f"## {title}", "", "| קישור | תוצאה | בדפים |", "|---|---|---|"]
        for url, (_, why) in sorted(group.items()):
            pages = ", ".join(found[url][:4]) + (" ועוד" if len(found[url]) > 4 else "")
            lines.append(f"| {url} | {why} | {pages} |")
        lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(lines[2])
    sys.exit(1 if broken else 0)


if __name__ == "__main__":
    main()
