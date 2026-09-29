"""ציר הזמן כ-SVG שנוצר בזמן הבנייה (פרק 6.3).

הציר מקוטע לפי תקופות: לכל תקופה רוחב קבוע, ובתוכה הסקאלה לינארית.
הזמן זורם מימין לשמאל (RTL) בגרסה האופקית, ומלמעלה למטה בגרסה האנכית.
גודל נקודה לפי מגניטודה, צבע לפי סוג הראיה, טווח תאריכים כקו.
ה-SVG יורש direction=rtl מהדף, ולכן text-anchor="start" הוא הקצה הימני.
"""

from html import escape as _escape

import fmt

ERAS = [
    # (התחלה, סוף, שם, משקל רוחב)
    (-800, 0, "לפני הספירה", 1.0),
    (0, 640, "העת העתיקה", 1.0),
    (640, 1517, "ימי הביניים", 1.1),
    (1517, 2030, "העת החדשה", 1.6),
]
INSTRUMENTS_YEAR = 1900

RLM = "\u200f"


def escape(text):
    """escape + סימן RLM בהתחלה, כדי שתווית שמתחילה בספרה תוצג מימין לשמאל."""
    return RLM + _escape(text)


KIND_LABELS = {
    "texts": "מקור כתוב",
    "archaeology": "ממצא ארכיאולוגי",
    "instrumental": "מדידה מכשירית",
}


def _kind(e):
    ev = e.get("evidence") or {}
    if ev.get("instrumental"):
        return "instrumental"
    if ev.get("archaeology"):
        return "archaeology"
    return "texts"


def _pos(year):
    """מיקום יחסי 0..1 על הציר המקוטע."""
    total = sum(w for *_, w in ERAS)
    acc = 0.0
    for start, end, _, w in ERAS:
        if year <= end or (start, end) == ERAS[-1][:2]:
            frac = min(max((year - start) / (end - start), 0.0), 1.0)
            return (acc + frac * w) / total
        acc += w
    return 1.0


def _era_bounds():
    total = sum(w for *_, w in ERAS)
    acc = 0.0
    out = []
    for start, end, name, w in ERAS:
        out.append((acc / total, (acc + w) / total, start, end, name))
        acc += w
    return out


def _radius(e):
    m = e.get("magnitude") or {}
    val = m.get("value")
    if val is None and m.get("range"):
        val = sum(m["range"]) / 2
    if val is None:
        return None
    return max(4.0, min(4.0 + (val - 5.5) * 3.2, 14.0))


def _spread(positions, min_gap):
    """מזיז תוויות כך שיהיה ביניהן לפחות min_gap, בלי לשנות את הסדר."""
    order = sorted(range(len(positions)), key=lambda i: positions[i])
    out = list(positions)
    last = None
    for i in order:
        if last is not None and out[i] < last + min_gap:
            out[i] = last + min_gap
        last = out[i]
    return out


def _label_width(text):
    """הערכה גסה של רוחב תווית בפיקסלים (12.5px)."""
    return len(text) * 6.8 + 6


def _boundary_label(y):
    if y == 0:
        return "ראשית הספירה"
    if y >= 2030:
        return "היום"
    return fmt.year(y)


