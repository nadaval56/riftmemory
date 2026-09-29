"""עיצוב תאריכים, שנים ומספרים לתצוגה בעברית (פרק 7, "שנה לפני הספירה").

טווחים נכתבים במילים ("בין 128 ל-131") ולא עם מקף, כדי שלא יתהפכו בטקסט RTL.
"""

MONTHS_HE = [
    None, "בינואר", "בפברואר", "במרץ", "באפריל", "במאי", "ביוני",
    "ביולי", "באוגוסט", "בספטמבר", "באוקטובר", "בנובמבר", "בדצמבר",
]

BCE = "לפנה״ס"

MAG_TYPES = {
    "Mw": "מגניטודת מומנט (Mw)",
    "ML": "מגניטודה מקומית (ML)",
    "estimated-historical": "הערכה היסטורית",
}

MAG_BASIS = {
    "instrumental": "מדידה מכשירית",
    "historical-estimate": "הערכה לפי תיאורי נזק",
}


def year(y):
    """1927 -> "1927", -31 -> "31 לפנה״ס"."""
    if y is None:
        return ""
    return f"{-y} {BCE}" if y < 0 else str(y)


def year_short(y):
    """לשימוש במשפטי ההד: אותו דבר, בלי שינוי לשנים לספירה."""
    return year(y)


def year_range(a, b):
    if a < 0 and b < 0:
        return f"בין {-a} ל-{-b} {BCE}"
    if a < 0 <= b:
        return f"בין {-a} {BCE} ל-{b}"
    return f"בין {a} ל-{b}"


def event_date(date):
    """תאריך רעידה היסטורית, עם רמת הוודאות שלו."""
    y, rng, cert = date.get("year"), date.get("year_range"), date.get("certainty")
    if cert == "disputed" and rng:
        text = year_range(*rng)
        if date.get("month") and date.get("day"):
            text += f" (לפי מקור אחד: {date['day']} {MONTHS_HE[date['month']]} {year(y)})"
        return text
    text = year(y)
    if date.get("month"):
        text = f"{MONTHS_HE[date['month']]} {text}"
        if date.get("day"):
            text = f"{date['day']} {text}"
    if cert == "approximate":
        text = f"בערך {text}"
    return text


def event_year_label(e):
    """שנה קצרה לתוויות (ציר זמן, רשימות)."""
    d = e["date"]
    if d.get("certainty") == "disputed" and d.get("year_range"):
        return year_range(*d["year_range"])
    prefix = "בערך " if d.get("certainty") == "approximate" else ""
    return prefix + year(d["year"])


def number(n):
    """285 -> "285", 30000 -> "30,000"."""
    if n is None:
        return ""
    if isinstance(n, float) and not n.is_integer():
        return f"{n:,}"
    return f"{int(n):,}"


def magnitude(m):
    if not m:
        return ""
    if m.get("range"):
        a, b = m["range"]
        text = f"בין {a} ל-{b}"
        if m.get("value") is not None and m["value"] not in (a, b):
            text = f"{m['value']} ({text})"
        return text
    if m.get("value") is not None:
        return str(m["value"])
    return ""


def mag_type(t):
    return MAG_TYPES.get(t, t or "")


def mag_basis(b):
    return MAG_BASIS.get(b, b or "")


def event_year_compact(e):
    """שנה קצרה לציר הזמן: "בערך 130" במקום טווח מלא."""
    d = e["date"]
    prefix = "בערך " if d.get("certainty") in ("approximate", "disputed") else ""
    return prefix + year(d["year"])
