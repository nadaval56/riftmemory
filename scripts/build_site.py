"""מייצר את האתר הסטטי בתיקייה site/ מתוך content/, data/, templates/ ו-static/.

ברירת מחדל: רק רעידות עם status: published נבנות (כלל 8).
python scripts/build_site.py --drafts בונה גם טיוטות, עם סימון "טיוטה"
ו-noindex, לתצוגה מקומית בלבד.

אם ב-data/site.json מוגדר "show_drafts": true, גם הבנייה הציבורית כוללת
טיוטות: כל דף טיוטה מסומן בבירור, מקבל noindex, ולא נכנס ל-sitemap.

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
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import markdown
import yaml
from html import escape
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

import echo
import fmt
import charts
import timeline
from build_events import load_events, read_event

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
TZ = ZoneInfo("Asia/Jerusalem")

# בבנייה ב-Actions הערכים מגיעים מהגדרות GitHub Pages (configure-pages). ברירת המחדל: הדומיין של האתר.
SITE_URL = os.environ.get("SITE_URL") or "https://quake.co.il"
# GitHub Pages מחזיר http:// לדומיין מותאם עד שתעודת ה-HTTPS מונפקת; האתר תמיד מוגש ב-https
SITE_URL = re.sub(r"^http://", "https://", SITE_URL.rstrip("/"))
BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")

SITE_NAME = "רעידת אדמה"
SITE_TAGLINE = "רעידות אדמה היסטוריות בשבר הסורי-אפריקני"

SEGMENT_NAMES_EXTRA = {echo.DISTANT: "רחוק"}

WIKI_LICENSE = {
    "label": "CC BY-SA 4.0",
    "url": "https://creativecommons.org/licenses/by-sa/4.0/deed.he",
}


# --- תמונות ---------------------------------------------------------------

# פרטי התמונות (כיתוב, קרדיט, רישיון) ב-data/images.yaml; הקבצים ב-static/img/photos/.
# בגוף ה-Markdown: [[fig:<id>]] בשורה נפרדת, או כמה מזהים מופרדים ברווח (קבוצה).
IMAGES = yaml.safe_load((ROOT / "data" / "images.yaml").read_text(encoding="utf-8")) or {}
PHOTOS = ROOT / "static" / "img" / "photos"
LICENSE_URLS = {
    "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC BY 2.0": "https://creativecommons.org/licenses/by/2.0/deed.he",
    "CC BY 2.5": "https://creativecommons.org/licenses/by/2.5/deed.he",
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/deed.he",
    "CC BY-SA 2.0": "https://creativecommons.org/licenses/by-sa/2.0/deed.he",
    "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/deed.he",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/deed.he",
}
FIG_MARK = re.compile(r"<p>\[\[fig:([^\]]+)\]\]</p>")


def image_credit(img):
    """שורת קרדיט: מי, רישיון (עם קישור), ודף המקור."""
    lic = escape(img["license"])
    if img["license"] in LICENSE_URLS:
        lic = f'<a href="{LICENSE_URLS[img["license"]]}" rel="license">{lic}</a>'
    src = f' · <a href="{escape(img["source"])}">ויקישיתוף</a>' if img.get("source") else ""
    return f'{escape(img["credit"])} · {lic}{src}'


def figure_html(ids):
    """<figure> לתמונה אחת, או קבוצה של כמה תמונות זו לצד זו."""
    from PIL import Image
    figs = []
    for key in ids.split():
        img = IMAGES.get(key)
        path = PHOTOS / f"{key}.webp"
        if img is None:
            raise SystemExit(f"תמונה לא מוגדרת ב-data/images.yaml: {key}")
        if not path.exists():
            print(f"warning: missing image file {path.name}; skipped")
            continue
        w, h = Image.open(path).size
        url = f"{BASE_PATH}/static/img/photos/{key}"
        figs.append(
            f'<figure class="photo">'
            f'<a href="{url}.webp" class="photo-link"><img src="{url}.webp" '
            f'srcset="{url}-640.webp 640w, {url}.webp {w}w" sizes="(max-width: 760px) 100vw, 680px" '
            f'width="{w}" height="{h}" alt="{escape(img["alt"])}" loading="lazy" decoding="async"></a>'
            f'<figcaption>{escape(img["caption"])} <span class="credit">{image_credit(img)}</span></figcaption>'
            f'</figure>')
    if not figs:
        return ""
    if len(figs) == 1:
        return figs[0]
    return f'<div class="photo-group n{len(figs)}">{"".join(figs)}</div>'


def image_credits():
    """רשימת כל התמונות לדף "אודות"."""
    return [{"key": k, "caption": v["caption"], "credit": image_credit(v)} for k, v in IMAGES.items()
            if (PHOTOS / f"{k}.webp").exists()]


# --- תוכן ---------------------------------------------------------------

HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)


FOOTNOTES = re.compile(r'<div class="footnote">.*</div>\s*$', re.S)


def split_sections(body):
    """גוף ה-Markdown -> (רשימת {title, html}, html של הערות השוליים).

    ה-Markdown מומר כולו בבת אחת, כדי שהערות השוליים ([^x]) יעבדו בין חלקים.
    חלק שכולו הערות HTML נשאר עם html ריק.
    """
    text = HTML_COMMENT.sub("", body)
    html = markdown.markdown(text, extensions=["extra"], extension_configs={
        "footnotes": {"BACKLINK_TITLE": "חזרה לטקסט"}})
    html = FIG_MARK.sub(lambda m: figure_html(m.group(1)), html)
    notes = ""
    m = FOOTNOTES.search(html)
    if m:
        notes, html = m.group(0), html[:m.start()]
        # בלי חיצי "חזרה לטקסט": ההערה נפתחת בחלון צף, והרשימה בתחתית היא ביבליוגרפיה
        notes = re.sub(r'(&#160;)?<a class="footnote-backref"[^>]*>.*?</a>', "", notes)
        notes = notes.replace("<hr />", "")
    sections = []
    parts = re.split(r"<h2[^>]*>(.*?)</h2>", html)
    for title, content in zip(parts[1::2], parts[2::2]):
        sections.append({"title": title.strip(), "html": content.strip()})
    return sections, notes


# קישורים למילון המונחים: המופע הראשון של כל מונח בגוף הדף מקשר להגדרה שלו (/glossary/#...).
# תחיליות עבריות (ו, ה, ב, ל, מ, ש, כ) מותרות לפני המונח; הסיומות מוגבלות, כדי שלא יתפסו
# מילים אחרות ("מוקדמות", "העתקה"). לא בתוך קישורים, כותרות, הערות שוליים או קוד.
# "העתק" במובן copy יקושר בטעות למילון: בתוכן כותבים במקומו "עותק" או "כפילות".
PREFIX = r"(?<![\u0590-\u05FF\w])(?:[והבלמשכ]{0,3})"
END = r"(?![\u0590-\u05FF\w])"
GLOSSARY_TERMS = [
    ("hypocenter", PREFIX + r"מוקד(?:ו|ה|ים)?" + END),
    ("fault", PREFIX + r"העתק(?:י|ים)?" + END),
    ("intensity", PREFIX + r"עוצמ(?:ה|ת)" + END),
    ("aftershocks", PREFIX + r"רעיד(?:ה|ת|ות) ה?משנה" + END),
    ("foreshocks", PREFIX + r"רעיד(?:ה|ות) ה?מקדימ(?:ה|ות)" + END),
    ("mainshock", PREFIX + r"רעידה ראשית" + END),
    ("tsunami", PREFIX + r"צונאמי" + END),
    ("liquefaction", PREFIX + r"התנזלות" + END),
    ("seismogram", PREFIX + r"סייסמוגרמ(?:ה|ות)" + END),
    ("strike-slip", PREFIX + r"(?:תזוזה|תנועה) אופקית" + END),
]
SKIP_TAGS = {"a", "h1", "h2", "h3", "h4", "h5", "h6", "sup", "code", "figcaption", "blockquote"}


def glossary_links(htmls):
    """מקבל רשימת קטעי HTML לפי הסדר בדף ומחזיר אותם עם קישור אחד לכל מונח."""
    done, out = set(), []
    for html in htmls:
        parts, depth = re.split(r"(<[^>]+>)", html), 0
        for i, part in enumerate(parts):
            if part.startswith("<"):
                m = re.match(r"<(/?)(\w+)", part)
                if m and m.group(2).lower() in SKIP_TAGS and not part.endswith("/>"):
                    depth += -1 if m.group(1) else 1
                continue
            if depth or not part.strip():
                continue
            for key, pat in GLOSSARY_TERMS:
                if key in done:
                    continue
                m = re.search(pat, part)
                if m:
                    done.add(key)
                    part = (part[:m.start()] + f'<a class="gl-term" href="{BASE_PATH}/glossary/#{key}">'
                            + m.group(0) + "</a>" + part[m.end():])
            parts[i] = part
        out.append("".join(parts))
    return out


# כרטיס העובדות מציג שורה קצרה. הפירוט (מי העריך מה, ובאיזה מקור) עובר להערה ממוספרת
# בסוף רשימת ההערות של הדף, ונפתח בחלון הצף כמו כל הערה אחרת.
CARD_DETAILS = [
    ("loc", lambda e: e["location"].get("description_detail")),
    ("mag", lambda e: (e.get("magnitude") or {}).get("note")),
    ("deaths", lambda e: (e.get("impact") or {}).get("deaths_detail")),
]


def card_notes(e):
    """מוסיף להערות של הדף את פירוט השדות בכרטיס; מחזיר {שדה: מספר ההערה}."""
    refs = {}
    n = e["footnotes"].count("<li id=")
    items = []
    for key, get in CARD_DETAILS:
        text = get(e)
        if not text:
            continue
        n += 1
        refs[key] = n
        html = markdown.markdown(text).removeprefix("<p>").removesuffix("</p>")
        items.append(f'<li id="card-{key}">{html}</li>')
    if items:
        if "</ol>" in e["footnotes"]:
            e["footnotes"] = e["footnotes"].replace("</ol>", "\n".join(items) + "\n</ol>", 1)
        else:
            e["footnotes"] = '<div class="footnote"><ol>' + "\n".join(items) + "</ol></div>"
    return refs


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



WEEKDAYS_HE = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]


def local_time(t):
    """ "יום שלישי 23.9 · 00:59" בשעון ישראל."""
    lt = t.astimezone(TZ)
    return f"יום {WEEKDAYS_HE[lt.weekday()]} {lt.day}.{lt.month} · {lt:%H:%M}"


def quake_id(q):
    return "q-" + (q.get("source_id") or q["time_utc"].replace(":", "").replace("-", ""))


def describe_quakes(quakes, segments, segment_names):
    """פרטים לכל רעידה חיה: שעה מקומית, המרחק מקו השבר הקרוב והמקטע שלו."""
    for q in quakes:
        seg, dist = echo.nearest_segment(q["lat"], q["lon"], segments)
        q["anchor"] = quake_id(q)
        q["local"] = local_time(q["time"])
        q["fault_km"] = round(dist) if seg is not None else None
        q["fault_seg"] = segment_names.get(seg["id"]) if seg is not None else None
    return quakes


def days_summary(days):
    """תיאור מילולי של גרף הימים, ל-aria-label."""
    total = sum(n for _, n, _ in days)
    if not total:
        return "לא נרשמו רעידות."
    peak = max(days, key=lambda d: d[1])
    empty = sum(1 for _, n, _ in days if n == 0)
    return (f"בסך הכול {total} רעידות. הכי הרבה ביום אחד: {peak[1]}, ב־{peak[0]}. "
            f"{empty} ימים בלי רעידות. ימין הגרף הוא לפני 30 ימים, שמאלו היום.")


def recent_summary(quakes, today, days=30):
    """מספר רעידות לכל יום (מהישן מימין), ולפי טווחי מגניטודה."""
    counts = {}
    for q in quakes:
        d = q["time"].astimezone(TZ).date()
        counts[d] = counts.get(d, 0) + 1
    items = []
    for i in range(days - 1, -1, -1):
        d = today - dt.timedelta(days=i)
        n = counts.get(d, 0)
        items.append((f"{d.day}.{d.month}", n, f"{d.day}.{d.month}: {n} רעידות"))
    bands = [("2–2.9", 2, 3), ("3–3.9", 3, 4), ("4 ומעלה", 4, 99)]
    by_mag = [(label, sum(1 for q in quakes if lo <= q["magnitude"] < hi)) for label, lo, hi in bands]
    return items, by_mag



# --- התקופה המכשירית -------------------------------------------------------

def decades_summary(decades):
    peak = max(decades, key=lambda d: d[1])
    total = sum(n for _, n, _ in decades)
    return (f"בסך הכול {total} רעידות משנות ה־{decades[0][0]} ועד שנות ה־{decades[-1][0]}. "
            f"הכי הרבה בשנות ה־{peak[0]}: {peak[1]}. ימין הגרף הוא העשור הראשון.")


def depth_summary(near, bands):
    depths = sorted(q["depth"] for q in near if q["depth"] is not None)
    if not depths:
        return ""
    fixed = sum(1 for d in depths if d == 10)
    per_band = sorted(((sum(1 for q in near if q["depth"] is not None and lo <= q["lat"] <= hi), name)
                       for lo, hi, name in bands), reverse=True)
    busiest = f"הכי הרבה רעידות ברצועה של {per_band[0][1]}: {per_band[0][0]}. " if per_band and per_band[0][0] else ""
    upto20 = sum(1 for d in depths if d <= 20)
    return (f"{len(depths)} רעידות. {fixed} מהן רשומות בעומק של 10 ק״מ בדיוק, שהוא עומק קבוע כשאין חישוב אמין. "
            f"{upto20} עד עומק 20 ק״מ; העמוקה ביותר ב־{depths[-1]:g} ק״מ. "
            f"{busiest}הרעידות החזקות מפורטות בטבלה בהמשך הדף.")


def load_catalog(name):
    path = ROOT / "data" / "catalog" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


PLACE_RE = re.compile(r"^(\d+) km ([NSEW]{1,3}) of (.+), ([^,]+)$")


def usgs_place_he(place, names):
    """ "21 km SE of Mi?pé Yeri?o, Israel" -> "21 ק״מ דרומית-מזרחית למצפה יריחו, ישראל".
    None אם אין תרגום לשם (אז מוצג המקטע הקרוב)."""
    if not place:
        return None
    if place in names["regions"]:
        return names["regions"][place]
    m = PLACE_RE.match(place)
    if not m:
        return None
    km, direction, town, country = m.groups()
    town_he, dir_he = names["places"].get(town), names["directions"].get(direction)
    if not town_he or not dir_he:
        return None
    country_he = names["countries"].get(country)
    return f"{km} ק״מ {dir_he} ל{town_he}" + (f", {country_he}" if country_he else "")


def instruments_data(segments, segment_names, events):
    """מה נרשם במכשירים: קטלוג USGS מ-1900, וקטלוג המכון לחודשים האחרונים."""
    usgs = load_catalog("usgs")
    gsi = load_catalog("gsi")
    if not usgs:
        return None
    names = json.loads((ROOT / "data" / "place_names_he.json").read_text(encoding="utf-8"))
    missing = set()
    rows = []
    for q in usgs["events"]:
        t = dt.datetime.fromisoformat(q["t"].replace("Z", "+00:00"))
        seg, dist = echo.nearest_segment(q["lat"], q["lon"], segments)
        near_seg = seg is not None and dist <= echo.SEGMENT_KM
        where = usgs_place_he(q.get("place"), names)
        if where is None:
            if q.get("place"):
                missing.add(q["place"])
            if seg is not None:
                name = segment_names.get(seg["id"]) or seg.get("name_he")
                where = name if near_seg else f"כ־{round(dist)} ק״מ מקו השבר ({name})"
        rows.append(dict(q, time=t, year=t.year, fault_km=round(dist), label=t.astimezone(TZ).strftime("%-d.%-m.%Y"),
                         seg=seg["id"] if near_seg else None, where=where))
    for place in sorted(missing):
        print(f"אזהרה: אין שם בעברית ל-USGS place {place!r} (data/place_names_he.json)")
    # רעידה היסטורית באתר מאותו יום (למשל 1927)
    by_date = {}
    for e in events:
        d = e["date"]
        if d.get("year") and d.get("month") and d.get("day"):
            by_date[(d["year"], d["month"], d["day"])] = e
    for q in rows:
        q["event"] = by_date.get((q["time"].year, q["time"].month, q["time"].day))

    first_decade = min(q["year"] for q in rows) // 10 * 10
    last_decade = max(q["year"] for q in rows) // 10 * 10
    decades = []
    for d0 in range(first_decade, last_decade + 1, 10):
        n = sum(1 for q in rows if d0 <= q["year"] < d0 + 10)
        decades.append((f"{d0}", n, f"שנות ה-{d0}: {n} רעידות בקטלוג"))

    seg_counts = [(s, sum(1 for q in rows if q["seg"] == s["id"])) for s in segments]
    # חתך עומק: רעידות עד 25 ק"מ מקו שבר, לאורך השבר מדרום לצפון
    near = [q for q in rows if q["fault_km"] <= 25 and 28.3 <= q["lat"] <= 34.0]
    bands = []
    for s in segments:
        lats = [c[1] for line in s["lines"] for c in line]
        lo, hi = max(min(lats), 28.3), min(max(lats), 34.0)
        if hi > lo:
            bands.append((lo, hi, s["name_he"]))
    section = charts.depth_section(
        [(q["lat"], q["depth"], q["mag"],
          f'{q["label"]} · \u2066M{q["mag"]:g}\u2069 · עומק {q["depth"]:g} ק״מ · {q["where"] or ""}' if q["depth"] is not None else "")
         for q in near], (28.3, 34.0), 40, bands=bands,
        x_labels=[(y, f"{y}°") for y in (29, 30, 31, 32, 33)],
        title="חתך עומק לאורך השבר: עומק המוקד של כל רעידה, מדרום (ימין) לצפון (שמאל)",
        summary=depth_summary(near, bands))
    strongest = sorted(rows, key=lambda q: -q["mag"])[:12]
    # כמה מהרעידות של שנות ה-90 הן במפרץ אילת בשנה שאחרי 22.11.1995
    nineties = [q for q in rows if 1990 <= q["year"] < 2000]
    after95 = [q for q in nineties if "1995-11-22" <= q["t"][:10] <= "1996-11-22" and q["lat"] < 29.6]
    gsi_rows = gsi["events"] if gsi else []
    return dict(
        usgs=usgs, gsi=gsi,
        usgs_fetched=dt.date.fromisoformat(usgs["fetched_at"][:10]).strftime("%-d.%-m.%Y"),
        gsi_fetched=dt.date.fromisoformat(gsi["fetched_at"][:10]).strftime("%-d.%-m.%Y") if gsi else "", rows=rows, strongest=strongest, seg_counts=seg_counts,
        near_count=len(near), depth10=sum(1 for q in near if q["depth"] == 10), first_year=min(q["year"] for q in rows),
        nineties=len(nineties), after95=len(after95),
        chart_decades=charts.bars(decades, width=420, height=170, title="מספר הרעידות בקטלוג בכל עשור",
                                  summary=decades_summary(decades)),
        table_decades=charts.data_table("מספר הרעידות בקטלוג בכל עשור", ["עשור", "רעידות"], [(d, n) for d, n, _ in decades]),
        chart_section=section,
        chart_segments=charts.hbars(sorted(((s["name_he"], n) for s, n in seg_counts), key=lambda r: -r[1])),
        gsi_count=len(gsi_rows),
        gsi_first=dt.date.fromisoformat(gsi_rows[0]["t"][:10]).strftime("%-d.%-m.%Y") if gsi_rows else None,
        gsi_felt=sum(1 for q in gsi_rows if q.get("felt")),
        map_live=[dict(lat=q["lat"], lon=q["lon"], magnitude=q["mag"], time_utc=q["t"],
                       label=q["time"].astimezone(TZ).strftime("%-d.%-m.%Y"), depth_km=q["depth"],
                       local=q["where"], anchor=None, url=q.get("url"), key="u-" + q["id"])
                  for q in rows],
    )


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
        untodo=lambda t: TODO_RE.sub("", t or "").strip(),
    )
    env.globals.update(
        asset=asset_url,
        figure=lambda ids: Markup(figure_html(ids)),
        og_image=og_image,
        jsonld=jsonld,
        base=BASE_PATH,
        site_url=SITE_URL,
        site_host=urlparse(SITE_URL).hostname,
        site_name=SITE_NAME,
        site_tagline=SITE_TAGLINE,
    )
    return env


def og_image(page_path):
    """תמונת השיתוף של הדף (scripts/make_og.py), או התמונה הכללית אם אין לו משלו."""
    parts = [p for p in page_path.strip("/").split("/") if p]
    key = "home" if not parts else f"event-{parts[1]}" if parts[0] == "events" and len(parts) > 1 else parts[0]
    rel = f"img/og/{key}.png"
    return rel if (ROOT / "static" / rel).exists() else "img/og.png"


def jsonld(page_path, title, description, e=None):
    """נתונים מובנים (schema.org) לגוגל: WebSite בדף הבית, Article לכל דף אחר.
    בדף רעידה גם about (האירוע, עם תאריך רק כשהוא ידוע לספירה) ו-citation (מקורות עם קישור)."""
    url = f"{SITE_URL}{page_path}"
    publisher = {"@type": "Organization", "name": SITE_NAME, "url": f"{SITE_URL}/"}
    if page_path == "/":
        data = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "alternateName": SITE_TAGLINE,
                "url": url, "inLanguage": "he", "description": description or SITE_TAGLINE, "publisher": publisher}
    else:
        data = {"@context": "https://schema.org", "@type": "Article", "headline": title or SITE_NAME,
                "description": description or SITE_TAGLINE, "url": url, "mainEntityOfPage": url, "inLanguage": "he",
                "image": f"{SITE_URL}/static/{og_image(page_path)}", "publisher": publisher,
                "isPartOf": {"@type": "WebSite", "name": SITE_NAME, "url": f"{SITE_URL}/"}}
        if e:
            about = {"@type": "Event", "name": e["title"]}
            d = e.get("date") or {}
            if d.get("certainty") in ("exact", "approximate") and (d.get("year") or 0) > 0:
                about["startDate"] = "-".join(f"{v:02d}" if i else f"{v:04d}"
                                              for i, v in enumerate(x for x in (d["year"], d.get("month"), d.get("day")) if x))
            if e.get("segment_name"):
                about["location"] = {"@type": "Place", "name": e["segment_name"]}
            data["about"] = about
            cites = [{"@type": "CreativeWork", "name": s["label"], "url": s["url"]}
                     for s in e.get("sources") or [] if s.get("url") and "TODO" not in (s.get("label") or "")]
            if cites:
                data["citation"] = cites
    # "</" בתוך סקריפט יסגור אותו מוקדם
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def asset_url(rel):
    """כתובת לקובץ ב-static/ עם גרסה לפי התוכן (?v=...), כדי שדפדפן לא ישתמש
    בגרסה ישנה מהמטמון אחרי עדכון (אחרת HTML חדש רץ עם JS ו-CSS ישנים)."""
    import hashlib
    data = (ROOT / "static" / rel).read_bytes()
    return f"{BASE_PATH}/static/{rel}?v={hashlib.sha1(data).hexdigest()[:8]}"


# סימוני עבודה בתוכן (כלל 1-2) נשארים בקובצי content/, אבל הקורא רואה תווית ברורה
# ולא "TODO". הערות HTML (הערות עבודה) לא נכנסות לדף בכלל.
TODO_RE = re.compile(r"\s*\(TODO:?\s*([^)<;]*)[^)<]*\)|TODO:?\s*([^.)<;]*)")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def _todo_label(m):
    what = m.group(1) if m.group(1) is not None else m.group(2)
    if what.startswith("מקור"):
        text = "חסר מקור"
    elif "ציטוט" in what:
        text = "ציטוט טרם אומת"
    else:
        text = "טרם נבדק במקור"
    return f' <span class="unchecked">{text}</span>'


def reader_facing(html):
    return TODO_RE.sub(_todo_label, COMMENT_RE.sub("", html))


def write(path, html):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(reader_facing(html), encoding="utf-8")


DAMAGE_STATUS = {
    "reported": "לפי המקורות",
    "found": "נמצא בשטח",
    "reported+found": "לפי המקורות, ונמצא בשטח",
    "doubtful": "הקשר לרעידה שנוי במחלוקת",
}


def load_damage():
    path = ROOT / "data" / "damage" / "sites.json"
    return json.loads(path.read_text(encoding="utf-8"))["sites"] if path.exists() else []


def damage_data(sites, events, only=None):
    """מקומות שנפגעו, לכל מקום הרעידות שפגעו בו. only: מזהה רעידה אחת (בדף רעידה)."""
    by_id = {e["id"]: e for e in events}
    out = []
    for s in sites:
        entries = [
            {"title": by_id[x["event"]]["short_title"], "url": f"{BASE_PATH}/events/{x['event']}/",
             "place": x["place_he"], "what": x["evidence"], "status": DAMAGE_STATUS.get(x["status"], ""),
             "doubtful": x["status"] == "doubtful", "year": by_id[x["event"]]["date"]["year"]}
            for x in s["entries"]
            if x["event"] in by_id and x["status"] in DAMAGE_STATUS and (only is None or x["event"] == only)
        ]
        if entries:
            entries.sort(key=lambda x: x["year"])
            out.append({"name": s["place_he"], "lat": s["lat"], "lon": s["lon"], "entries": entries,
                        "doubtful": all(x["doubtful"] for x in entries)})
    return out


def approx_points(e, focus):
    """מיקומים משוערים של רעידה היסטורית: מוקד אחד ממקור, או כמה הצעות (למשל 1927).
    focus: בדף הרעידה התוויות קבועות; בדף הבית הן מופיעות רק בריחוף, כדי לא להעמיס."""
    loc = e["location"]
    base = {"id": e["id"], "title": e["short_title"], "year": fmt.event_year_label(e),
            "kind": evidence_kind(e), "url": f"{BASE_PATH}/events/{e['id']}/"}
    out = []
    if loc.get("lat") is not None and loc.get("lon") is not None:
        out.append(dict(base, lat=loc["lat"], lon=loc["lon"], source=loc.get("source"),
                        source_url=loc.get("source_url"), label=None, perm=True))
    for p in loc.get("proposals") or []:
        out.append(dict(base, lat=p["lat"], lon=p["lon"], label=p["label"],
                        source=p.get("source") or f'{p["label"]}. לפי {loc.get("proposals_source")}',
                        source_url=p.get("source_url") or loc.get("proposals_source_url"), perm=False))
    return out


def map_data(events, live, segments, focus=False, highlight=None, all_events=None, damage=None):
    """focus: מפה של דף רעידה בודדת. המבט כולל את הרעידה גם כשהיא רחוקה.
    highlight: מזהה המקטע של הרעידה. המקטע מודגש והמבט מתמקד בו."""
    return {
        "focus": focus,
        "damage": damage or [],
        "basemap": f"{BASE_PATH}/static/data/basemap.json",
        "highlight": highlight,
        "segments": [
            {"id": s["id"], "name": s["name_he"] + (" (טיוטה, טרם אושר)" if s.get("draft") else ""),
             "note": s.get("note_he"), "lines": s["lines"], "draft": bool(s.get("draft")),
             # הרעידות ההיסטוריות שמשויכות למקטע, לחלון שנפתח בלחיצה על הקו
             "history": [{"title": e["short_title"], "url": f"{BASE_PATH}/events/{e['id']}/"}
                         for e in sorted(all_events or [], key=lambda e: e["date"]["year"])
                         if e["location"].get("segment") == s["id"]]}
            for s in segments if s.get("approved")
        ],
        "events": [p for e in events for p in approx_points(e, focus)],
        "live": [
            {
                "lat": q["lat"],
                "lon": q["lon"],
                "mag": q["magnitude"],
                "time_utc": q["time_utc"],
                "label": q["label"],
                "depth": q.get("depth_km"),
                "local": q.get("local"),
                "url": f"{BASE_PATH}/recent/#{q['anchor']}" if q.get("anchor") else q.get("url"),
                "key": q.get("anchor") or q.get("key"),
            }
            for q in live["events"]
        ],
    }


def load_config():
    path = ROOT / "data" / "site.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def build(drafts=False):
    now = dt.datetime.now(dt.timezone.utc)
    public_drafts = not drafts and bool(load_config().get("show_drafts"))
    today = now.astimezone(TZ).date()

    all_events = load_events()
    events = [e for e in all_events if drafts or public_drafts or e["status"] == "published"]
    segments = echo.load_segments()
    segment_names = {s["id"]: s["name_he"] for s in segments} | SEGMENT_NAMES_EXTRA

    # בתצוגת טיוטות גם מקטעים שלא אושרו משמשים למפה ולהד, כדי שאפשר יהיה לבדוק אותם
    if drafts or public_drafts:
        segments = [dict(s, draft=not s.get("approved"), approved=True) for s in segments]
    live = load_live()
    damage_sites = load_damage()
    echo.annotate(live["events"], events, segments)
    for q in live["events"]:
        q["ago"] = relative_hours(q["time"], now)
        q["label"] = live_label(q, segment_names)
    describe_quakes(live["events"], segments, segment_names)

    by_id = {e["id"]: e for e in events}
    for e in events:
        e["sections"], e["footnotes"] = split_sections(e["body"])
        for sec, html in zip(e["sections"], glossary_links([x["html"] for x in e["sections"]])):
            sec["html"] = html
        e["card_notes"] = card_notes(e)
        e["kind"] = evidence_kind(e)
        e["has_wikipedia"] = any("wikipedia.org" in (s.get("url") or "") for s in e.get("sources") or [])
        seg = e["location"].get("segment")
        e["segment_name"] = segment_names.get(seg) if seg else None
        e["same_segment"] = [
            o for o in events
            if o is not e and seg and seg != echo.DISTANT and o["location"].get("segment") == seg
        ]
        e["live_nearby"] = [q for q in live["events"] if seg and q.get("segment") == seg]

    env = make_env()
    # הפס החי בראש כל דף: הרעידה האחרונה שנרשמה
    latest_quake = live["events"][0] if live["events"] else None
    # הבאנר "האתר בבנייה" רק כשיש באמת דף טיוטה באתר
    common = dict(drafts=drafts, public_drafts=public_drafts and any(e["status"] != "published" for e in events), built_at=now, segment_names=segment_names,
                  live_bar=latest_quake, live_ticker=live["events"][:5], live_bar_by_id={e["id"]: e for e in events})

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
        map_data=map_data(events, live_month, segments, all_events=events, damage=damage_data(damage_sites, events)),
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
            map_data=map_data([e], dict(live, events=e["live_nearby"]), segments, focus=True, all_events=events,
                              damage=damage_data(damage_sites, events, only=e["id"]),
                              highlight=e["location"].get("segment") if e["segment_name"] and e["location"].get("segment") != echo.DISTANT else None),
        ))
        if e["status"] == "published":
            pages.append(path)

    # 30 הימים האחרונים
    days, by_mag = recent_summary(live_month["events"], today)
    write(SITE / "recent" / "index.html", env.get_template("recent.html").render(
        **common,
        page_path="/recent/",
        live=live,
        supplement_since=(lambda t: f"{t.day}.{t.month}")(dt.datetime.fromisoformat(live["supplement"]["since"].replace("Z", "+00:00")).astimezone(TZ)) if live.get("supplement") else None,
        quakes=live_month["events"],
        by_id=by_id,
        by_mag=by_mag,
        strongest=max(live_month["events"], key=lambda q: q["magnitude"], default=None),
        felt=[q for q in live_month["events"] if q.get("felt")],
        chart_days=charts.bars(days, width=420, height=150, label_every=7, title="מספר הרעידות בכל יום, 30 הימים האחרונים",
                               summary=days_summary(days)),
        table_days=charts.data_table("מספר הרעידות בכל יום, מהישן לחדש", ["תאריך", "רעידות"], [(d, n) for d, n, _ in days]),
        map_data=map_data([], live_month, segments),
    ))
    pages.append("/recent/")

    # מכשירי מדידה
    inst = instruments_data(segments, segment_names, events)
    if inst:
        write(SITE / "instruments" / "index.html", env.get_template("instruments.html").render(
            **common,
            page_path="/instruments/",
            inst=inst,
            map_data=dict(map_data([], {"events": inst["map_live"]}, segments), live_title="רעידות שנמדדו", live_legend="2.5 ומעלה, בקטלוג USGS", live_kind="נמדדה במכשירים · קטלוג USGS", dot_scale=2.2),
        ))
        pages.append("/instruments/")

    # ציר הזמן
    write(SITE / "timeline" / "index.html", env.get_template("timeline.html").render(
        **common,
        page_path="/timeline/",
        events=events,
        svg_h=timeline.horizontal(events, BASE_PATH),
        svg_v=timeline.vertical(events, BASE_PATH),
    ))
    pages.append("/timeline/")

    # דפים כלליים מ-content/pages/*.md (למשל "מה זו רעידת אדמה"). כל דף: frontmatter עם
    # slug, title, description ו-lede, וגוף Markdown עם כותרות ## והערות שוליים.
    for path in sorted((ROOT / "content" / "pages").glob("*.md")):
        meta, body = read_event(path)
        if meta.get("status") != "published" and not (drafts or public_drafts):
            continue
        # קישורים פנימיים בכתיבה הם "/events/..." ; באתר הם תחת BASE_PATH
        body = body.replace("](/", f"]({BASE_PATH}/")
        meta["sections"], meta["footnotes"] = split_sections(body)
        slug = meta["slug"]
        write(SITE / slug / "index.html", env.get_template("page.html").render(
            **common, page_path=f"/{slug}/", page=meta, noindex=meta.get("status") != "published"))
        if meta.get("status") == "published":
            pages.append(f"/{slug}/")

    # על האתר
    write(SITE / "about" / "index.html", env.get_template("about.html").render(
        **common,
        page_path="/about/",
        license=WIKI_LICENSE,
        image_credits=image_credits(),
    ))
    pages.append("/about/")

    # הצהרות: פרטיות ונגישות
    for name in ("privacy", "accessibility"):
        write(SITE / name / "index.html", env.get_template(f"{name}.html").render(**common, page_path=f"/{name}/"))
        pages.append(f"/{name}/")

    write(SITE / "404.html", env.get_template("404.html").render(**common, page_path="/404.html"))

    # sitemap ו-robots
    if drafts:
        write(SITE / "robots.txt", "User-agent: *\nDisallow: /\n")
    else:
        write(SITE / "sitemap.xml", env.get_template("sitemap.xml").render(
            pages=pages, lastmod=today.isoformat()))
        write(SITE / "robots.txt", f"User-agent: *\nAllow: /\n# תיאור האתר למודלי שפה: {SITE_URL}/llms.txt\nSitemap: {SITE_URL}/sitemap.xml\n")
        # llms.txt: תיאור האתר ורשימת הדפים למודלי שפה (llmstxt.org)
        write(SITE / "llms.txt", env.get_template("llms.txt").render(**common, events=[e for e in events if e["status"] == "published"]))

    mode = ", with drafts (local)" if drafts else ", with drafts (public, noindex)" if public_drafts else ""
    print(f"built {len(events)} events{mode}, sitemap {len(pages)} pages -> {SITE}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--drafts", action="store_true", help="לבנות גם טיוטות (תצוגה מקומית בלבד)")
    build(drafts=parser.parse_args().drafts)


if __name__ == "__main__":
    main()
