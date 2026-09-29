"""בונה את data/events.json מה-frontmatter של content/events/*.md (פרק 5.1).

הקובץ כולל את כל הרעידות, גם בסטטוס draft. הסינון לפי סטטוס נעשה ב-build_site.py.
"""

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
EVENTS_DIR = ROOT / "content" / "events"
OUT = ROOT / "data" / "events.json"


def read_event(path):
    """מחזיר (frontmatter, body) של קובץ Markdown."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: חסר frontmatter")
    _, fm, body = text.split("---\n", 2)
    meta = yaml.safe_load(fm)
    if meta.get("id") != path.stem:
        raise ValueError(f"{path}: id={meta.get('id')!r} לא תואם לשם הקובץ")
    return meta, body


def load_events():
    """כל הרעידות, ממוינות לפי שנה."""
    events = []
    for path in sorted(EVENTS_DIR.glob("*.md")):
        meta, body = read_event(path)
        meta["body"] = body
        events.append(meta)
    events.sort(key=lambda e: (e["date"]["year"], e["date"].get("month") or 0, e["date"].get("day") or 0))
    return events


def main():
    events = load_events()
    public = [{k: v for k, v in e.items() if k != "body"} for e in events]
    OUT.write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(public)} events to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
