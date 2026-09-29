"""משיכת מחקרים ומקורות לבדיקת עובדות (לא לפרסום).

קלט: .github/research-urls.txt (או קובץ אחר כארגומנט שני), שורה לכל מקור: "<slug> <url>".
פלט: תיקייה (ברירת מחדל research-out/) עם <slug>.txt (הטקסט) ו-<slug>.links.txt
(הקישורים שבדף, לדפי HTML). ה-workflow מצפין את הפלט לפני שהוא נשמר בריפו,
כדי לא לפרסם מחדש חומר מוגן בזכויות יוצרים.
"""

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


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "research-out")
    urls = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / ".github" / "research-urls.txt"
    out.mkdir(parents=True, exist_ok=True)
    lines = urls.read_text(encoding="utf-8").splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
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
                subprocess.run(["pdftotext", "-layout", str(pdf), str(out / f"{slug}.txt")], check=False)
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
        except Exception as exc:  # noqa: BLE001
            print(f"{slug}: failed {exc!r}")
            (out / f"{slug}.txt").write_text(f"ERROR {exc!r}", encoding="utf-8")
        time.sleep(1)


if __name__ == "__main__":
    main()
