"""מייצר את האתר הסטטי בתיקייה site/ מתוך content/, data/, templates/ ו-static/.

ברירת מחדל: רק רעידות עם status: published נבנות (כלל 8).
python scripts/build_site.py --drafts בונה גם טיוטות, עם סימון "טיוטה"
ו-noindex, לתצוגה מקומית בלבד.

משתני סביבה:
  SITE_URL   כתובת האתר המלאה, בלי / בסוף (ל-sitemap ול-Open Graph)
  BASE_PATH  הנתיב שהאתר יושב בו, למשל /riftmemory (ריק בדומיין משלו)
"""

import argparse
import datetime as dt
import json
import os
import re
import shutil
from pathlib import Path
from zoneinfo import ZoneInfo

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

import echo
import fmt
import timeline
from build_events import load_events

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
TZ = ZoneInfo("Asia/Jerusalem")

SITE_URL = os.environ.get("SITE_URL", "https://nadaval56.github.io/riftmemory").rstrip("/")
BASE_PATH = os.environ.get("BASE_PATH", "/riftmemory").rstrip("/")

SITE_NAME = "השבר"
SITE_TAGLINE = "רעידות האדמה בארץ ישראל: 3,000 שנות היסטוריה, ופס חי מהסייסמוגרפים"

SEGMENT_NAMES_EXTRA = {echo.DISTANT: "רחוק"}

WIKI_LICENSE = {
    "label": "CC BY-SA 4.0",
    "url": "https://creativecommons.org/licenses/by-sa/4.0/deed.he",
}


# --- תוכן ---------------------------------------------------------------

HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)


def split_sections(body):
    """גוף ה-Markdown -> רשימת (כותרת, html). חלק שכולו הערות נשאר עם html ריק."""
    sections = []
    for chunk in re.split(r"^## ", body, flags=re.M):
        if not chunk.strip():
            continue
        title, _, text = chunk.partition("\n")
        text = HTML_COMMENT.sub("", text).strip()
        html = markdown.markdown(text, extensions=["extra"]) if text else ""
        sections.append({"title": title.strip(), "html": html})
    return sections


def evidence_kind(e):
    """הראיה החזקה ביותר, לצבע בציר הזמן ובמפה."""
    ev = e.get("evidence") or {}
    if ev.get("instrumental"):
        return "instrumental"
    if ev.get("archaeology"):
        return "archaeology"
    return "texts"


# --- נתונים חיים --------------------------------------------------------

def load_live():
    path = ROOT / "data" / "live" / "latest.json"
    live = json.loads(path.read_text(encoding="utf-8"))
    for q in live["events"]:
        q["time"] = dt.datetime.fromisoformat(q["time_utc"].replace("Z", "+00:00"))
    return live


