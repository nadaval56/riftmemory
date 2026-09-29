"""בדיקות לפני פרסום (פרק 10), מה שאפשר לבדוק אוטומטית.

רץ על content/ ועל site/ אחרי build_site.py. מדווח ולא מתקן.
יוצא בקוד 1 אם יש כשל בדף שמסומן published, או קישור פנימי שבור.

בדיקות תוכן (רק על published):
  - אין "TODO: מקור" או "TODO: לאמת ציטוט" גלויים (מחוץ להערות HTML ול-review_notes):
    טענה בלי מקור, או ציטוט שלא אומת, לא מתפרסמים (כללים 1–2).
    "TODO: לבדוק במקור" מותר בדף מפורסם, לפי החלטת נדב (ספטמבר 2026): הקורא רואה
    תווית גלויה "טרם נבדק במקור" ליד מקור שעוד לא נבדק מול המקור עצמו.
  - יש לפחות מקור אחד עם url
  - אין ניסוח חיזויי
בדיקות טכניות (על site/):
  - אין שנה שלילית מוצגת ("-31")
  - קישורים פנימיים שבורים
  - לכל דף: title, description, canonical, og:title, og:description, og:url, og:image
  - sitemap.xml תקין ומכיל רק דפים שקיימים
  - בדפי רעידה: קרדיט ורישיון לוויקיפדיה
"""

import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from build_events import load_events
from build_site import BASE_PATH, SITE, SITE_URL

ROOT = Path(__file__).resolve().parent.parent

# ניסוחים חיזויים (כלל 5). "תחזיות" לבד מותר, כי האתר אומר שהוא לא עוסק בהן.
FORECAST = re.compile(r"הרעידה הבאה|צפויה|צפוי ל|מתקרבת|עומדת לפרוץ|בקרוב תהיה|סימן ש(?!אלה)|מבשר")
# סימוני TODO שחוסמים פרסום: טענה בלי מקור, ציטוט שלא אומת. "לבדוק במקור" מותר (מוצג כתווית).
BLOCKING_TODO = re.compile(r"TODO:?\s*(מקור|לאמת ציטוט)")
FORECAST_OK = re.compile(r"לא עוסק ב(תחזיות|שאלה מתי תהיה הרעידה הבאה)|מתי תהיה הרעידה הבאה")


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.meta, self.title, self._in_title = [], {}, "", False
        self.text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag in ("link", "script") and (a.get("href") or a.get("src")):
            self.links.append(a.get("href") or a.get("src"))
        if tag == "meta":
            key = a.get("property") or a.get("name")
            if key:
                self.meta[key] = a.get("content", "")
        if tag == "link" and a.get("rel") == "canonical":
            self.meta["canonical"] = a.get("href", "")
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        self.text.append(data)


def check_content(problems):
    for e in load_events():
        if e["status"] != "published":
            continue
        where = f"content/events/{e['id']}.md"
        raw = (Path(__file__).resolve().parent.parent / where).read_text(encoding="utf-8")
        visible = re.sub(r"<!--.*?-->", "", raw.split("\nreview_notes:", 1)[0] + raw.split("\n---", 2)[-1], flags=re.S)
        for m in BLOCKING_TODO.finditer(visible):
            problems.append(f"{where}: published עם {m.group(0)!r}")
        sources = e.get("sources") or []
        if not any(s.get("url") for s in sources):
            problems.append(f"{where}: אין מקור עם קישור")
        body = FORECAST_OK.sub("", e["body"])
        for m in FORECAST.finditer(body):
            problems.append(f"{where}: ניסוח חיזויי: {m.group(0)!r}")


