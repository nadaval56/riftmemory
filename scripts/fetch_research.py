"""משיכת מחקרים ומקורות לבדיקת עובדות (לא לפרסום).

קלט: .github/research-urls.txt (או קובץ אחר כארגומנט שני), שורה לכל מקור: "<slug> <url>".
שורה בצורה "<slug> <url> | מילה;מילה" שומרת רק קטעים קצרים סביב מילות המפתח (מצב קטעים),
למקורות מוגנים בזכויות יוצרים שפתוחים לקריאה: מספיק לאימות, בלי לשמור את הטקסט המלא.
פלט: תיקייה (ברירת מחדל research-out/) עם <slug>.txt (הטקסט) ו-<slug>.links.txt
(הקישורים שבדף, לדפי HTML). ה-workflow מצפין את הפלט לפני שהוא נשמר בריפו,
כדי לא לפרסם מחדש חומר מוגן בזכויות יוצרים.
"""

import shutil
import subprocess
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import requests

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (riftmemory research; https://github.com/nadaval56/riftmemory)"}


class Text(HTMLParser):
    SKIP = {"script", "style", "noscript"}
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "table", "blockquote", "section"}

    def __init__(self, base):
        super().__init__()
        self.base, self.out, self.links, self._skip, self._href = base, [], [], 0, None

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1
        if tag in self.BLOCK:
            self.out.append("\n")
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._atext = []

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self._skip -= 1
        if tag == "a" and self._href:
            self.links.append(f"{urljoin(self.base, self._href)}\t{' '.join(self._atext).strip()}")
            self._href = None

    def handle_data(self, data):
        if self._skip:
            return
        self.out.append(data)
        if self._href:
            self._atext.append(data.strip())


EXCERPT_CONTEXT = 4   # שורות לפני ואחרי כל התאמה
EXCERPT_MAX = 30      # מספר קטעים מרבי למקור


def excerpts(text, keywords):
    """רק השורות שסביב מילות המפתח, עם מספרי שורות."""
    lines = text.splitlines()
    keep, hits = set(), 0
    for i, line in enumerate(lines):
        if any(k.lower() in line.lower() for k in keywords):
            hits += 1
            if hits > EXCERPT_MAX:
                break
            keep.update(range(max(0, i - EXCERPT_CONTEXT), min(len(lines), i + EXCERPT_CONTEXT + 1)))
    out, prev = [], None
    for i in sorted(keep):
        if prev is not None and i != prev + 1:
            out.append("[...]")
        out.append(f"{i + 1}: {lines[i]}")
        prev = i
    return "\n".join(out)


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "research-out")
    urls = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / ".github" / "research-urls.txt"
    out.mkdir(parents=True, exist_ok=True)
    lines = urls.read_text(encoding="utf-8").splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        keywords = None
        if " | " in line:
            line, kw = line.split(" | ", 1)
            keywords = [k.strip() for k in kw.split(";") if k.strip()]
        slug, url = line.split(None, 1)
        try:
            r = requests.get(url, headers=UA, timeout=60)
            ctype = r.headers.get("content-type", "")
            print(f"{slug}: {r.status_code} {ctype} {len(r.content)}")
            if r.status_code != 200:
                (out / f"{slug}.txt").write_text(f"HTTP {r.status_code}\n{r.text[:2000]}", encoding="utf-8")
                continue
            if "pdf" in ctype or r.content[:4] == b"%PDF":
                pdf = out / f"{slug}.pdf"
                pdf.write_bytes(r.content)
                txt = out / f"{slug}.txt"
                subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], check=False)
                # PDF סרוק בלי שכבת טקסט: זיהוי תווים (OCR) עם tesseract, אם הוא מותקן
                if (not txt.exists() or txt.stat().st_size < 2000) and shutil.which("tesseract"):
                    pages = out / f"{slug}-pages"
                    pages.mkdir(exist_ok=True)
                    subprocess.run(["pdftoppm", "-r", "300", "-gray", "-png", str(pdf), str(pages / "p")], check=False)
                    parts = []
                    for img in sorted(pages.glob("p-*.png")):
                        res = subprocess.run(["tesseract", str(img), "-", "-l", "eng"], capture_output=True, text=True)
                        parts.append(f"\n\n=== {img.stem} ===\n" + res.stdout)
                    txt.write_text(f"SOURCE: {url} (OCR)\n" + "".join(parts), encoding="utf-8")
                    shutil.rmtree(pages)
                pdf.unlink()
            else:
                r.encoding = r.encoding or r.apparent_encoding
                p = Text(url)
                p.feed(r.text)
                text = "".join(p.out)
                text = "\n".join(l.rstrip() for l in text.splitlines())
                while "\n\n\n" in text:
                    text = text.replace("\n\n\n", "\n\n")
                (out / f"{slug}.txt").write_text(f"SOURCE: {url}\n\n{text}", encoding="utf-8")
                (out / f"{slug}.links.txt").write_text("\n".join(p.links), encoding="utf-8")
            txt = out / f"{slug}.txt"
            if keywords and txt.exists():
                full = txt.read_text(encoding="utf-8", errors="replace")
                txt.write_text(f"SOURCE: {url}\nEXCERPTS ONLY (מקור מוגן; רק קטעים סביב: {'; '.join(keywords)})\n\n"
                               + excerpts(full, keywords), encoding="utf-8")
                links = out / f"{slug}.links.txt"
                if links.exists():
                    links.unlink()
        except Exception as exc:  # noqa: BLE001
            print(f"{slug}: failed {exc!r}")
            (out / f"{slug}.txt").write_text(f"ERROR {exc!r}", encoding="utf-8")
        time.sleep(1)


if __name__ == "__main__":
    main()
