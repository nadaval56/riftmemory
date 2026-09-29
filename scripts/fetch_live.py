"""משיכת רעידות אחרונות (פרק 4.2–4.3). פלט: data/live/latest.json (פרק 5.2).

סדר המקורות: המכון הגיאולוגי, ואם נכשל USGS, ואם נכשל EMSC.
אם כל המקורות נכשלו, הקובץ הקודם נשאר כמו שהוא (כולל fetched_at),
והסקריפט יוצא בקוד 0 כדי שהבנייה תמשיך עם הנתונים הקודמים.

נמשכות רעידות מ-30 הימים האחרונים (למפה בדף הבית), מגניטודה 2.0 ומעלה,
בתיבה 27–36 צפון, 32–38 מזרח.
"""

import datetime as dt
import json
import sys
from pathlib import Path

import requests

import echo

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "live" / "latest.json"

USER_AGENT = "riftmemory/0.1 (https://github.com/nadaval56/riftmemory)"
TIMEOUT = 30
DAYS = 30
MAX_EVENTS = 300
BOX = dict(min_lat=27.0, max_lat=36.0, min_lon=32.0, max_lon=38.0)
MIN_MAG = 2.0

session = requests.Session()
session.headers["User-Agent"] = USER_AGENT


def iso_z(t):
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_time(s):
    t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return t


def in_box(lat, lon):
    return BOX["min_lat"] <= lat <= BOX["max_lat"] and BOX["min_lon"] <= lon <= BOX["max_lon"]


def record(time, lat, lon, depth, mag, mag_type, place=None, place_he=None, source_id=None):
    return {
        "time_utc": iso_z(time),
        "lat": round(float(lat), 4),
        "lon": round(float(lon), 4),
        "depth_km": None if depth is None else round(float(depth), 1),
        "magnitude": round(float(mag), 1),
        "mag_type": mag_type,
        "place_he": place_he,
        "place": place,
        "source_id": source_id,
    }


# --- המכון הגיאולוגי ----------------------------------------------------

GSI_API = "https://eq.gsi.gov.il/api/earthquakes/"


# שמות האזורים ב-API של המכון הם באנגלית. תרגום רק לשמות מוכרים; אחרת נשאר המקור.
GSI_REGIONS_HE = {
    "Arava": "הערבה",
    "Dead-Sea": "ים המלח",
    "Dead Sea": "ים המלח",
    "Judea-Samaria": "יהודה ושומרון",
    "Jordan-Valley": "בקעת הירדן",
    "Jordan Valley": "בקעת הירדן",
    "Kinneret": "הכינרת",
    "Galilee": "הגליל",
    "Hula": "החולה",
    "Carmel": "הכרמל",
    "Gulf-of-Eilat": "מפרץ אילת",
    "Gulf of Eilat": "מפרץ אילת",
    "Gulf-of-Aqaba": "מפרץ אילת",
    "Negev": "הנגב",
    "Sinai": "סיני",
    "Jordan": "ירדן",
    "Lebanon": "לבנון",
    "Syria": "סוריה",
    "Cyprus": "קפריסין",
    "Turkey": "טורקיה",
    "Egypt": "מצרים",
    "E.Mediter.-Sea": "מזרח הים התיכון",
    "Dead-Sea-Basin": "אגן ים המלח",
    "E.Shomron": "מזרח השומרון",
    "Elat-Deep": "מפרץ אילת",
    "Aragonese-Deep": "מפרץ אילת",
    "Northern-Jordan": "צפון ירדן",
    "Palmira": "תדמור (סוריה)",
    "Syria2": "סוריה",
    "Yamune": "ימונה (לבנון)",
    "W.-Sirhan": "ואדי סירחאן",
    "Suez": "מפרץ סואץ",
}


def fetch_gsi(start, end):
    resp = session.get(GSI_API, timeout=TIMEOUT, params={
        "startDate": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "endDate": end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "minMagnitude": MIN_MAG,
    })
    resp.raise_for_status()
    return parse_gsi(resp.json())


