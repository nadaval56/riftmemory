"""מייצר את האתר הסטטי בתיקייה site/ מתוך content/, data/, templates/ ו-static/.

בשלב 0 זה שלד בלבד: יוצר site/ עם דף זמני, כדי שה-Action יוכל לפרסם.
"""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

PLACEHOLDER = """<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>השבר</title>
</head>
<body>
<h1>השבר</h1>
<p>האתר בבנייה.</p>
</body>
</html>
"""


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    (SITE / "index.html").write_text(PLACEHOLDER, encoding="utf-8")
    shutil.copytree(ROOT / "static", SITE / "static", ignore=shutil.ignore_patterns(".gitkeep"))
    print(f"built {SITE}")


if __name__ == "__main__":
    main()
