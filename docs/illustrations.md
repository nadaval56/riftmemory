# איורים לדפים בלי תמונות (מידג'רני)

**מצב (אוקטובר 2026):** נבחר סגנון רישום בדיו וצבעי מים (במקום הלינוליאום שלמטה). רפרנס סגנון: העבודה
a992194e-f909-4162-b937-a8119cdc9137 בחשבון של נדב. `--sref` מקבל רק כתובת של תמונה (לא קוד עבודה); כתובת קבועה: "Web" ← העתקת כתובת התמונה (cdn.midjourney.com). קישורי Discord פגים אחרי כיום. רישיון האיורים: CC BY 4.0.
שולבו כל השישה: 31 לפנה"ס (ill-qumran), 130 (ill-chronicle), 881 (ill-catalogues), 1033 (ill-harbour), 1068 (ill-ramla), 1834 (ill-jerusalem-siege).
לכל פרומפט בסגנון החדש: `loose contemporary pen and ink sketch with light watercolour washes, ... quick confident linework, mostly white paper, touches of terracotta and pale blue, urban-sketcher style --sref ... --ar 16:9 --style raw --no text, letters, signature, people`

אחרי ששולבו התמונות מוויקישיתוף (data/images.yaml), נשארו שישה דפי רעידות בלי שום תמונה:
31 לפנה"ס, 130, 881, 1033, 1068 ו-1834. לדפים האלה מוצע איור אחד לכל דף.

## הכללים

1. **צריך להיות ברור שזה איור.** הסגנון שטוח, דו-צבעי, בסגנון חיתוך לינוליאום, ולא מנסה להיראות כמו צילום או ציור תקופתי.
   בכיתוב תמיד מופיעה המילה "איור", ובשורת הקרדיט: "איור: נדב, בעזרת Midjourney".
2. **האיור לא מוסיף עובדות.** בכל סצנה יש רק מה שכבר כתוב בדף עם מקור, או נוף כללי של המקום.
   לא מציירים פרט שאין לו מקור, כמו מספר קורבנות, בניין מסוים שקרס או גל שלא תועד.
3. **סגנון אחיד בכל האיורים.** אותה סיומת לכל הפרומפטים, ואותו יחס גובה-רוחב (16:9).
   הצבעים קרובים לצבעי האתר: נייר בהיר חמים, טרקוטה ופחם.
4. **בלי טקסט ובלי אותיות באיור.** מידג'רני משבש אותיות, ובמיוחד עברית.

## הסיומת הקבועה

```
flat two-colour linocut print, terracotta and charcoal ink on warm off-white paper, bold simple shapes, visible paper grain, limited palette, calm composition, editorial illustration, no text, no letters, no people's faces, not photorealistic --ar 16:9 --style raw
```

## הפרומפטים

### 31 לפנה"ס — רעידת האדמה ביהודה
מה בדף: יוסף בן מתתיהו, וקומראן שמעל ים המלח.
```
the ruins of Qumran on a dry marl plateau above the Dead Sea, steep desert cliffs with cave openings behind, a single thin crack running across the plateau toward the sea, early morning light, [סיומת]
```

### 130 — רעידת האדמה ביהודה
מה בדף: שורה אחת בכרוניקון של אוסביוס. האיור מציג את המקור, לא את הרעידה.
```
an old leather-bound chronicle lying open on a wooden desk, columns of illegible handwriting, one single line marked with a terracotta stroke, a small oil lamp beside it, [סיומת]
```

### 881 — רעידת האדמה בעכו
מה בדף: הדיווח על הגל הגיע דרך קטלוגים, והחקירה מראה שהוא שגוי. לכן אין בסצנה גל.
```
a stack of old scientific catalogues and loose index cards on a table, an antique coastal map of a walled harbour town lying under them, a magnifying glass, [סיומת]
```

### 1033 — רעידת האדמה בבקעת הירדן
מה בדף: הים שנסוג מנמל עכו. הנסיגה מתועדת במקורות שבדף.
```
a medieval walled harbour town seen from the sea, the water drawn far back from the harbour, small wooden boats resting on the exposed wet seabed, gulls, an uneasy still sky, [סיומת]
```

### 1068 — רעידת האדמה במזרח הקרוב
מה בדף: שתי רעידות, הראשונה בדרום (אילה והערבה) והשנייה ברמלה.
```
diptych composition: on one side bare red desert mountains above the northern tip of a narrow gulf, on the other side a low walled town in a flat sandy coastal plain with palm trees, a thin crack line connecting the two halves, [סיומת]
```

### 1834 — רעידת האדמה בירושלים
מה בדף: הרעידה פגעה בירושלים בזמן המצור של מרד הפלאחים.
```
the walls and domes of old Jerusalem seen from a distance at dusk, a military tent camp on the hills outside the walls, fine cracks in the city wall, [סיומת]
```

## אחרי שיש איורים

1. מעלים את האיור (PNG או JPG) לשיחה, או ל-`static/img/illustrations/incoming/` דרך GitHub.
2. אני ממיר אותו ל-WebP (`scripts/make_photos.py`), מוסיף רשומה ל-`data/images.yaml` עם `credit: 'איור: נדב, בעזרת Midjourney'` ו-`license`, ומציב `[[fig:...]]` בדף.
3. הכיתוב פותח במילה "איור" ומתאר רק את מה שמצויר.

לגבי הרישיון: לפי תנאי השימוש של מידג'רני, למנויים בתשלום יש בעלות על התמונות שהם יוצרים. אפשר לציין "כל הזכויות שמורות" או לשחרר ב-CC BY. ההחלטה של נדב.
