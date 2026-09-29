"""שיוך רעידה חיה למקטע ובניית "הד היסטורי" (פרק 7).

ההד מציין עובדה גיאוגרפית בלבד: באותו מקטע קרתה רעידה היסטורית.
משפטים מתבנית קבועה בלבד. בלי מסקנות ובלי שום ניסוח חיזויי.

המקטעים מוגדרים לפי קווי העתקים אמיתיים (data/faults.geojson, מתוך GEM
Global Active Faults, EMME), ולא לפי מלבנים. רעידה משויכת למקטע של ההעתק
הקרוב אליה, אם המרחק עד SEGMENT_KM. עד NEAR_KM היא "קרובה" (בלי שיוך),
ומעבר לזה היא distant. רק מקטעים עם approved: true משמשים לשיוך; רעידה
שההעתק הקרוב אליה שייך למקטע שלא אושר מקבלת segment=null ובלי הד.

הרצה ישירה מעדכנת את שדות segment ו-echo ב-data/live/latest.json.
"""

import json
import math
from pathlib import Path

import fmt

ROOT = Path(__file__).resolve().parent.parent
SEGMENTS = ROOT / "data" / "segments.json"
FAULTS = ROOT / "data" / "faults.geojson"
LATEST = ROOT / "data" / "live" / "latest.json"

DISTANT = "distant"
SEGMENT_KM = 20
NEAR_KM = 50

TEXT_NONE = "אין רעידה היסטורית מתועדת באתר מהאזור הזה."
# נוסח המדריך היה "הרעידה רחוקה משבר ים המלח.", אבל רעידות בלבנון ובסוריה נמצאות
# על המשך אותה מערכת שברים. לכן הניסוח מתייחס למקטעים שהאתר מסמן.
TEXT_DISTANT = "הרעידה רחוקה ממקטעי השבר שמסומנים באתר."
TEXT_OUTSIDE = "הרעידה מחוץ למקטעי השבר שמסומנים באתר."


def load_segments():
    """המקטעים, כל אחד עם רשימת הקווים שלו (lines: רשימות של [lon, lat])."""
    segments = json.loads(SEGMENTS.read_text(encoding="utf-8"))
    faults = json.loads(FAULTS.read_text(encoding="utf-8"))["features"]
    for seg in segments:
        seg["lines"] = [f["geometry"]["coordinates"] for f in faults if f["properties"]["segment"] == seg["id"]]
    return segments


def _km_to_line(lat, lon, line):
    """מרחק משוער בק"מ מנקודה לקו שבור (הטלה מקומית שווה-מרחקים)."""
    kx = 111.32 * math.cos(math.radians(lat))
    ky = 110.57
    best = float("inf")
    for (lon1, lat1), (lon2, lat2) in zip(line, line[1:]):
        ax, ay = (lon1 - lon) * kx, (lat1 - lat) * ky
        bx, by = (lon2 - lon) * kx, (lat2 - lat) * ky
        dx, dy = bx - ax, by - ay
        t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best


def nearest_segment(lat, lon, segments):
    """(המקטע של ההעתק הקרוב ביותר, המרחק בק"מ)."""
    best, dist = None, float("inf")
    for seg in segments:
        for line in seg.get("lines", []):
            d = _km_to_line(lat, lon, line)
            if d < dist:
                best, dist = seg, d
    return best, dist


def classify(lat, lon, segments):
    """(segment, kind): kind הוא "in", "unapproved", "near" או "far"."""
    seg, dist = nearest_segment(lat, lon, segments)
    if seg is not None and dist <= SEGMENT_KM:
        return (seg["id"], "in") if seg.get("approved") else (None, "unapproved")
    if dist <= NEAR_KM:
        return None, "near"
    return DISTANT, "far"


def segment_for(lat, lon, segments):
    return classify(lat, lon, segments)[0]


def _when(e):
    """ "ב-1837", "ב-31 לפנה״ס", ולתאריך לא ודאי "בסביבות 130"."""
    y = fmt.year(e["date"]["year"])
    if e["date"].get("certainty") in ("approximate", "disputed"):
        return f"בסביבות {y}"
    return f"ב-{y}"


def _and(phrase):
    """ "ב-1837" -> "וב-1837", "בסביבות 130" -> "ובסביבות 130"."""
    return "ו" + phrase


def echo_for(segment, events, limit=3):
    """ההד לרעידה במקטע נתון. events: הרעידות ההיסטוריות שמוצגות באתר."""
    if segment is None:
        return None
    if segment == DISTANT:
        return {"event_ids": [], "text": TEXT_DISTANT}
    matches = [
        e for e in events
        if e["location"].get("segment") == segment and not e["location"].get("distant")
    ]
    matches.sort(key=lambda e: e["date"]["year"])
    matches = matches[:limit]
    ids = [e["id"] for e in matches]
    if not matches:
        text = TEXT_NONE
    elif len(matches) == 1:
        e = matches[0]
        text = f"באזור הזה נקרע השבר גם {_when(e)}. {e['short_title']}"
    else:
        parts = [_when(e) for e in matches]
        text = f"זה האזור שנקרע {', '.join(parts[:-1])} {_and(parts[-1])}."
    return {"event_ids": ids, "text": text}


def annotate(live_events, events, segments):
    """מוסיף segment ו-echo לכל רעידה חיה."""
    for q in live_events:
        seg, kind = classify(q["lat"], q["lon"], segments)
        q["segment"] = seg
        q["echo"] = {"event_ids": [], "text": TEXT_OUTSIDE} if kind == "near" else echo_for(seg, events)
    return live_events


def main():
    from build_events import load_events

    events = [e for e in load_events() if e["status"] == "published"]
    latest = json.loads(LATEST.read_text(encoding="utf-8"))
    annotate(latest["events"], events, load_segments())
    LATEST.write_text(json.dumps(latest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"annotated {len(latest['events'])} live events")


if __name__ == "__main__":
    main()
