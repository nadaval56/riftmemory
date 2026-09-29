"""מפת בסיס מקומית מתוך Natural Earth (נחלת הכלל), בלי שרת אריחים חיצוני.

CARTO התחיל לדרוש מפתח API, ואריחי OSM הרגילים מסמנים שטחים צבאיים בפוליגונים
ורודים. לכן המפה נבנית משכבות שהאתר מאחסן בעצמו: ים, אגמים, נהרות ושמות ערים
(בעברית, מהשדה NAME_HE של Natural Earth). גבולות מדיניים לא מצוירים.

הרצה (פעם אחת, התוצאה נשמרת בריפו):
  python scripts/make_basemap.py <natural-earth-vector/geojson>
המקור: https://github.com/nvkelso/natural-earth-vector (קבצי 10m).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "data" / "basemap.json"

# אזור המפה: מכרתים ומצרים במערב עד סוריה וירדן במזרח
W, S, E, N = 23.5, 27.0, 40.0, 37.5
TOL = 0.004  # פישוט קווים, במעלות (כ-400 מ׳)

LAKES = {"Dead Sea", "Sea of Galilee"}
# ערים לפי Natural Earth. rank קובע מאיזו רמת זום השם מוצג.
CITIES = {
    "Jerusalem": 0, "Damascus": 0,
    "Tel Aviv": 1, "Amman": 1, "Beirut": 1, "Haifa": 1, "Beer Sheva": 1, "Al Aqabah": 1, "Gaza City": 1, "Cairo": 1, "Nicosia": 1, "Iraklio": 1,
    "Nazareth": 2, "Nablus": 2, "Al Khalil": 2, "Ramla": 2, "Irbid": 2, "Al Karak": 2, "Saida": 2,
    "Al Qunaytirah": 2, "Zahlé": 2, "Ṭarābulus": 2, "Ma'an": 2, "At Tafilah": 2, "As Salt": 2,
}


def clip_ring(ring):
    """Sutherland–Hodgman: חיתוך טבעת של מצולע למלבן האזור."""
    def clip(pts, inside, cross):
        out = []
        for i, cur in enumerate(pts):
            prev = pts[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cross(prev, cur))
        return out

    def at_x(x):
        return lambda a, b: [x, a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])]

    def at_y(y):
        return lambda a, b: [a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y]

    pts = ring[:-1] if ring and ring[0] == ring[-1] else ring
    for inside, cross in (
        (lambda p: p[0] >= W, at_x(W)), (lambda p: p[0] <= E, at_x(E)),
        (lambda p: p[1] >= S, at_y(S)), (lambda p: p[1] <= N, at_y(N)),
    ):
        if not pts:
            break
        pts = clip(pts, inside, cross)
    return pts + pts[:1] if len(pts) >= 3 else None


def simplify(pts, tol=TOL):
    """Douglas–Peucker."""
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    norm = (dx * dx + dy * dy) ** 0.5
    best, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / norm if norm else ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
        if d > best:
            best, idx = d, i
    if best <= tol:
        return [pts[0], pts[-1]]
    return simplify(pts[: idx + 1], tol)[:-1] + simplify(pts[idx:], tol)


def rnd(pts):
    return [[round(x, 3), round(y, 3)] for x, y in pts]


def polygons(geom):
    return [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]


def clip_polys(geom):
    out = []
    for poly in polygons(geom):
        rings = []
        for ring in poly:
            c = clip_ring(ring)
            if c:
                c = simplify(c)
                if len(c) >= 4:
                    rings.append(rnd(c))
        if rings:
            out.append(rings)
    return out


def in_box(x, y):
    return W <= x <= E and S <= y <= N


def clip_line(line):
    """קטעי הקו שבתוך האזור (בלי חיתוך מדויק בשוליים, מספיק לתצוגה)."""
    parts, cur = [], []
    for x, y in line:
        if in_box(x, y):
            cur.append([x, y])
        elif cur:
            parts.append(cur)
            cur = []
    if cur:
        parts.append(cur)
    return [rnd(simplify(p)) for p in parts if len(p) >= 2]


def main():
    src = Path(sys.argv[1])
    load = lambda name: json.loads((src / name).read_text(encoding="utf-8"))["features"]

    sea = []
    for f in load("ne_10m_ocean.geojson"):
        sea += clip_polys(f["geometry"])

    lakes = []
    for f in load("ne_10m_lakes.geojson"):
        if f["properties"].get("name") in LAKES:
            lakes += clip_polys(f["geometry"])

    rivers = []
    for f in load("ne_10m_rivers_lake_centerlines.geojson"):
        g = f["geometry"]
        if g is None:
            continue
        lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        for line in lines:
            rivers += clip_line(line)

    cities = []
    for f in load("ne_10m_populated_places.geojson"):
        p = f["properties"]
        if p["NAME"] in CITIES:
            x, y = f["geometry"]["coordinates"]
            cities.append({"name": p["NAME_HE"], "lat": round(y, 3), "lon": round(x, 3), "rank": CITIES[p["NAME"]]})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "source": "Natural Earth 1:10m (naturalearthdata.com), נחלת הכלל",
        "bbox": [W, S, E, N],
        "sea": sea, "lakes": lakes, "rivers": rivers, "cities": cities,
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {len(sea)} sea polygons, {len(lakes)} lakes, "
          f"{len(rivers)} river lines, {len(cities)} cities, {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
