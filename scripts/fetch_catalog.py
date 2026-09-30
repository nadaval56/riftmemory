"""משיכת קטלוגים של רעידות לאורך שנים, לעמוד "מכשירי מדידה".

1. המכון הגיאולוגי: ה-API של האתר שומר רק כמה חודשים אחורה, אבל עם רעידות קטנות.
2. USGS ComCat (נחלת הכלל): מתחילת התקופה המכשירית, רעידות 2.5 ומעלה באזור.

המקור: ה-API של אתר המכון (eq.gsi.gov.il/api/earthquakes), אותו API שמשמש את הפס החי.
נמשכות רעידות מקומיות בלבד (id שמתחיל ב-gsi_loc), מגניטודה MIN_MAG ומעלה,
בתיבה של השבר ושוליו. הבקשות נשלחות לפי שנה; אם ה-API מסמן isLimited, הטווח מתחלק.

פלט: data/catalog/gsi.json. רץ ב-Actions (fetch.yml, task "catalog"), כי בסביבת
הפיתוח אין גישה לאתר המכון.
"""

import datetime as dt
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "catalog" / "gsi.json"
API = "https://eq.gsi.gov.il/api/earthquakes/"
UA = {"User-Agent": "riftmemory/0.1 (https://github.com/nadaval56/riftmemory)"}
FMT = "%Y-%m-%dT%H:%M:%S.000Z"

START_YEAR = 1900
MIN_MAG = 2.5
BOX = dict(min_lat=28.0, max_lat=34.8, min_lon=33.8, max_lon=37.0)


def query(start, end, depth=0):
    """כל הרעידות בטווח. מתחלק לשניים אם התשובה מוגבלת."""
    params = {"startDate": start.strftime(FMT), "endDate": end.strftime(FMT), "minMagnitude": MIN_MAG}
    for attempt in range(4):
        try:
            r = requests.get(API, params=params, headers=UA, timeout=90)
            r.raise_for_status()
            data = r.json()
            break
        except Exception as exc:  # noqa: BLE001
            print(f"  retry {attempt + 1}: {exc!r}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    else:
        raise RuntimeError(f"failed {start}..{end}")
    if data.get("isLimited") and depth < 8 and (end - start) > dt.timedelta(days=2):
        mid = start + (end - start) / 2
        return query(start, mid, depth + 1) + query(mid, end, depth + 1)
    return data.get("earthquakes") or []


def keep(q):
    return (
        str(q.get("id", "")).startswith("gsi_loc")
        and q.get("m_type") in (None, "", "earthquake")
        and BOX["min_lat"] <= q["latitude"] <= BOX["max_lat"]
        and BOX["min_lon"] <= q["longitude"] <= BOX["max_lon"]
    )


USGS_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"
USGS_OUT = ROOT / "data" / "catalog" / "usgs.json"


def fetch_usgs(now):
    rows = {}
    for start_year in range(1900, now.year + 1, 10):
        start = f"{start_year}-01-01"
        end = f"{min(start_year + 10, now.year + 1)}-01-01"
        r = requests.get(USGS_API, headers=UA, timeout=120, params=dict(
            format="geojson", starttime=start, endtime=end, minmagnitude=MIN_MAG,
            minlatitude=BOX["min_lat"], maxlatitude=BOX["max_lat"],
            minlongitude=BOX["min_lon"], maxlongitude=BOX["max_lon"], orderby="time-asc", limit=20000))
        r.raise_for_status()
        for f in r.json()["features"]:
            p, (lon, lat, depth) = f["properties"], f["geometry"]["coordinates"]
            if p.get("type") != "earthquake" or p.get("mag") is None:
                continue
            t = dt.datetime.fromtimestamp(p["time"] / 1000, dt.timezone.utc)
            rows[f["id"]] = {
                "id": f["id"], "t": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "lat": round(lat, 3), "lon": round(lon, 3),
                "depth": None if depth is None else round(depth, 1),
                "mag": round(p["mag"], 2), "mag_type": p.get("magType"),
                "place": p.get("place"), "felt": p.get("felt"), "url": p.get("url"),
            }
        print("usgs", start_year, len(rows))
        time.sleep(1)
    out = sorted(rows.values(), key=lambda e: e["t"])
    USGS_OUT.write_text(json.dumps({
        "fetched_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "USGS ComCat (earthquake.usgs.gov/fdsnws/event/1), נחלת הכלל",
        "min_magnitude": MIN_MAG, "box": BOX, "count": len(out), "events": out,
    }, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(out)} events -> {USGS_OUT.relative_to(ROOT)}")


def main():
    now = dt.datetime.now(dt.timezone.utc)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        fetch_usgs(now)
    except Exception as exc:  # noqa: BLE001
        print(f"usgs failed: {exc!r}", file=sys.stderr)
    events, per_year = {}, {}
    for year in range(max(START_YEAR, now.year - 2), now.year + 1):
        start = dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc)
        end = min(dt.datetime(year + 1, 1, 1, tzinfo=dt.timezone.utc), now)
        got = query(start, end)
        n = 0
        for q in got:
            if keep(q) and q["id"] not in events:
                events[q["id"]] = {
                    "id": q["id"],
                    "t": q["timestamp"][:19] + "Z",
                    "lat": round(q["latitude"], 3),
                    "lon": round(q["longitude"], 3),
                    "depth": None if q.get("depth") is None else round(q["depth"], 1),
                    "mag": round(q["magnitude"], 2),
                    "region": q.get("region"),
                    "felt": q.get("felt") or None,
                }
                n += 1
        per_year[year] = n
        if n:
            print(year, n)
        time.sleep(0.5)
    rows = sorted(events.values(), key=lambda e: e["t"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "fetched_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "המכון הגיאולוגי לישראל, eq.gsi.gov.il (API האתר)",
        "min_magnitude": MIN_MAG,
        "box": BOX,
        "first": rows[0]["t"] if rows else None,
        "count": len(rows),
        "events": rows,
    }, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(rows)} events -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
