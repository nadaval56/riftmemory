"""תמונות שיתוף (og:image) לכל דף: כרטיס 1200×630 בשפה של האתר.

שני שלבים, כי הרינדור צריך דפדפן (Playwright), ולא רץ בכל בנייה:
  1. python3 scripts/make_og.py            -> og-build/cards.html (כל הכרטיסים בדף אחד)
  2. node scripts/og_render.mjs            -> static/img/og/<key>.png (צילום של כל כרטיס)
להריץ שוב כשמוסיפים רעידה, משנים שם או מקטע. build_site.py משתמש בתמונה של הדף
אם היא קיימת, ובתמונה הכללית static/img/og.png אם לא.

בכרטיס: שם, שנה, מקטע, ומפה קטנה של קווי ההעתקים (data/faults.geojson) שבה המקטע
של הרעידה מודגש. אין נקודת מוקד: לרוב הרעידות אין קואורדינטות מאושרות (CLAUDE.md, כלל 9).
"""

import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import echo  # noqa: E402
import fmt  # noqa: E402
from build_events import load_events  # noqa: E402

OUT = ROOT / "og-build"
SITE_NAME = "רעידת אדמה"
TAGLINE = "רעידות אדמה היסטוריות בשבר הסורי-אפריקני"

# דפים כלליים: מפתח הקובץ -> (כותרת, שורת משנה)
PAGES = {
    "home": ("השבר הסורי-אפריקני", "רעידות אדמה היסטוריות בארץ ישראל, לפי המקורות"),
    "recent": ("רעידות אדמה ב־30 הימים האחרונים", "מתעדכן כל שעה, לפי המכון הגיאולוגי"),
    "instruments": ("מכשירי מדידה", "מה נרשם בסייסמוגרפים מאז 1900"),
    "timeline": ("ציר הזמן", "כל הרעידות שבאתר על ציר אחד"),
    "people": ("עדים וחוקרים", "מי תיעד את הרעידות ומי חקר אותן"),
    "what-is-an-earthquake": ("מה זו רעידת אדמה?", "הסבר קצר ומדויק, עם מקורות"),
    "earthquake-safety": ("מה עושים ברעידת אדמה", "ההנחיות של פיקוד העורף, מילה במילה"),
    "glossary": ("מילון מונחים", "מגניטודה, עוצמה, מוקד, העתק ועוד, עם מקור לכל הגדרה"),
    "about": ("על האתר ועל המקורות", "איך נבנה האתר ועל מה הוא מבוסס"),
}

# גבולות המפה (קו רוחב / אורך) והגודל שלה בכרטיס
BOX = dict(min_lat=28.3, max_lat=34.4, min_lon=34.2, max_lon=37.0)
MAP_W, MAP_H = 300, 520

ARCH = ('<svg class="mark" viewBox="0 0 32 32" aria-hidden="true"><g>'
        '<path d="M3 24.2h6v6h-6Z"/><path d="M3 17.8h6v6h-6Z"/><path d="M23 24.2h6v6h-6Z"/><path d="M23 17.8h6v6h-6Z"/>'
        '<path d="M21.92 5.63A13 13 0 0 1 29.00 17.20L23.00 17.20A7 7 0 0 0 19.19 10.97Z"/>'
        '<path d="M3.00 17.20A13 13 0 0 1 10.08 5.63L12.81 10.97A7 7 0 0 0 9.00 17.20Z"/>'
        '<path d="M9.77 3.78A14.8 14.8 0 0 1 22.23 3.78L18.48 11.85A5.9 5.9 0 0 0 13.52 11.85Z"/></g></svg>')


def project(lon, lat):
    x = (lon - BOX["min_lon"]) / (BOX["max_lon"] - BOX["min_lon"]) * MAP_W
    y = (BOX["max_lat"] - lat) / (BOX["max_lat"] - BOX["min_lat"]) * MAP_H
    return f"{x:.1f},{y:.1f}"


def fault_map(segments, highlight=None):
    paths = []
    for seg in segments:
        cls = "hl" if seg["id"] == highlight else "f"
        for line in seg["lines"]:
            paths.append(f'<polyline class="{cls}" points="{" ".join(project(lon, lat) for lon, lat in line)}"/>')
    # המקטע המודגש מצויר אחרון, מעל האחרים
    paths.sort(key=lambda p: 'class="hl"' in p)
    return f'<svg class="map" viewBox="0 0 {MAP_W} {MAP_H}" aria-hidden="true">{"".join(paths)}</svg>'