def site_path(href):
    """קישור פנימי -> קובץ ב-site/, או None לקישור חיצוני."""
    u = urlparse(href)
    if u.scheme in ("http", "https"):
        if not href.startswith(SITE_URL):
            return None
        path = u.path[len(urlparse(SITE_URL).path):]
    elif u.scheme or href.startswith(("#", "mailto:")):
        return None
    else:
        path = u.path
        if BASE_PATH and path.startswith(BASE_PATH):
            path = path[len(BASE_PATH):]
    path = path.lstrip("/")
    target = SITE / path
    if path == "" or path.endswith("/"):
        target = target / "index.html"
    return target


def check_site(problems, warnings):
    if not SITE.exists():
        problems.append("site/ לא קיים. להריץ קודם build_site.py")
        return
    pages = sorted(SITE.rglob("*.html"))
    for f in pages:
        rel = f.relative_to(SITE)
        html = f.read_text(encoding="utf-8")
        p = Page()
        p.feed(html)
        text = " ".join(p.text)

        if re.search(r"(?<![\w.\d-])-\d{1,4}(?![\d.])", text):
            for m in re.finditer(r"(?<![\w.\d-])-\d{1,4}(?![\d.])", text):
                warnings.append(f"{rel}: אולי שנה שלילית מוצגת: {m.group(0)!r}")
        clean = FORECAST_OK.sub("", text)
        for m in FORECAST.finditer(clean):
            problems.append(f"{rel}: ניסוח חיזויי: {m.group(0)!r}")

        for href in p.links:
            target = site_path(href)
            if target is not None and not target.exists():
                problems.append(f"{rel}: קישור שבור: {href}")

        if rel.name != "404.html":
            for key in ("description", "canonical", "og:title", "og:description", "og:url", "og:image"):
                if not p.meta.get(key):
                    problems.append(f"{rel}: חסר {key}")
            if not p.title.strip():
                problems.append(f"{rel}: חסר title")
            og_img = site_path(p.meta.get("og:image", ""))
            if og_img is not None and not og_img.exists():
                problems.append(f"{rel}: og:image לא קיים: {p.meta.get('og:image')}")

        if rel.parts[0] == "events":
            if "he.wikipedia.org" in html and "CC BY-SA" not in html:
                problems.append(f"{rel}: קישור לוויקיפדיה בלי רישיון")

    sitemap = SITE / "sitemap.xml"
    if sitemap.exists():
        try:
            root = ET.parse(sitemap).getroot()
        except ET.ParseError as exc:
            problems.append(f"sitemap.xml לא תקין: {exc}")
        else:
            ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            for loc in root.findall("s:url/s:loc", ns):
                target = site_path(loc.text.strip())
                if target is None or not target.exists():
                    problems.append(f"sitemap.xml: דף לא קיים: {loc.text}")
    elif not (SITE / "robots.txt").read_text().startswith("User-agent: *\nDisallow"):
        problems.append("חסר sitemap.xml")


def check_damage(problems):
    """כל רשומה בשכבת המקומות שנפגעו מצטטת משפט שקיים בדף הרעידה, עם הערות שקיימות בו."""
    places = ROOT / "data" / "damage" / "places.json"
    if not places.exists():
        return
    pages = {}
    for p in json.loads(places.read_text(encoding="utf-8")):
        path = ROOT / "content" / "events" / f"{p['event']}.md"
        text = pages.setdefault(p["event"], path.read_text(encoding="utf-8") if path.exists() else "")
        if p["page_sentence"] not in text:
            problems.append(f"places.json: המשפט על {p['place_en']} ({p['event']}) לא נמצא בדף")
        for fn in p["footnotes"]:
            if f"[^{fn}]:" not in text:
                problems.append(f"places.json: הערה {fn} ({p['place_en']}, {p['event']}) לא קיימת בדף")


def main():
    problems, warnings = [], []
    check_content(problems)
    check_damage(problems)
    check_site(problems, warnings)
    for w in warnings:
        print(f"אזהרה: {w}")
    for p in problems:
        print(f"כשל: {p}")
    print(f"{len(problems)} כשלים, {len(warnings)} אזהרות")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
