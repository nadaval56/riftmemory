# השבר — riftmemory

אתר סטטי על רעידות האדמה בארץ ישראל: דף לכל רעידה היסטורית, ציר זמן,
ופס "רעידה אחרונה" שמתעדכן כל שעה עם "הד היסטורי". המדריך המלא: `docs/guide.pdf`.

## הרצה מקומית

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/build_events.py
.venv/bin/python scripts/build_site.py --drafts   # כולל טיוטות, לתצוגה מקומית בלבד
cd scripts && ../.venv/bin/python check_site.py   # בדיקות פרק 10
```

האתר נבנה ל-`site/`. בלי `--drafts` נבנים רק דפים עם `status: published`.
הנתיבים באתר מתחילים ב-`BASE_PATH` (ברירת מחדל `/riftmemory`). לתצוגה
מקומית: `BASE_PATH= .venv/bin/python scripts/build_site.py --drafts` ואז
`python3 -m http.server -d site`.

## איך מפרסמים רעידה

1. עוברים על `content/events/<id>.md`: ה-frontmatter, `review_notes`, וכל TODO בגוף.
2. משנים `status: draft` ל-`reviewed`, ואחרי בדיקה ל-`published`.
3. `check_site.py` נכשל אם בדף published נשאר TODO, מקור חסר או ניסוח חיזויי.

## מקטעי השבר

`data/segments.json`: מלבנים גסים. כל מקטע מתחיל עם `approved: false`.
רק מקטע מאושר מוצג במפה ומשתתף ב"הד ההיסטורי".

## Workflows

- `build.yml`: בכל push ל-main — בנייה, בדיקות ופרסום ל-GitHub Pages.
- `live.yml`: כל שעה — `fetch_live.py` (המכון הגיאולוגי, ואם נכשל USGS ואז EMSC),
  `echo.py`, שמירת `data/live/latest.json`, בנייה ופרסום.
- `fetch.yml`: משיכת ויקיפדיה ובדיקת מקורות. מופעל ידנית, או ב-push של
  `.github/fetch-request` (שם משימה בכל שורה) ל-branch שאינו main.
  התוצאה נשמרת כ-commit על אותו branch.
