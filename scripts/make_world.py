"""קו החוף של העולם, למפה הקטנה ברובריקה "רעידות חזקות בעולם" (דף 30 הימים).

המקור: Natural Earth, ne_110m_land (נחלת הכלל). הפלט הוא מסלול SVG אחד
בהיטל שווה-מרחקים (מעלה = יחידה), מעוגל למעלה שלמה כדי שיהיה קטן מספיק
להטמעה בדף. הקו המפריד של המפה עובר במצר ברינג (CUT), כדי שהאוקיינוס השקט
יהיה שלם; אנטארקטיקה לא מצוירת (המפה נחתכת ב-SOUTH).

הרצה (פעם אחת, התוצאה נשמרת בריפו):
  python scripts/make_world.py <ne_110m_land.geojson>
המקור: https://github.com/nvkelso/natural-earth-vector (geojson/ne_110m_land.geojson).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "world_land.json"

CUT = -169.0          # קו האורך שבו המפה נחתכת
NORTH, SOUTH = 80, -58


def x_of(lon):
    """מקו האורך למרחק מהקצה המערבי של המפה (CUT), במעלות."""
    return (lon - CUT) % 360


def unwrap(ring):
    """x רציף לאורך הטבעת (בלי קפיצה של 360 בקו החיתוך)."""
    xs = [x_of(ring[0][0])]
    for lon, _ in ring[1:]:
        x = x_of(lon)
        while x - xs[-1] > 180:
            x -= 360
        while xs[-1] - x > 180:
            x += 360
        xs.append(x)
    return xs


def ring_path(xs, ring, shift=0):
    pts, last = [], None
    for x, (_, lat) in zip(xs, ring):
        p = (round(x + shift), round(NORTH - lat))
        if p != last:
            pts.append(p)
            last = p
    if len(pts) < 3:
        return ""
    out = [f"M{pts[0][0]} {pts[0][1]}"]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        out.append(f"l{x1 - x0} {y1 - y0}")
    return "".join(out) + "z"


def main(src):
    data = json.loads(Path(src).read_text(encoding="utf-8"))
    parts = []
    for f in data["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            ring = poly[0]
            if max(lat for _, lat in ring) < SOUTH:
                continue  # אנטארקטיקה
            xs = unwrap(ring)
            parts.append(ring_path(xs, ring))
            # טבעת שחוצה את קו החיתוך מצוירת פעמיים, משני צדי המפה
            if max(xs) > 360:
                parts.append(ring_path(xs, ring, -360))
            if min(xs) < 0:
                parts.append(ring_path(xs, ring, 360))
    path = "".join(p for p in parts if p)
    OUT.write_text(json.dumps({
        "source": "Natural Earth, ne_110m_land (public domain)",
        "cut": CUT, "north": NORTH, "south": SOUTH, "path": path,
    }) + "\n", encoding="utf-8")
    print(f"{len(path)} chars -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
