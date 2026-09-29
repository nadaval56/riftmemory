"""שלב 1: משיכת ערכי הקטגוריה "ארץ ישראל: רעידות אדמה" מה-API של מדיה-ויקי.

פלט: data/raw/wikipedia/<pageid>.json לכל ערך (ראו docs/guide.pdf, פרק 4.1).
תת-קטגוריות לא נמשכות, וכפילויות מוסרות לפי pageid.
דף הפניה (#הפניה) נשמר עם היעד שלו: אם ההפניה היא לפסקה בערך אחר,
נשמר הוויקיטקסט של הפסקה הזו בלבד, בשדה redirect.
"""

import json
import re
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "wikipedia"

API = "https://he.wikipedia.org/w/api.php"
CATEGORY = "קטגוריה:ארץ ישראל: רעידות אדמה"
USER_AGENT = "riftmemory/0.1 (https://github.com/nadaval56/riftmemory)"
DELAY_SECONDS = 1.0

session = requests.Session()
session.headers["User-Agent"] = USER_AGENT


def api_get(**params):
    params.setdefault("format", "json")
    params.setdefault("formatversion", "2")
    resp = session.get(API, params=params, timeout=30)
    resp.raise_for_status()
    time.sleep(DELAY_SECONDS)
    data = resp.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data


def category_pages():
    """חברי הקטגוריה מסוג דף (namespace 0) בלבד, בלי כפילויות לפי pageid."""
    pages = {}
    params = dict(
        action="query",
        list="categorymembers",
        cmtitle=CATEGORY,
        cmlimit="500",
        cmtype="page",
    )
    while True:
        data = api_get(**params)
        for m in data["query"]["categorymembers"]:
            if m["ns"] == 0:
                pages.setdefault(m["pageid"], m["title"])
        if "continue" not in data:
            break
        params.update(data["continue"])
    return pages


def fetch_page(pageid, title):
    parsed = api_get(
        action="parse",
        pageid=pageid,
        prop="wikitext|categories|links",
    )["parse"]
    meta = api_get(
        action="query",
        pageids=pageid,
        prop="pageprops|coordinates|info",
        inprop="url",
    )["query"]["pages"][0]

    coords = meta.get("coordinates") or []
    primary = next((c for c in coords if c.get("primary")), coords[0] if coords else None)

    return {
        "pageid": pageid,
        "title": parsed["title"],
        "url": meta.get("fullurl"),
        "revid": parsed.get("revid"),
        "wikidata": meta.get("pageprops", {}).get("wikibase_item"),
        "coordinates": (
            {"lat": primary["lat"], "lon": primary["lon"]} if primary else None
        ),
        "categories": [c["category"] for c in parsed.get("categories", [])],
        "links": [l["title"] for l in parsed.get("links", []) if l.get("ns") == 0],
        "wikitext": parsed["wikitext"],
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


REDIRECT_RE = re.compile(r"^#(?:הפניה|redirect)\s*\[\[([^\]#|]+)(?:#([^\]|]+))?", re.I)


def section_wikitext(wikitext, heading):
    """הוויקיטקסט של פסקה לפי כותרת, עד הכותרת הבאה באותה רמה או גבוהה ממנה."""
    lines = wikitext.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(=+)\s*(.*?)\s*\1\s*$", line)
        if m and m.group(2) == heading:
            level = len(m.group(1))
            out = [line]
            for rest in lines[i + 1:]:
                n = re.match(r"^(=+)[^=].*?\1\s*$", rest)
                if n and len(n.group(1)) <= level:
                    break
                out.append(rest)
            return "\n".join(out)
    return None


def fetch_redirect(wikitext):
    m = REDIRECT_RE.match(wikitext.strip())
    if not m:
        return None
    target, section = m.group(1).strip(), (m.group(2) or "").strip() or None
    parsed = api_get(action="parse", page=target, prop="wikitext", redirects="1")["parse"]
    info = api_get(action="query", titles=parsed["title"], prop="info", inprop="url")["query"]["pages"][0]
    text = parsed["wikitext"]
    return {
        "title": parsed["title"],
        "section": section,
        "url": info.get("fullurl") + (("#" + section.replace(" ", "_")) if section else ""),
        "revid": parsed.get("revid"),
        "wikitext": section_wikitext(text, section) if section else text,
    }


EN_API = "https://en.wikipedia.org/w/api.php"


def fetch_english(pageid):
    """הערך המקביל בוויקיפדיה האנגלית, אם יש (לבדיקה מול מקורות, לא לפרסום)."""
    pages = api_get(action="query", pageids=pageid, prop="langlinks", lllang="en")["query"]["pages"]
    links = pages[0].get("langlinks") or []
    if not links:
        return None
    title = links[0]["title"]
    resp = session.get(EN_API, params=dict(action="parse", page=title, prop="wikitext",
                                           redirects="1", format="json", formatversion="2"), timeout=30)
    resp.raise_for_status()
    time.sleep(DELAY_SECONDS)
    parsed = resp.json()["parse"]
    return {"title": parsed["title"], "url": "https://en.wikipedia.org/wiki/" + parsed["title"].replace(" ", "_"),
            "revid": parsed.get("revid"), "wikitext": parsed["wikitext"]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pages = category_pages()
    for pageid, title in sorted(pages.items(), key=lambda p: p[1]):
        record = fetch_page(pageid, title)
        record["redirect"] = fetch_redirect(record["wikitext"])
        record["english"] = None if record["redirect"] else fetch_english(pageid)
        path = OUT / f"{pageid}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{pageid}\t{record['title']}\twikidata={record['wikidata']}\tcoords={record['coordinates']}"
              + (f"\tredirect={record['redirect']['title']}#{record['redirect']['section']}" if record["redirect"] else ""))
    print(f"saved {len(pages)} pages")


if __name__ == "__main__":
    main()