def _dot(e, cx, cy, base):
    r = _radius(e)
    kind = "verdict" if e.get("verdict") else _kind(e)
    note = {"misattributed": " · יוחסה לארץ בטעות", "doubtful": " · כנראה לא התרחשה"}.get(e.get("verdict"), "")
    title = escape(f"{e['title']} · {fmt.event_year_label(e)}{note}")
    url = f"{base}/events/{e['id']}/"
    if r is None:
        shape = (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="7" class="dot k-{kind} no-mag"/>'
                 f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2" class="dot-center k-{kind}"/>')
    else:
        shape = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="dot k-{kind}"/>'
    return f'<a href="{url}" class="tl-event"><title>{title}</title>{shape}</a>'


def horizontal(events, base):
    W, H = 1000, 320
    left, right = 30, 970
    axis_y = 150

    def x(year):
        return right - _pos(year) * (right - left)

    parts = [f'<svg class="timeline timeline-h" viewBox="0 0 {W} {H}" role="img" '
             f'aria-label="ציר זמן של רעידות האדמה, מימין לשמאל">']

    for a, b, start, end, name in _era_bounds():
        xa, xb = right - a * (right - left), right - b * (right - left)
        parts.append(f'<rect x="{xb:.1f}" y="40" width="{xa - xb:.1f}" height="230" class="era-band"/>')
        parts.append(f'<text x="{(xa + xb) / 2:.1f}" y="30" class="era-name" text-anchor="middle">{name}</text>')
        parts.append(f'<line x1="{xa:.1f}" x2="{xa:.1f}" y1="40" y2="270" class="era-sep"/>')
        parts.append(f'<text x="{xa:.1f}" y="288" class="era-year" text-anchor="middle">{escape(_boundary_label(start))}</text>')
    parts.append(f'<text x="{left:.1f}" y="288" class="era-year" text-anchor="middle">היום</text>')

    xi = x(INSTRUMENTS_YEAR)
    parts.append(f'<line x1="{xi:.1f}" x2="{xi:.1f}" y1="48" y2="{H - 54}" class="instruments"/>')
    parts.append(f'<text x="{xi + 6:.1f}" y="{H - 58}" class="instruments-label" text-anchor="end">כאן מתחילים המכשירים</text>')

    parts.append(f'<line x1="{left}" x2="{right}" y1="{axis_y}" y2="{axis_y}" class="axis"/>')

    evs = sorted(events, key=lambda e: e["date"]["year"])
    xs = [x(e["date"]["year"]) for e in evs]
    # ארבעה מסלולי תוויות, שניים מעל הציר ושניים מתחתיו. כל תווית נכנסת
    # למסלול הראשון שבו היא לא עולה על התווית הקודמת.
    lanes = [axis_y - 30, axis_y + 40, axis_y - 62, axis_y + 72]
    lane_edge = [None] * len(lanes)  # הקצה השמאלי של התווית האחרונה בכל מסלול
    order = sorted(range(len(evs)), key=lambda i: -xs[i])  # מימין לשמאל
    for i in order:
        e = evs[i]
        w = _label_width(e["short_title"])
        lx = min(max(xs[i], left + w / 2), right - w / 2)
        lane = next((k for k, edge in enumerate(lane_edge) if edge is None or lx + w / 2 + 8 <= edge), None)
        if lane is None:
            lane = max(range(len(lanes)), key=lambda k: lane_edge[k])
            lx = lane_edge[lane] - 8 - w / 2
        lane_edge[lane] = lx - w / 2
        ly = lanes[lane]
        above = ly < axis_y
        leader_end = ly + 4 if above else ly - 13
        parts.append(f'<line x1="{xs[i]:.1f}" y1="{axis_y + (-8 if above else 8)}" x2="{lx:.1f}" y2="{leader_end}" class="leader"/>')
        parts.append(f'<a href="{base}/events/{e["id"]}/" class="tl-label">'
                     f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" class="label-title">{escape(e["short_title"])}</text></a>')

    for e in evs:
        rng = e["date"].get("year_range")
        if rng:
            parts.append(f'<line x1="{x(rng[0]):.1f}" x2="{x(rng[1]):.1f}" y1="{axis_y}" y2="{axis_y}" class="range k-{_kind(e)}"/>')
    for e, cx in zip(evs, xs):
        parts.append(_dot(e, cx, axis_y, base))

    parts.append("</svg>")
    return "\n".join(parts)


def vertical(events, base):
    W, H = 380, 1300
    top, bottom = 40, 1260
    axis_x = W - 130

    def y(year):
        return top + _pos(year) * (bottom - top)

    parts = [f'<svg class="timeline timeline-v" viewBox="0 0 {W} {H}" role="img" '
             f'aria-label="ציר זמן של רעידות האדמה, מלמעלה למטה">']

    for a, b, start, end, name in _era_bounds():
        ya, yb = top + a * (bottom - top), top + b * (bottom - top)
        parts.append(f'<rect x="{axis_x - 20}" y="{ya:.1f}" width="40" height="{yb - ya:.1f}" class="era-band"/>')
        parts.append(f'<line x1="{axis_x - 20}" x2="{W}" y1="{ya:.1f}" y2="{ya:.1f}" class="era-sep"/>')
        parts.append(f'<text x="{W - 4}" y="{ya + 16:.1f}" class="era-year" text-anchor="start">{escape(_boundary_label(start))}</text>')
        parts.append(f'<text x="{W - 4}" y="{(ya + yb) / 2:.1f}" class="era-name-v" text-anchor="start">{name}</text>')

    yi = y(INSTRUMENTS_YEAR)
    parts.append(f'<line x1="{axis_x - 20}" x2="{W - 70}" y1="{yi:.1f}" y2="{yi:.1f}" class="instruments"/>')
    parts.append(f'<text x="{W - 4}" y="{yi - 4:.1f}" class="instruments-label" text-anchor="start">כאן מתחילים</text>')
    parts.append(f'<text x="{W - 4}" y="{yi + 10:.1f}" class="instruments-label" text-anchor="start">המכשירים</text>')

    parts.append(f'<line x1="{axis_x}" x2="{axis_x}" y1="{top}" y2="{bottom}" class="axis"/>')

    evs = sorted(events, key=lambda e: e["date"]["year"])
    ys = [y(e["date"]["year"]) for e in evs]
    label_ys = _spread(ys, 24)
    lx = axis_x - 26
    for e, py, ly in zip(evs, ys, label_ys):
        parts.append(f'<line x1="{axis_x - 8}" y1="{py:.1f}" x2="{lx + 4}" y2="{ly:.1f}" class="leader"/>')
        parts.append(f'<a href="{base}/events/{e["id"]}/" class="tl-label">'
                     f'<text x="{lx:.1f}" y="{ly + 4:.1f}" text-anchor="start" class="label-title">{escape(e["short_title"])}</text></a>')

    for e in evs:
        rng = e["date"].get("year_range")
        if rng:
            parts.append(f'<line y1="{y(rng[0]):.1f}" y2="{y(rng[1]):.1f}" x1="{axis_x}" x2="{axis_x}" class="range k-{_kind(e)}"/>')
    for e, py in zip(evs, ys):
        parts.append(_dot(e, axis_x, py, base))

    parts.append("</svg>")
    return "\n".join(parts)
