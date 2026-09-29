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
        out.append(f'<g><title>{escape(tip)}</title>'
                   f'<rect class="chart-bar" x="{x + bw * 0.15:.1f}" y="{y:.1f}" width="{bw * 0.7:.1f}" height="{max(h, 0):.1f}" rx="1.5"/>')
        if value:
            out.append(f'<text class="chart-val" x="{x + bw / 2:.1f}" y="{y - 3:.1f}" text-anchor="middle">{value}</text>')
        out.append('</g>')
        if label and i % label_every == 0:
            out.append(f'<text class="chart-label" x="{x + bw / 2:.1f}" y="{height - 8}" text-anchor="middle">{_t(label)}</text>')
    out.append('</svg>')
    return "\n".join(out)


def depth_section(points, x_range, depth_max, bands=(), width=640, height=260, title="", x_labels=()):
    """חתך עומק. points: (x, depth_km, mag). x_range: (ימין, שמאל) בערכי x.
    bands: (x1, x2, תווית) — רצועות רקע, למשל המקטעים. x_labels: (x, תווית)."""
    top, bottom, left_pad, right_pad = 22, 22, 34, 6
    cw, ch = width - left_pad - right_pad, height - top - bottom
    x_right, x_left = x_range

    def px(x):
        return width - right_pad - (x - x_right) / (x_left - x_right) * cw

    def py(d):
        return top + min(d, depth_max) / depth_max * ch

    out = [f'<svg class="chart chart-depth" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">']
    for i, (x1, x2, label) in enumerate(bands):
        a, b = sorted((px(x1), px(x2)))
        out.append(f'<rect class="chart-band b{i % 2}" x="{a:.1f}" y="{top}" width="{b - a:.1f}" height="{ch}"/>')
        out.append(f'<text class="chart-band-label" x="{(a + b) / 2:.1f}" y="{top - 7}" text-anchor="middle">{_t(label)}</text>')
    for d in range(0, int(depth_max) + 1, 10):
        y = py(d)
        out.append(f'<line class="chart-grid" x1="{left_pad}" x2="{width - right_pad}" y1="{y:.1f}" y2="{y:.1f}"/>')
        out.append(f'<text class="chart-label" x="{left_pad - 4}" y="{y + 4:.1f}" text-anchor="end" direction="ltr">{d}</text>')
    for x, label in x_labels:
        out.append(f'<text class="chart-label" x="{px(x):.1f}" y="{height - 6}" text-anchor="middle">{_t(label)}</text>')
    for x, d, m in sorted(points, key=lambda p: p[2]):
        if d is None:
            continue
        r = max(1.2, (m - 1.5) * 1.3)
        out.append(f'<circle class="chart-dot" cx="{px(x):.1f}" cy="{py(d):.1f}" r="{r:.1f}"/>')
    out.append('</svg>')
    return "\n".join(out)
