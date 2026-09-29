"""שכבת "מקומות שנפגעו" במפה: המקומות שדפי הרעידות מתארים בהם נזק, עם קואורדינטות מ-GeoNames.

קלט:
  data/damage/places.json — חילוץ מתוך דפי הרעידות: לכל מקום, הרעידה, הסטטוס
    (reported / found / reported+found / doubtful / rejected), ההערות שתומכות בזה, והמשפט מהדף.
  data/raw/geonames/places.tsv — GeoNames (CC BY 4.0), fetch_geonames.py.
פלט: data/damage/sites.json — מקום אחד לכל נקודה, עם כל הרעידות שפגעו בו.

אלה מקומות שבהם תועד נזק, לא מוקדים של רעידות. מקומות שהמחקר דחה (rejected) לא מוצגים.
כל התאמה לא חד-משמעית מוגדרת כאן ידנית (GEONAMEID), ואחרת לפי השם ב-GeoNames.
"""

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACES = ROOT / "data" / "damage" / "places.json"
GEONAMES = ROOT / "data" / "raw" / "geonames" / "places.tsv"
OUT = ROOT / "data" / "damage" / "sites.json"

JERUSALEM = "281184"  # Jerusalem IL PPLA
# אתרים בתוך ירושלים מקובצים לנקודה אחת, והשם המדויק מופיע בחלון
IN_JERUSALEM = {"Al-Aqsa Mosque", "Christ Church, Jerusalem", "Church of the Holy Sepulchre",
                "City of David, Jerusalem", "Ophel, Jerusalem", "Petra Hotel, Jerusalem",
                "Temple Mount, Jerusalem", "Jerusalem"}

# התאמות ידניות: place_en -> geonameid (נבדקו מול השם, המדינה והסוג ב-GeoNames)
GEONAMEID = {
    "Antipatris": "Tel Afeq|IL|32.10532",
    "As-Salt": "As Salţ|JO",
    "Banias": "Bāniyās|IL",
    "Deir Alla": "Dayr ‘Allā|JO",
    "Ein Hatzeva": "H̱aẕeva|IL",
    "Emmaus Nicopolis": "Nicopolis|PS",
    "Gezer": "Tel Gezer|IL",
    "Hazor": "Tel H̱atsor|IL",
    "Hunin": "H̱orbat Metsudat Hunin|IL",
    "Khirbat al-Mafjar (Hisham's Palace)": "Qaşr Hishām|PS",
    "Nabratein": "H̱orbat Nevoraya|IL",
    "Nimrod Fortress": "Metsudat Nimrūd|IL",
    "Petra": "Petra|JO|30.32982",
    "Qumran": "Khirbat Qumrān|IL",
    "Rashaya": "Râchaïya el Ouadi|LB",
    "Rmeish": "Rmaych|LB",
    "Sepphoris": "Tel Tsippori|IL",
    "Tafilah": "Aţ Ţafīlah|JO",
    "Tel Ateret (Vadum Iacob)": "Metsad ‘Ateret|IL",
    "Umm ar-Rasas": "Umm ar Raşāş|JO|31.51225",
    "Zoara (Ghor as-Safi)": "Safi|JO",
    "al-Badhan": "Al Bādhān|PS",
}
# בלי נקודה: ים/אגם, זיהוי לא ודאי, או מחוץ לנתוני GeoNames שנמשכו (טורקיה)
SKIP = {"Dead Sea", "Mediterranean Sea", "Sea of Galilee", "Eroge (En Rogel), Jerusalem",
        "Evrona playa", "Nahal Tze'elim", "Mount Tabor", "Neocaesarea (Niksar)", "Nicaea (Iznik)",
        "Nicopolis (Pontus, Koyulhisar)", "Nahal Darga", "Nahal Tze'elim (Ze'elim terrace)", "Valletta"}
REGION_COUNTRIES = ("IL", "PS", "JO", "LB", "SY")


def load_geonames():
    rows = list(csv.DictReader(GEONAMES.open(encoding="utf-8"), delimiter="\t"))
    by_id = {r["geonameid"]: r for r in rows}
    idx = {}
    for r in rows:
        names = {r["name"], r["asciiname"]} | {a for a in r["alternatenames"].split(",") if a}
        for n in names:
            idx.setdefault(n.lower(), []).append(r)
    return rows, by_id, idx


def resolve(place_en, rows, by_id, idx):
    if place_en in IN_JERUSALEM:
        return by_id[JERUSALEM]
    if place_en in GEONAMEID:
        name, country, *lat = GEONAMEID[place_en].split("|")
        hits = [r for r in rows if r["name"] == name and r["country"] == country
                and (not lat or r["lat"].startswith(lat[0]))]
        if len(hits) != 1:
            raise SystemExit(f"{place_en}: {len(hits)} התאמות ל-{name}")
        return hits[0]
    forms = [place_en, re.sub(r"\s*\(.*?\)", "", place_en)] + re.findall(r"\((.*?)\)", place_en)
    forms += [f.split(",")[0] for f in forms]
    cands = [r for f in forms for r in idx.get(f.strip().lower(), [])]
    local = [r for r in cands if r["country"] in REGION_COUNTRIES] or cands
    local.sort(key=lambda r: (r["fclass"] != "P", -int(r["population"] or 0)))
    return local[0] if local else None


def main():
    places = json.loads(PLACES.read_text(encoding="utf-8"))
    rows, by_id, idx = load_geonames()
    sites, missing = {}, set()
    for p in places:
        if p["kind"] == "region" or p["status"] == "rejected" or p["place_en"] in SKIP:
            continue
        r = resolve(p["place_en"], rows, by_id, idx)
        if r is None:
            missing.add(p["place_en"])
            continue
        site = sites.setdefault(r["geonameid"], {
            "geonameid": r["geonameid"], "name_gn": r["name"],
            "lat": round(float(r["lat"]), 4), "lon": round(float(r["lon"]), 4),
            "place_he": "ירושלים" if r["geonameid"] == JERUSALEM else p["place_he"],
            "entries": [],
        })
        site["entries"].append({
            "event": p["event"], "place_he": p["place_he"], "status": p["status"],
            "evidence": p["evidence"], "footnotes": p["footnotes"],
        })
    out = sorted(sites.values(), key=lambda s: s["place_he"])
    OUT.write_text(json.dumps({
        "source": "מקומות: דפי הרעידות באתר. קואורדינטות: GeoNames (geonames.org), CC BY 4.0",
        "sites": out,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(out)} sites -> {OUT.relative_to(ROOT)}")
    if missing:
        print("no match:", ", ".join(sorted(missing)))


if __name__ == "__main__":
    main()
