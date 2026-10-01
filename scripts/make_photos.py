"""המרת תמונה מקורית לקובצי האתר: static/img/photos/<id>.webp (עד 1200 פיקסלים ברוחב)
ו-<id>-640.webp (לטלפונים). הפרטים (כיתוב, קרדיט, רישיון) ב-data/images.yaml.

    python3 scripts/make_photos.py <id> <קובץ מקור> [<id> <קובץ מקור> ...]
"""

import sys
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "static" / "img" / "photos"
SIZES = {"": 1200, "-640": 640}


def convert(key, src):
    im = Image.open(src)
    im = im.convert("RGB") if im.mode not in ("RGB", "L") else im
    OUT.mkdir(parents=True, exist_ok=True)
    for suffix, width in SIZES.items():
        copy = im.copy()
        if copy.width > width:
            copy = copy.resize((width, round(copy.height * width / copy.width)), Image.LANCZOS)
        copy.save(OUT / f"{key}{suffix}.webp", "WEBP", quality=78, method=6)
    print(key, im.size)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or len(args) % 2:
        sys.exit(__doc__)
    for key, src in zip(args[::2], args[1::2]):
        convert(key, src)