def parse_gsi(data):
    out = []
    for q in data["earthquakes"]:
        if q.get("m_type", "earthquake") != "earthquake" or q.get("magnitude") is None:
            continue
        region = (q.get("region") or "").strip() or None
        out.append(record(parse_time(q["timestamp"]), q["latitude"], q["longitude"], q.get("depth"),
                          q["magnitude"], None, place=region,
                          place_he=GSI_REGIONS_HE.get(region), source_id=q.get("id")))
    return out


# --- USGS ---------------------------------------------------------------

USGS_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"


def fetch_usgs(start, end):
    resp = session.get(USGS_API, timeout=TIMEOUT, params=dict(
        format="geojson", starttime=iso_z(start), endtime=iso_z(end),
        minlatitude=BOX["min_lat"], maxlatitude=BOX["max_lat"],
        minlongitude=BOX["min_lon"], maxlongitude=BOX["max_lon"],
        minmagnitude=MIN_MAG, orderby="time", limit=MAX_EVENTS,
    ))
    resp.raise_for_status()
    out = []
    for f in resp.json()["features"]:
        p, (lon, lat, depth) = f["properties"], f["geometry"]["coordinates"]
        if p.get("type") != "earthquake" or p.get("mag") is None:
            continue
        t = dt.datetime.fromtimestamp(p["time"] / 1000, dt.timezone.utc)
        out.append(record(t, lat, lon, depth, p["mag"], p.get("magType"), place=p.get("place"), source_id=f["id"]))
    return out


# --- EMSC ---------------------------------------------------------------

EMSC_API = "https://www.seismicportal.eu/fdsnws/event/1/query"


def fetch_emsc(start, end):
    resp = session.get(EMSC_API, timeout=TIMEOUT, params=dict(
        format="json", start=iso_z(start), end=iso_z(end),
        minlat=BOX["min_lat"], maxlat=BOX["max_lat"],
        minlon=BOX["min_lon"], maxlon=BOX["max_lon"],
        minmag=MIN_MAG, orderby="time", limit=MAX_EVENTS,
    ))
    resp.raise_for_status()
    out = []
    for f in resp.json()["features"]:
        p = f["properties"]
        if p.get("evtype") not in (None, "ke") or p.get("mag") is None:
            continue
        place = (p.get("flynn_region") or "").title() or None
        out.append(record(parse_time(p["time"]), p["lat"], p["lon"], p.get("depth"),
                          p["mag"], p.get("magtype"), place=place, source_id=p.get("unid")))
    return out


SOURCES = [("gsi", fetch_gsi), ("usgs", fetch_usgs), ("emsc", fetch_emsc)]


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None  # לבדיקה: fetch_live.py usgs
    end = dt.datetime.now(dt.timezone.utc)
    start = end - dt.timedelta(days=DAYS)

    for name, fn in SOURCES:
        if only and name != only:
            continue
        try:
            events = [q for q in fn(start, end) if in_box(q["lat"], q["lon"]) and q["magnitude"] >= MIN_MAG]
        except Exception as exc:  # noqa: BLE001 — כל כשל עובר למקור הבא
            print(f"{name}: failed: {exc!r}")
            continue
        events.sort(key=lambda q: q["time_utc"], reverse=True)
        events = events[:MAX_EVENTS]
        # segment ו-echo מחושבים כאן לפי הרעידות שפורסמו, ומחושבים מחדש בזמן הבנייה
        from build_events import load_events
        published = [e for e in load_events() if e["status"] == "published"]
        echo.annotate(events, published, echo.load_segments())
        latest = {"fetched_at": iso_z(end), "source": name, "events": events}
        OUT.write_text(json.dumps(latest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{name}: saved {len(events)} events")
        return

    print("all sources failed; keeping previous latest.json")


if __name__ == "__main__":
    main()
