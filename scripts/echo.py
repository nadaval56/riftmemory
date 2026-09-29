"""שיוך רעידה חיה למקטע ובניית "הד היסטורי" (פרק 7).

ההד מציין עובדה גיאוגרפית בלבד: באותו מקטע קרתה רעידה היסטורית.
משפטים מתבנית קבועה בלבד. בלי מסקנות ובלי שום ניסוח חיזויי.

רק מקטעים עם approved: true משמשים לשיוך. נקודה שנמצאת רק במקטע שלא
אושר מקבלת segment=null ובלי הד. נקודה מחוץ לכל המקטעים ורחוקה מהם
יותר מ-NEAR_KM היא distant. נקודה מחוץ למקטעים אבל קרובה אליהם (למשל
בהרי יהודה ושומרון) מקבלת segment=null ומשפט ניטרלי, ולא "רחוקה מהשבר".

הרצה ישירה מעדכנת את שדות segment ו-echo ב-data/live/latest.json.
"""

import json
import math
from pathlib import Path

import fmt

ROOT = Path(__file__).resolve().parent.parent
SEGMENTS = ROOT / "data" / "segments.json"
LATEST = ROOT / "data" / "live" / "latest.json"

DISTANT = "distant"
NEAR_KM = 50

TEXT_NONE = "אין רעידה היסטורית מתועדת באתר מהאזור הזה."
TEXT_DISTANT = "הרעידה רחוקה משבר ים המלח."
TEXT_OUTSIDE = "הרעידה מחוץ למקטעי השבר שמסומנים באתר."


def load_segments():
    return json.loads(SEGMENTS.read_text(encoding="utf-8"))


def in_bbox(lat, lon, bbox):
    min_lat, min_lon, max_lat, max_lon = bbox
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def km_to_bbox(lat, lon, bbox):
    """מרחק משוער בק"מ מנקודה למלבן (0 בתוכו)."""
    min_lat, min_lon, max_lat, max_lon = bbox
    dlat = max(min_lat - lat, 0, lat - max_lat)
    dlon = max(min_lon - lon, 0, lon - max_lon)
    return math.hypot(dlat * 111.0, dlon * 111.0 * math.cos(math.radians(lat)))


def classify(lat, lon, segments):
    """(segment, kind): kind הוא "in", "unapproved", "near" או "far"."""
    unapproved_hit = False
    for seg in segments:
        if in_bbox(lat, lon, seg["bbox"]):
            if seg.get("approved"):
                return seg["id"], "in"
            unapproved_hit = True
    if unapproved_hit:
        return None, "unapproved"
    if segments and min(km_to_bbox(lat, lon, s["bbox"]) for s in segments) <= NEAR_KM:
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
