"""בדיקה חד-פעמית של אתר המכון הגיאולוגי (שלב 6): איך נראה ה-API שמאחורי הדף.

שומר ב-data/raw/gsi/ את ה-HTML, הקשרים מה-bundle של האפליקציה, ודוגמאות מה-API.
"""

import datetime as dt
import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "gsi"
BASE = "https://eq.gsi.gov.il"
UA = {"User-Agent": "riftmemory/0.1 (https://github.com/nadaval56/riftmemory)"}


def get(url, **kw):
    try:
        r = requests.get(url, headers=UA, timeout=60, **kw)
        return f"{r.status_code} {r.headers.get('content-type')}\n{r.text}"
    except Exception as exc:  # noqa: BLE001
        return f"ERROR {exc!r}"


def contexts(text, needle, width=400, limit=15):
    out = []
    for m in re.finditer(re.escape(needle), text):
        out.append(text[max(0, m.start() - width): m.end() + width])
        if len(out) >= limit:
            break
    return "\n\n-----\n\n".join(out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    html = requests.get(f"{BASE}/heb/earthquake/ageEarthquakes.php", headers=UA, timeout=60).text
    (OUT / "ageEarthquakes.html").write_text(html, encoding="utf-8")
    for src in re.findall(r'src="([^"]+\.js)"', html):
        js = requests.get(BASE + src, headers=UA, timeout=60).text
        print("bundle", src, len(js))
        for needle in ("startDate", "api/earthquakes", "Magnitude", "magnitude", "csv",
                       "fault", "Fault", "geojson", "arcgis", "MapServer", "kml", "/api/"):
            (OUT / f"bundle-ctx-{needle.replace('/', '_')}.txt").write_text(contexts(js, needle), encoding="utf-8")

    end = dt.datetime.now(dt.timezone.utc)
    start = end - dt.timedelta(days=7)
    fmt = "%Y-%m-%dT%H:%M:%S.000Z"
    samples = {
        "api-range": (f"{BASE}/api/earthquakes/", {"startDate": start.strftime(fmt), "endDate": end.strftime(fmt)}),
        "api-latest-check": (f"{BASE}/api/earthquakes/latest-check", {"lastId": ""}),
    }
    for name, (url, params) in samples.items():
        text = get(url, params=params)
        (OUT / f"{name}.txt").write_text(text[:40000], encoding="utf-8")
        print(name, text[:200].replace("\n", " "))


if __name__ == "__main__":
    main()
