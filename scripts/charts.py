"""גרפים קטנים כ-SVG שנוצרים בזמן הבנייה: עמודות וחתך עומק.

כמו בציר הזמן, הזמן זורם מימין לשמאל: העמודה הראשונה ברשימה היא הימנית.
ה-SVG יורש direction=rtl מהדף, ולכן text-anchor="start" הוא הקצה הימני.
צבעים דרך מחלקות CSS (chart-*), כדי שמצב כהה יעבוד.
"""

from html import escape

RLM = "‏"


def _t(text):
    return RLM + escape(str(text))


def bars(items, width=640, height=160, label_every=1, title=""):
    """items: רשימת (תווית, ערך, תיאור לריחוף). הראשון מימין."""
    n = len(items) or 1
    top, bottom, side = 16, 26, 4
    ch = height - top - bottom
    peak = max((v for _, v, _ in items), default=0) or 1
    bw = (width - 2 * side) / n
    out = [f'<svg class="chart chart-bars" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">']
    out.append(f'<line class="chart-axis" x1="{side}" x2="{width - side}" y1="{top + ch}" y2="{top + ch}"/>')
    for i, (label, value, tip) in enumerate(items):
        x = width - side - (i + 1) * bw
        h = ch * value / peak
        y = top + ch - h
        out.append(f'<g class="chart-hit" data-tip="{escape(tip)}"><title>{escape(tip)}</title>'
                   f'<rect class="chart-bar" x="{x + bw * 0.15:.1f}" y="{y:.1f}" width="{bw * 0.7:.1f}" height="{max(h, 0):.1f}" rx="1.5"/>')
        if value:
            out.append(f'<text class="chart-val" x="{x + bw / 2:.1f}" y="{y - 3:.1f}" text-anchor="middle">{value}</text>')
        out.append('</g>')
        if label and i % label_every == 0:
            out.append(f'<text class="chart-label" x="{x + bw / 2:.1f}" y="{height - 8}" text-anchor="middle">{_t(label)}</text>')
    out.append('</svg>')
    return "\n".join(out)


LABEL_ANGLE = 40  # מעלות. תוויות המקטעים מוטות, כדי שגם מקטעים צרים יקבלו שם קריא


def depth_section(points, x_range, depth_max, bands=(), width=420, height=280, title="", x_labels=()):
    """חתך עומק. points: (x, depth_km, mag, תיאור ללחיצה). x_range: (ימין, שמאל) בערכי x.
    bands: (x1, x2, תווית) — רצועות רקע, למשל המקטעים. x_labels: (x, תווית).
    הערכים המקוריים נשמרים ב-data-*, כדי ש-site.js יוכל לקרב (צביטה, כפתורים) ולצייר מחדש
    בלי שהנקודות והטקסט יגדלו יחד עם הזום."""
    top, bottom, left_pad, right_pad = 84, 22, 26, 4
    cw, ch = width - left_pad - right_pad, height - top - bottom
    x_right, x_left = x_range

    def px(x):
        return width - right_pad - (x - x_right) / (x_left - x_right) * cw

    def py(d):
        return top + min(d, depth_max) / depth_max * ch

    out = [f'<svg class="chart chart-depth" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}"'
           f' data-zoom data-x0="{x_right}" data-x1="{x_left}" data-dmax="{depth_max}"'
           f' data-l="{left_pad}" data-r="{right_pad}" data-t="{top}" data-b="{bottom}" data-w="{width}" data-h="{height}">']
    out.append(f'<defs><clipPath id="depth-clip"><rect x="{left_pad}" y="{top - 6}" width="{cw}" height="{ch + 12}"/></clipPath></defs>')
    out.append('<g class="cz-plot" clip-path="url(#depth-clip)">')
    for i, (x1, x2, label) in enumerate(bands):
        a, b = sorted((px(x1), px(x2)))
        out.append(f'<rect class="chart-band b{i % 2}" x="{a:.1f}" y="{top}" width="{b - a:.1f}" height="{ch}" data-x1="{x1}" data-x2="{x2}"/>')
    out.append('<g class="cz-grid">')
    for d in range(0, int(depth_max) + 1, 10):
        out.append(f'<line class="chart-grid" x1="{left_pad}" x2="{width - right_pad}" y1="{py(d):.1f}" y2="{py(d):.1f}"/>')
    out.append('</g>')
    for x, d, m, tip in sorted(points, key=lambda p: p[2]):
        if d is None:
            continue
        r = max(1.2, (m - 2) * 1.1)
        # לחיצה או נגיעה בנקודה פותחת תווית (static/js/site.js, [data-tip])
        out.append(f'<circle class="chart-dot chart-hit" cx="{px(x):.1f}" cy="{py(d):.1f}" r="{r:.1f}" data-x="{x}" data-d="{d}"'
                   f' data-tip="{escape(tip)}"><title>{escape(tip)}</title></circle>')
    out.append('</g>')
    # תוויות המקטעים: מוטות, מעוגנות במרכז הרצועה (text-anchor="end" הוא הקצה השמאלי, כי הכיוון rtl)
    out.append('<g class="cz-bands">')
    for x1, x2, label in bands:
        cx = (px(x1) + px(x2)) / 2
        out.append(f'<text class="chart-band-label" x="0" y="0" text-anchor="end" data-x1="{x1}" data-x2="{x2}"'
                   f' transform="translate({cx:.1f},{top - 5}) rotate(-{LABEL_ANGLE})">{_t(label)}</text>')
    out.append('</g><g class="cz-ylabels">')
    for d in range(0, int(depth_max) + 1, 10):
        out.append(f'<text class="chart-label" x="{left_pad - 4}" y="{py(d) + 4:.1f}" text-anchor="end" direction="ltr">{d}</text>')
    out.append('</g><g class="cz-xlabels">')
    for x, label in x_labels:
        out.append(f'<text class="chart-label" x="{px(x):.1f}" y="{height - 6}" text-anchor="middle">{_t(label)}</text>')
    out.append('</g></svg>')
    return "\n".join(out)


def hbars(items, unit=""):
    """עמודות אופקיות ב-HTML (הטקסט גדל עם הגדרות הקורא). items: (תווית, ערך)."""
    peak = max((v for _, v in items), default=0) or 1
    rows = []
    for label, value in items:
        rows.append(f'<div class="hb-row"><span class="hb-label">{escape(label)}</span>'
                    f'<span class="hb-track"><span class="hb-bar" style="width:{100 * value / peak:.1f}%"></span></span>'
                    f'<span class="hb-val">{value}{escape(unit)}</span></div>')
    return '<div class="hbars">' + "".join(rows) + "</div>"