def relative_hours(t, now):
    """ "לפני 3 שעות" וכו'. בדף עצמו JS מעדכן את זה לפי השעון של הקורא."""
    minutes = int((now - t).total_seconds() // 60)
    if minutes < 60:
        return "לפני פחות משעה"
    hours = minutes // 60
    if hours == 1:
        return "לפני שעה"
    if hours == 2:
        return "לפני שעתיים"
    if hours < 24:
        return f"לפני {hours} שעות"
    days = hours // 24
    if days == 1:
        return "אתמול"
    if days == 2:
        return "לפני יומיים"
    return f"לפני {days} ימים"


def live_label(q, segment_names):
    if q.get("place_he"):
        return q["place_he"]
    seg = q.get("segment")
    if seg and seg != echo.DISTANT and seg in segment_names:
        return segment_names[seg]
    return q.get("place") or segment_names.get(seg, "")


# --- היום בהיסטוריה -----------------------------------------------------

def hebrew_month_day(y, m, d):
    from convertdate import hebrew
    _, hm, hd = hebrew.from_gregorian(y, m, d)
    return hm, hd


def today_in_history(events, today):
    """התאמה לתאריך הלועזי או העברי של היום. אחרת בחירה קבועה לפי מספר היום בשנה."""
    today_heb = hebrew_month_day(today.year, today.month, today.day)
    for e in events:
        d = e["date"]
        if d.get("certainty") == "disputed" or not (d.get("month") and d.get("day")):
            continue
        if (d["month"], d["day"]) == (today.month, today.day):
            return e, "gregorian"
        # התאריך העברי מחושב רק לתאריכים בלוח הגרגוריאני (מ-1583). תאריכים קודמים
        # במקורות הם לפי הלוח היוליאני, והמרה שלהם תיתן יום עברי שגוי.
        if d.get("hebrew_date") and d["year"] >= 1583:
            if hebrew_month_day(d["year"], d["month"], d["day"]) == today_heb:
                return e, "hebrew"
    if not events:
        return None, None
    doy = today.timetuple().tm_yday
    return events[(doy + today.year) % len(events)], "random"


# --- בנייה --------------------------------------------------------------

def make_env():
    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters.update(
        year=fmt.year,
        event_date=fmt.event_date,
        year_label=fmt.event_year_label,
        number=fmt.number,
        magnitude=fmt.magnitude,
        mag_type=fmt.mag_type,
        mag_basis=fmt.mag_basis,
    )
    env.globals.update(
        base=BASE_PATH,
        site_url=SITE_URL,
        site_name=SITE_NAME,
        site_tagline=SITE_TAGLINE,
    )
    return env


def write(path, html):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def map_data(events, live, segments):
    return {
        "segments": [
            {"id": s["id"], "name": s["name_he"], "bbox": s["bbox"]}
            for s in segments if s.get("approved")
        ],
        "events": [
            {
                "id": e["id"],
                "title": e["short_title"],
                "year": fmt.event_year_label(e),
                "lat": e["location"]["lat"],
                "lon": e["location"]["lon"],
                "kind": evidence_kind(e),
                "url": f"{BASE_PATH}/events/{e['id']}/",
            }
            for e in events
            if e["location"].get("lat") is not None and e["location"].get("lon") is not None
        ],
        "live": [
            {
                "lat": q["lat"],
                "lon": q["lon"],
                "mag": q["magnitude"],
                "time_utc": q["time_utc"],
                "label": q["label"],
            }
            for q in live["events"]
        ],
    }


def build(drafts=False):
    now = dt.datetime.now(dt.timezone.utc)
    today = now.astimezone(TZ).date()

    all_events = load_events()
    events = [e for e in all_events if drafts or e["status"] == "published"]
    segments = echo.load_segments()
    segment_names = {s["id"]: s["name_he"] for s in segments} | SEGMENT_NAMES_EXTRA

    live = load_live()
    echo.annotate(live["events"], events, segments)
    for q in live["events"]:
        q["ago"] = relative_hours(q["time"], now)
        q["label"] = live_label(q, segment_names)

    by_id = {e["id"]: e for e in events}
    for e in events:
        e["sections"] = split_sections(e["body"])
        e["kind"] = evidence_kind(e)
        seg = e["location"].get("segment")
        e["segment_name"] = segment_names.get(seg) if seg else None
        e["same_segment"] = [
            o for o in events
            if o is not e and seg and seg != echo.DISTANT and o["location"].get("segment") == seg
        ]
        e["live_nearby"] = [q for q in live["events"] if seg and q.get("segment") == seg]

    env = make_env()
    common = dict(drafts=drafts, built_at=now, segment_names=segment_names)

    if SITE.exists():
        shutil.rmtree(SITE)
    shutil.copytree(ROOT / "static", SITE / "static", ignore=shutil.ignore_patterns(".gitkeep"))

    pages = []

    # דף הבית
    week_ago = now - dt.timedelta(days=7)
    latest = live["events"][0] if live["events"] else None
    quiet = latest is None or latest["time"] < week_ago
    featured, featured_reason = today_in_history(events, today)
    month_ago = now - dt.timedelta(days=30)
    live_month = dict(live, events=[q for q in live["events"] if q["time"] >= month_ago])
    write(SITE / "index.html", env.get_template("index.html").render(
        **common,
        page_path="/",
        latest=latest,
        quiet=quiet,
        live=live,
        featured=featured,
        featured_reason=featured_reason,
        today=today,
        events=events,
        map_data=map_data(events, live_month, segments),
    ))
    pages.append("/")

    # דפי רעידות
    tpl = env.get_template("event.html")
    for e in events:
        path = f"/events/{e['id']}/"
        write(SITE / "events" / e["id"] / "index.html", tpl.render(
            **common,
            page_path=path,
            e=e,
            by_id=by_id,
            map_data=map_data([e], dict(live, events=e["live_nearby"]), segments),
        ))
        pages.append(path)

    # ציר הזמן
    write(SITE / "timeline" / "index.html", env.get_template("timeline.html").render(
        **common,
        page_path="/timeline/",
        events=events,
        svg_h=timeline.horizontal(events, BASE_PATH),
        svg_v=timeline.vertical(events, BASE_PATH),
    ))
    pages.append("/timeline/")

    # על האתר
    write(SITE / "about" / "index.html", env.get_template("about.html").render(
        **common,
        page_path="/about/",
        license=WIKI_LICENSE,
    ))
    pages.append("/about/")

    write(SITE / "404.html", env.get_template("404.html").render(**common, page_path="/404.html"))

    # sitemap ו-robots
    if drafts:
        write(SITE / "robots.txt", "User-agent: *\nDisallow: /\n")
    else:
        write(SITE / "sitemap.xml", env.get_template("sitemap.xml").render(
            pages=pages, lastmod=today.isoformat()))
        write(SITE / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")

    print(f"built {len(pages)} pages ({len(events)} events{', with drafts' if drafts else ''}) -> {SITE}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--drafts", action="store_true", help="לבנות גם טיוטות (תצוגה מקומית בלבד)")
    build(drafts=parser.parse_args().drafts)


if __name__ == "__main__":
    main()
