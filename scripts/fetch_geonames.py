"""משיכת שמות מקומות וקואורדינטות מ-GeoNames (CC BY 4.0), לשכבת "מקומות שנפגעו" במפה.

רץ ב-Actions (fetch.yml, task "geonames"). נשמרים רק יישובים (מחלקה P) ואתרים
עתיקים והיסטוריים (ANS, RUIN, HSTS, CSTL, ...), בלי שאר השדות.
פלט: data/raw/geonames/places.tsv
"""

import csv
import io
import sys
import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "geonames" / "places.tsv"
COUNTRIES = ["IL", "PS", "JO", "LB", "SY", "EG", "SA", "GR", "CY"]
S_CODES = {"ANS", "RUIN", "HSTS", "CSTL", "TMPL", "CH", "MSTY", "PAL", "ARCH"}
UA = {"User-Agent": "riftmemory/0.1 (https://github.com/nadaval56/riftmemory)"}


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["geonameid", "name", "asciiname", "alternatenames", "lat", "lon", "fclass", "fcode", "country", "population"])
        for cc in COUNTRIES:
            r = requests.get(f"https://download.geonames.org/export/dump/{cc}.zip", headers=UA, timeout=180)
            r.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                text = z.read(f"{cc}.txt").decode("utf-8")
            for row in csv.reader(io.StringIO(text), delimiter="\t", quoting=csv.QUOTE_NONE):
                fclass, fcode = row[6], row[7]
                if fclass == "P" or (fclass == "S" and fcode in S_CODES):
                    w.writerow([row[0], row[1], row[2], row[3], row[4], row[5], fclass, fcode, row[8], row[14]])
                    n += 1
            print(cc, "ok", file=sys.stderr)
    print(f"{n} places -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