def card(key, title, sub, meta, segments, highlight=None):
    size = "xl" if len(title) <= 16 else "l" if len(title) <= 28 else "m"
    meta_html = f'<p class="meta">{escape(meta)}</p>' if meta else ""
    return (f'<section class="card" id="{key}">'
            f'<div class="text"><p class="brand">{ARCH}<span>{SITE_NAME}</span></p>'
            f'<h1 class="{size}">{escape(title)}</h1>{meta_html}<p class="sub">{escape(sub)}</p>'
            f'<p class="tag">{TAGLINE}</p></div>'
            f'<div class="map-wrap">{fault_map(segments, highlight)}</div></section>')


def main():
    segments = echo.load_segments()
    names = {s["id"]: s["name_he"] for s in segments}
    cards = []
    for key, (title, sub) in PAGES.items():
        cards.append(card(key, title, sub, None, segments))
    for e in load_events():
        if e["status"] != "published":
            continue
        seg = (e.get("location") or {}).get("segment")
        meta = fmt.event_year_label(e)
        if seg in names:
            meta += f" · {names[seg]}"
        # השנה כבר בשורה שמתחת לכותרת, אז בלי "(1927)" בסוף הכותרת
        title = re.sub(r"\s*\([^()]*\)$", "", e["title"])
        cards.append(card(f"event-{e['id']}", title, e.get("meta_description") or "", meta,
                          segments, highlight=seg if seg in names else None))
    fonts = (ROOT / "static" / "fonts").as_uri()
    html = f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><style>
@font-face {{ font-family: Heebo; font-weight: 100 900; src: url('{fonts}/heebo-hebrew.woff2') format('woff2'); }}
@font-face {{ font-family: Heebo; font-weight: 100 900; src: url('{fonts}/heebo-latin.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+2000-206F; }}
body {{ margin: 0; background: #ddd; font-family: Heebo, sans-serif; }}
.card {{ width: 1200px; height: 630px; box-sizing: border-box; display: flex; gap: 48px; padding: 56px 64px;
  background: #f4f2ec; color: #1f1e1d; border-top: 14px solid #c96442; margin-bottom: 20px; }}
.text {{ flex: 1; display: flex; flex-direction: column; min-width: 0; }}
.brand {{ display: flex; align-items: center; gap: 14px; margin: 0; font-size: 34px; font-weight: 700; color: #a75337; }}
.mark {{ width: 52px; height: 52px; fill: #c96442; }}
h1 {{ margin: 56px 0 0; font-weight: 800; line-height: 1.12; letter-spacing: -.5px; }}
h1.xl {{ font-size: 84px; }} h1.l {{ font-size: 68px; }} h1.m {{ font-size: 56px; }}
.meta {{ margin: 22px 0 0; font-size: 36px; font-weight: 600; color: #a75337; }}
.sub {{ margin: 22px 0 0; font-size: 28px; line-height: 1.4; color: #55524d;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
.tag {{ margin: auto 0 0; font-size: 24px; color: #6b675f; }}
.map-wrap {{ width: {MAP_W}px; flex: none; display: flex; align-items: center; justify-content: center;
  background: #fbfaf6; border: 1px solid #e3ded3; border-radius: 22px; }}
.map {{ width: {MAP_W - 40}px; height: auto; }}
.map polyline {{ fill: none; stroke-linecap: round; stroke-linejoin: round; }}
.map .f {{ stroke: #9c968b; stroke-width: 3; }}
.map .hl {{ stroke: #c96442; stroke-width: 7; }}
</style></head><body>{"".join(cards)}</body></html>"""
    OUT.mkdir(exist_ok=True)
    (OUT / "cards.html").write_text(html, encoding="utf-8")
    (OUT / "keys.json").write_text(json.dumps([c.split('id="')[1].split('"')[0] for c in cards]), encoding="utf-8")
    print(f"{len(cards)} cards -> {OUT / 'cards.html'}")


if __name__ == "__main__":
    main()
