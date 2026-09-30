# משימת המשך: אימות מקורות דרך הדפדפן (JSTOR, Google Books ועוד)

המסמך הזה מיועד לסשן Claude Code **מקומי**, על המחשב של נדב, עם Claude in Chrome.
הסשן בענן לא יכול להגיע ל-JSTOR ול-Google. לפני שמתחילים, קרא את **CLAUDE.md**:
כללי התוכן שם מחייבים.

## המצב כרגע (30 בספטמבר 2026)
- כל 13 הרעידות מפורסמות. מקור שלא נבדק מול הטקסט עצמו מסומן בקוד
  `TODO: לבדוק במקור`, ובאתר הקורא רואה את התווית "טרם נבדק במקור".
- טענה בלי מקור בכלל מוסתרת כהערת HTML: `<!-- TODO: מקור ... -->`.
- אחרי שני סבבי אימות (ראו למטה) נשארו 63 תוויות "לבדוק במקור" (הרשימה המלאה בסוף המסמך).
  רובן נשענות על מקור משני שכבר נקרא, ורק המקור הראשוני לא נבדק.
- לנדב יש חשבון JSTOR חינמי ("Read online", מכסה חודשית של מאמרים).

## סבב 2 (30 בספטמבר 2026): מה נעשה
- JSTOR (שני המאמרים האחרונים של החודש; המכסה נגמרה): **Amiran, Arieh & Turcotte 1994** → `0031bce` (קבר יאסון), `0130` (לוד), `1033` (רעידת 4 בינואר 1034 ממוקמת אצלם בים מול עכו, לא בבקעה), `1068` ("a day's walk", נספח 5), `1834`, `1837` (ה-4,083 מופיע אצלם "according to an official report"), `1927`. **Brock 1977** → `0363` (מהדורת איגרת קירילוס).
- קלנר-עמירן 1950–1951, הערך על 1759 (עמ׳ 230) → `1759`.
- deadseaquake.info, נקראו הדפים עצמם → `0031bce`, `0130` (אין שם "שנה 13–14 לאדריאנוס"), `0363`, `0760bce` (חצור: בן-תור גם קיבל את פרשנות ידין), `1834`.
- ISC-GEM דרך USGS ועלון ISC → `1927` (שלושה מוקדים מכשיריים שונים; lat/lon לא שונו).

נשאר פתוח מהסבב הזה:
- Grigoratos et al. 2020: המאמר ב-Springer בתשלום, אבל ב-ETH Research Collection יש PDF פתוח (9.49MB, doi:10.3929/ethz-b-000534303), כנראה עבודת הדוקטור עם הקטלוג. לא הורד, כי הורדת קובץ דורשת אישור של נדב.
- Ben-Menahem 1991 (Wiley) בתשלום. Ferry 2007 (ScienceDirect) חסום ב-CAPTCHA.
- המכסה החינמית ב-JSTOR מתחדשת בחודש הבא: Lewis 1999 לא שם; מועמדים: מרגליות 1960 (תרביץ כט), מגנס 2010.

## סבב JSTOR (30 בספטמבר 2026, סשן מקומי עם Chrome): מה נעשה
נקראו ב-JSTOR (8 מתוך 10 המאמרים החינמיים של החודש):
- קלנר-עמירן, IEJ 1 (1950–1951) → `1033` (עמ׳ 227), `1927` (עמ׳ 234–236), `1834` (עמ׳ 230).
- עמירן, IEJ 2 (1952), עם הנספח של בן-חורין (עמ׳ 63–65) → `1837`. ה-4,083 נפתר: סכום עמודת ההרוגים בעמ׳ 63–64 (בדוח אין שורת סיכום).
- Russell 1980 → `0363`; Russell 1985 → `0130`. ההחלפה אדריאנוס←טראיאנוס (111/112) שיוחסה לראסל אינה במאמר.
- Tsafrir & Foerster, BSOAS 55 (1992), גרסה מתוקנת של תרביץ נח → `0749`.
- קרץ' ואלעד, תרביץ סא (עמ׳ 67–83) ומרגליות, ידיעות ח (תש"א) → `0749`.
- Meyers, Strange & Meyers, BASOR 246 (1982) → `0363`.

מחוץ ל-JSTOR: התקציר של Aldersons & Ben-Avraham 2014 ב-Springer → `1927` (מוקד מועדף 31.92, 35.56; lat/lon לא עודכנו, להחלטת נדב). החתם סופר, *תורת משה*, אמור, בספריא → `1837`.

נשאר פתוח:
- Lewis, *Levant* 31 (1999): לא ב-JSTOR (הוצאת Taylor & Francis). השאלה על ברוס (1767) פתוחה.
- Ambraseys 2009 ו-Ambraseys, Melville & Adams 1994 ב-Google Books: לספר של 2009 אין תצוגה מקדימה, ו-Google חסם את החיפוש ב-CAPTCHA.
- יערי, *אגרות ארץ ישראל* (1943): לא נמצא בגישה פתוחה.
- הנספח של עמירן 1952 (עמ׳ 65) ו-Russell 1980 כוללים עוד חומר שלא נוצל (למשל ערך 1759 אצל קלנר-עמירן, עמ׳ 230).

## המשימה המקורית, לפי סדר עדיפות (ראו את הסטטוס למעלה)
1. **JSTOR** (דרך Chrome, בחשבון של נדב):
   - Russell, "The Earthquake of May 19, A.D. 363", *BASOR* 238 (1980), pp. 47–64 → `0363-galilee.md`
   - Russell, "The Earthquake Chronology of Palestine and Northwest Arabia...", *BASOR* 260 (1985), pp. 37–59 → `0130-judea.md`, `0363`, `0749`
   - Ben-Horin, "An official report on the earthquake of 1837", *IEJ* 2 (1952), pp. 63–65 → `1837-safed.md` (`[^katz-refs]`; מאיפה המספר 4,083)
   - Kallner-Amiran, "A Revised Earthquake-Catalogue of Palestine", *IEJ* 1 (1950/51), pp. 223–246 → `1033`, `1927` (השנה המדויקת; טבלת היישובים)
   - צפריר ופרסטר, "לשאלת התאריך של 'רעש שביעית'", *תרביץ* נח (תשמ"ט), עמ׳ 357–362 → `0749-shviit.md`
   - קרץ' ואלעד, "על תיארוך 'רעש השביעית' ומשמעותו", *תרביץ* סא (תשנ"ב), עמ׳ 67–82 → `0749`
   - מרגליות, "לקביעת זמנו של רעש שביעית", *ידיעות החברה העברית לחקירת א"י* ח (תש"א) → `0749`
   - Tsafrir & Foerster, *BSOAS* 55 (1992), pp. 231–235 → `0749`
   - Lewis, "Baalbek before and after the earthquake of 1759: the drawings of James Bruce", *Levant* 31 (1999) → `1759-galilee-lebanon.md`:
     **האם ברוס צייר רק ב-1767, אחרי הרעידה?** בדף כתוב "לפני ואחרי", ויש על כך הערה נסתרת.
2. **Google Books** (תצוגה חלקית): Ambraseys, *Earthquakes in the Mediterranean and Middle East* (2009):
   עמ׳ 642–643 (1834: השעה 13:00 או 04:00), עמ׳ 683–685 (1856: הרוגים בכרתים, רודוס, קהיר, אלכסנדריה).
   גם Ambraseys, Melville & Adams 1994 (1068: 200 ילדים, בניאס, מצרים).
3. **Springer**: התקציר של Aldersons & Ben-Avraham 2014, doi:10.1007/978-94-017-8872-4_3
   → `1927-dead-sea.md`. הטענה מוסתרת. לבדוק אם הם מציעים מוקד מועדף (31.92, 35.56).
4. **קתדרה** (files.ybz.org.il) ו-**HebrewBooks**: יערי, *אגרות ארץ ישראל* (עמ׳ 70–73 למכתב של 1033;
   עמ׳ 287 לאיגרת ר' יוסף סופר, 1759); החתם סופר, *תורת משה*, פרשת אמור (1837).

## איך לעבוד (חובה)
- **קרא את המקור עצמו.** תקן את הדף לפי מה שכתוב בו, גם אם זה סותר את מה שכתוב עכשיו.
  ציטוט נכנס רק מילה במילה מהמקור. הטקסט העברי בדף הוא ניסוח מקורי ולא תרגום.
- **הסר את ה-TODO** מההערה ומהתווית רק אחרי שבדקת בפועל. הוסף מספר עמוד.
  אם המקור סותר את הדף: תקן את הדף, והוסף שורה ל-`review_notes` בראש הקובץ
  (בפורמט `- 'סבב JSTOR (אוקטובר 2026): ...'`).
- **אל תשמור בריפו טקסט מוגן בזכויות יוצרים.** מותרים רק ציטוטים קצרים בהערות.
  PDF-ים ותמלילים מלאים נשארים מחוץ לריפו.
- **אם שינית משפט** ש-`data/damage/places.json` מצטט (`page_sentence`), עדכן גם שם.
- **אחרי כל שינוי:**
  ```
  python3 scripts/build_events.py && python3 scripts/build_site.py && python3 scripts/check_site.py
  ```
  התוצאה חייבת להיות 0 כשלים. אחרי שינויי עיצוב: `scripts/check_a11y.mjs` (הוראות בראש הקובץ).
- **גרסה:** ענף חדש, commit, PR ומיזוג. נדב אישר מיזוג בלי לחכות לו.
- **בסוף, לנדב (בעברית):** מה אומת, מה תוקן, ומה עדיין פתוח.

## הרשימה המלאה של "TODO: לבדוק במקור" (נוצרה אוטומטית מתוך content/events)
- `0031bce-judea.md` · ביבליוגרפיה: Jefferson B. Williams, Markus J. Schwab and Achim Brauer, "An early first-century earthquake in the Dead Sea", International Geology Review 54 (10) (2012), pp. 1219–1228 (TODO: לבדוק במקור)
- `0031bce-judea.md` · הערה [^williams]: Jefferson B. Williams, Markus J. Schwab and Achim Brauer, "An early first-century earthquake in the Dead Sea", *International Geology Review* 54 (2012), pp. 1219–1228. TODO: לבדוק במקור.
- `0130-judea.md` · ביבליוגרפיה: Caesarea Maritima: A Retrospective after Two Millennia, p. 23 (TODO: לבדוק במקור)
- `0130-judea.md` · הערה [^caesarea]: *Caesarea Maritima: A Retrospective after Two Millennia*, עמ׳ 23 (שם מוזכרת לוד). TODO: לבדוק במקור.
- `0363-galilee.md` · ביבליוגרפיה: E. Y. Meimaris and K. I. Kritikakou, Inscriptions from Palaestina Tertia, vol. Ia: The Greek Inscriptions from Ghor es-Safi (Byzantine Zoora), Athens, 2005 (TODO: לבדוק במקור)
- `0363-galilee.md` · ביבליוגרפיה: Michael Eisenberg, דוח על הבזיליקה בסוסיתא (2021), עמ׳ 171–173, כפי שמובא אצל Williams, deadseaquake.info (TODO: לבדוק במקור ולהשלים פרטים ביבליוגרפיים)
- `0363-galilee.md` · הערה [^meimaris]: E. Y. Meimaris and K. I. Kritikakou, *Inscriptions from Palaestina Tertia*, vol. Ia, Athens, 2005, כפי שמובא אצל Zohar, Salamon and Rubin 2016 ואצל Williams, deadseaquake.info. TODO: לבדוק במקור.
- `0363-galilee.md` · הערה [^eisenberg]: Michael Eisenberg (2021), עמ׳ 171–173, מצוטט אצל Williams, "363 CE Cyril Quakes", deadseaquake.info, בפרק "Hippos Sussita" (הדף נקרא באוקטובר 2026). בציטוט שם: "The latest of the trapped coins date to 361/2 CE"; "it seems that the basilica 
- `0363-galilee.md` · הערה [^dsqsepphoris]: Williams, "363 CE Cyril Quakes", deadseaquake.info, בפרק "Sepphoris": E. M. Meyers et al. 1992 מייחסים לרעידה חלק מההרס; J. F. Strange et al. 2006 מייחסים חלק גדול ממנו למרד גאלוס. TODO: לבדוק במקור.
- `0363-galilee.md` · הערה [^dsqnab]: Williams, "363 CE Cyril Quakes", deadseaquake.info, בפרק "en-Nabratein", על פי Meyers et al. 1982, Magness 2010 ו-Meyers and Meyers 2010. TODO: לבדוק במקור.
- `0749-shviit.md` · ביבליוגרפיה: S. Marco, M. Hartal, N. Hazan, L. Lev, M. Stein, "Archaeology, history, and geology of the A.D. 749 earthquake, Dead Sea transform", Geology 31 (2003), עמ׳ 665–668 (הפרטים הביבליוגרפיים אומתו ברשימת הפרסומים של מרקו באתר אוניברסיטת תל אביב,
- `0749-shviit.md` · ביבליוגרפיה: שולמית אליצור, פיוטי ר׳ פינחס הכהן, ירושלים תשס"ד (TODO: לבדוק במקור)
- `0749-shviit.md` · ביבליוגרפיה: G. Avni, The Byzantine-Islamic Transition in Palestine: An Archaeological Approach, Oxford 2014 (TODO: לבדוק במקור)
- `0749-shviit.md` · הערה [^marco]: S. Marco, M. Hartal, N. Hazan, L. Lev, M. Stein, "Archaeology, history, and geology of the A.D. 749 earthquake, Dead Sea transform", [Geology 31 (2003)](https://doi.org/10.1130/G19516.1), עמ׳ 665–668. הקרע בטבריה אומת דרך סלמון ואחרים (2007
- `0749-shviit.md` · הערה [^elitzur]: שולמית אליצור, פיוטי ר' פינחס הכהן, ירושלים תשס"ד. TODO: לבדוק במקור.
- `0749-shviit.md` · הערה [^avni]: G. Avni, The Byzantine-Islamic Transition in Palestine: An Archaeological Approach, Oxford 2014, עמ׳ 325. TODO: לבדוק במקור.
- `0760bce-uzziah.md` · ביבליוגרפיה: N. N. Ambraseys, "Historical earthquakes in Jerusalem: a methodological discussion", Journal of Seismology 9 (2005), pp. 329–340 (TODO: לבדוק במקור)
- `0760bce-uzziah.md` · ביבליוגרפיה: Steven A. Austin, Gordon W. Franz and Eric G. Frost, "Amos's Earthquake: An Extraordinary Middle East Seismic Event of 750 B.C.", International Geology Review 42 (2000), pp. 657–671 (TODO: לבדוק במקור)
- `0760bce-uzziah.md` · ביבליוגרפיה: A. Ben-Menahem, "Four thousand years of seismicity along the Dead Sea Rift", Journal of Geophysical Research 96 (B12) (1991), pp. 20195–20216 (TODO: לבדוק במקור)
- `0760bce-uzziah.md` · הערה [^ambraseys2005]: N. N. Ambraseys, "Historical earthquakes in Jerusalem: a methodological discussion", *Journal of Seismology* 9 (2005), pp. 329–340, כפי שמצוטט אצל Salamon et al. 2007. TODO: לבדוק במקור, כולל העמוד.
- `0760bce-uzziah.md` · הערה [^austin]: Steven A. Austin, Gordon W. Franz and Eric G. Frost, "Amos's Earthquake: An Extraordinary Middle East Seismic Event of 750 B.C.", *International Geology Review* 42 (2000), pp. 657–671. TODO: לבדוק במקור, כולל רשימת האתרים.
- `0760bce-uzziah.md` · הערה [^benmenahem]: A. Ben-Menahem, "Four thousand years of seismicity along the Dead Sea Rift", *Journal of Geophysical Research* 96 (B12) (1991), pp. 20195–20216. התאריך והגודל לפי Salamon et al. 2007; ההצעה על מוקד בחצור לפי Austin et al. 2000. TODO: לבדוק 
- `0760bce-uzziah.md` · הערה [^zilberman]: E. Zilberman, R. Amit, I. Bruner and Y. Nachmias, *Neotectonic and paleoseismic study: Bet Shean Valley*, Geological Survey of Israel, Jerusalem, 2004, כפי שמובא אצל Salamon et al. 2007. TODO: לבדוק במקור.
- `0881-acre.md` · ביבליוגרפיה: A. Salamon, T. Rockwell, E. Guidoboni, A. Comastri, "A critical evaluation of tsunami records reported for the Levant coast from the second millennium BCE to the present", Israel Journal of Earth Sciences 58 (2011), עמ׳ 327–354 (TODO: לבדוק
- `1033-jordan-valley.md` · ביבליוגרפיה: אברהם יערי, אגרות ארץ ישראל, תל אביב 1943, עמ׳ 70–73 (מכתבו של שלמה בן צמח. TODO: לבדוק במקור)
- `1033-jordan-valley.md` · ביבליוגרפיה: I. Grigoratos, V. Poggi, L. Danciu, G. Rojo, "An updated parametric catalog of historical earthquakes around the Dead Sea Transform Fault Zone", Journal of Seismology 24 (2020), עמ׳ 803–832 (TODO: לבדוק במקור)
- `1033-jordan-valley.md` · ביבליוגרפיה: M. Ferry ואחרים, "A 48-kyr-long slip rate history for the Jordan Valley segment of the Dead Sea Fault", Earth and Planetary Science Letters 260 (2007), עמ׳ 394–406 (TODO: לבדוק במקור)
- `1033-jordan-valley.md` · ביבליוגרפיה: M. Ma׳oz, S. Nusseibeh (עורכים), Jerusalem: Points of Friction and Beyond, Kluwer 2000, עמ׳ 136–138 (TODO: לבדוק במקור)
- `1033-jordan-valley.md` · הערה [^nusseibeh]: M. Ma'oz, S. Nusseibeh (עורכים), Jerusalem: Points of Friction and Beyond, Kluwer 2000, עמ׳ 136–138. TODO: לבדוק במקור.
- `1033-jordan-valley.md` · הערה [^ferry]: M. Ferry ואחרים, "A 48-kyr-long slip rate history for the Jordan Valley segment of the Dead Sea Fault", [Earth and Planetary Science Letters 260 (2007)](https://doi.org/10.1016/j.epsl.2007.05.049), עמ׳ 394–406. TODO: לבדוק במקור.
- `1033-jordan-valley.md` · הערה [^grig]: I. Grigoratos, V. Poggi, L. Danciu, G. Rojo, ["An updated parametric catalog of historical earthquakes around the Dead Sea Transform Fault Zone"](https://link.springer.com/article/10.1007/s10950-020-09904-9), Journal of Seismology 24 (2020)
- `1068-near-east.md` · ביבליוגרפיה: N. N. Ambraseys, C. P. Melville, R. D. Adams, The Seismicity of Egypt, Arabia and the Red Sea: A Historical Review, Cambridge University Press 1994 (TODO: לבדוק במקור)
- `1068-near-east.md` · ביבליוגרפיה: E. Zilberman, R. Amit, N. Porat, Y. Enzel, U. Avner, "Surface ruptures induced by the devastating 1068 AD earthquake in the southern Arava valley, Dead Sea Rift, Israel", Tectonophysics 408 (2005), עמ׳ 79–99 (TODO: לבדוק במקור)
- `1068-near-east.md` · הערה [^ama]: N. N. Ambraseys, C. P. Melville, R. D. Adams, [The Seismicity of Egypt, Arabia and the Red Sea: A Historical Review](https://books.google.com/books?id=fxnnk2inWT0C&pg=PA31), Cambridge University Press 1994. TODO: לבדוק במקור.
- `1068-near-east.md` · הערה [^zil]: E. Zilberman, R. Amit, N. Porat, Y. Enzel, U. Avner, "Surface ruptures induced by the devastating 1068 AD earthquake in the southern Arava valley, Dead Sea Rift, Israel", [Tectonophysics 408 (2005)](https://doi.org/10.1016/j.tecto.2005.05.0
- `1759-galilee-lebanon.md` · ביבליוגרפיה: T. Nemer, M. Meghraoui, K. Khair, "The Rachaya-Serghaya fault system (Lebanon): evidence of coseismic ruptures, and the AD 1759 earthquake sequence", Journal of Geophysical Research 113 (2008), B05312 (נקראו התקציר ועמ׳ 1–3 מתוך 12. TODO: ל
- `1759-galilee-lebanon.md` · ביבליוגרפיה: N. N. Lewis, "Baalbek before and after the earthquake of 1759: the drawings of James Bruce", Levant 31 (1999), עמ׳ 241 ואילך (TODO: לבדוק במקור)
- `1759-galilee-lebanon.md` · ביבליוגרפיה: אברהם יערי, אגרות ארץ ישראל, עמ׳ 287, איגרת ר׳ יוסף סופר מצפת (TODO: לבדוק במקור)
- `1759-galilee-lebanon.md` · הערה [^yaari]: אברהם יערי, *אגרות ארץ ישראל*, עמ׳ 287, איגרת ר׳ יוסף סופר מצפת. TODO: לבדוק במקור.
- `1759-galilee-lebanon.md` · הערה [^lewis]: N. N. Lewis, *Levant* 31 (1999), עמ׳ 242. TODO: לבדוק במקור.
- `1834-jerusalem.md` · ביבליוגרפיה: N. N. Ambraseys, Earthquakes in the Mediterranean and Middle East: A Multidisciplinary Study of Seismicity up to 1900, Cambridge University Press, 2009, עמ׳ 642–643 (TODO: לבדוק במקור)
- `1834-jerusalem.md` · ביבליוגרפיה: C. Migowski, A. Agnon, R. Bookman, J. F. W. Negendank, M. Stein, "Recurrence pattern of Holocene earthquakes along the Dead Sea transform revealed by varve-counting and radiocarbon dating of lacustrine sediments", Earth and Planetary Scienc
- `1837-safed.md` · ביבליוגרפיה: T. Nemer and M. Meghraoui, "Evidence of coseismic ruptures along the Roum fault (Lebanon): a possible source for the AD 1837 earthquake", Journal of Structural Geology 28(8) (2006), pp. 1483–1495 (TODO: לבדוק במקור)
- `1837-safed.md` · ביבליוגרפיה: M. Vered and H. L. Striem, "A macroseismic study and the implications of structural damage of two recent major earthquakes in the Jordan Rift", Bulletin of the Seismological Society of America 67(6) (1977), pp. 1607–1613 (TODO: לבדוק במקור)
- `1837-safed.md` · ביבליוגרפיה: מיכאל איש-שלום, מסעי נוצרים לארץ ישראל, 1965 (TODO: לבדוק במקור)
- `1837-safed.md` · ביבליוגרפיה: יצחק ריבקינד, "הרוגי צפת ברעש תקצ"ז", ספר השנה של ארץ-ישראל ב–ג (תרפ"ד–תרפ"ה), עמ׳ 100–109 (TODO: לבדוק במקור)
- `1837-safed.md` · הערה [^wachs]: D. Wachs and D. Levitte, "Earthquake-induced landslides in the Galilee", *Israel Journal of Earth Sciences* 30 (1981), pp. 39–43, כפי שמובא אצל Ambraseys 1997 (לעיל), עמ׳ 924 ורשימת המקורות, עמ׳ 932. אמברייזיס נשען עליו כשהוא מייחס את חורבן
- `1837-safed.md` · הערה [^vered]: M. Vered and H. L. Striem, *BSSA* 67(6) (1977), עמ׳ 1607 ו-1612: ML 6.25 עד 6.5, לפי השוואה לנתוני הנזק ברעידת 1927, ומוקד מעט צפונית לצפת. TODO: לבדוק במקור.  המוקד אומת דרך אמברייזיס 1997, עמ׳ 923, שמסכם את המחקרים הקודמים: "Modern writer
- `1837-safed.md` · הערה [^ishshalom2]: ויזינו, בתרגום אצל מיכאל איש-שלום, *מסעי נוצרים לארץ ישראל*, 1965, עמ׳ 477–478. פרפרזה; הנוסח המדויק לא נבדק. TODO: לבדוק במקור. אליאב 1996, עמ׳ 73, הערה 17, מונה את ויזינו (J. N. Visino, *Meine Wanderung nach Palästina*, Passau 1840, pp. 2
- `1837-safed.md` · הערה [^benayahu]: מאיר בניהו, *רבי חיים יוסף דוד אזולאי*, ירושלים תשי"ט. TODO: לבדוק במקור.
- `1837-safed.md` · הערה [^rivkind]: יצחק ריבקינד, "הרוגי צפת ברעש תקצ"ז", *ספר השנה של ארץ-ישראל* ב–ג (תרפ"ד–תרפ"ה), עמ׳ 100–109. TODO: לבדוק במקור. אליאב 1996 מפנה למאמר ("עמ׳ 103 ואילך", עמ׳ 62, הערה 32), ולפיו ריבקינד הסתמך על תיאורו של תומסון, אמד את הרוגי היהודים בצפת בכ
- `1856-crete.md` · ביבליוגרפיה: N. N. Ambraseys, Earthquakes in the Mediterranean and Middle East: A Multidisciplinary Study of Seismicity up to 1900, Cambridge University Press, 2009, עמ׳ 683–685 (TODO: לבדוק במקור)
- `1856-crete.md` · ביבליוגרפיה: B. C. Papazachos, P. E. Comninakis, G. F. Karakaisis ועמיתיו, A catalogue of earthquakes in Greece and surrounding area for the period 550BC–1999, University of Thessaloniki, 2000 (TODO: לבדוק במקור)
- `1856-crete.md` · ביבליוגרפיה: N. N. Ambraseys, C. P. Melville, R. D. Adams, The Seismicity of Egypt, Arabia and the Red Sea: A Historical Review, Cambridge University Press, 1994, עמ׳ 69–70 (TODO: לבדוק במקור)
- `1927-dead-sea.md` · ביבליוגרפיה: רון אבני, רעידת האדמה של שנת 1927: מחקר מאקרוסייסמי על בסיס מקורות התקופה, עבודת דוקטור, אוניברסיטת בן-גוריון, 1999. בשם האנגלי, לפי זוהר ומרקו 2012: The 1927 Jericho Earthquake. Comprehensive Macroseismic Analysis Based on Contemporary Sou
- `1927-dead-sea.md` · ביבליוגרפיה: A. Shapira, R. Avni, A. Nur, "A new estimate for the epicenter of the Jericho earthquake of 11 July 1927", Israel Journal of Earth Sciences 42 (1993), pp. 93–96 (TODO: לבדוק במקור)
- `1927-dead-sea.md` · ביבליוגרפיה: R. Avni, D. Bowman, A. Shapira, A. Nur, "Erroneous interpretation of historical documents related to the epicenter of the 1927 Jericho earthquake in the Holy Land", Journal of Seismology 6(4) (2002), pp. 469–476 (הפרטים אומתו ברשימת המקורות
- `1927-dead-sea.md` · ביבליוגרפיה: M. Vered and H. L. Striem, "A macroseismic study and the implications of structural damage of two recent major earthquakes in the Jordan Rift", Bulletin of the Seismological Society of America 67(6) (1977), pp. 1607–1613 (TODO: לבדוק במקור.
- `1927-dead-sea.md` · ביבליוגרפיה: רון אבני, דן באומן, אבי שפירא ועמוס נור, "מיקום רעידת האדמה של ה-11 יולי 1927 בארץ ישראל – אנטומיה של טעות", אופקים בגאוגרפיה 53 (2001), עמ׳ 85–94 (TODO: לבדוק במקור)
- `1927-dead-sea.md` · הערה [^avni-18]: רון אבני, 1999, עמ׳ 18 וטבלה 2. TODO: לבדוק במקור.
- `1927-dead-sea.md` · הערה [^vered]: M. Vered and H. L. Striem, *BSSA* 67(6) (1977), pp. 1607–1613. המאמר עצמו לא נקרא (TODO: לבדוק במקור); ההצעה שלהם מובאת אצל זוהר ומרקו 2012, עמ׳ 20.
- `1927-dead-sea.md` · הערה [^shapira]: A. Shapira, R. Avni and A. Nur, *Israel Journal of Earth Sciences* 42 (1993), עמ׳ 93–96; רון אבני, 1999, עמ׳ 20–22. המוקד בצפון ים המלח מאושר גם אצל Zohar, Rubin and Salamon 2014, עמ׳ 912. המאמר מ-1993 עצמו לא נקרא (TODO: לבדוק במקור).
- `1927-dead-sea.md` · הערה [^avni02]: R. Avni, D. Bowman, A. Shapira and A. Nur, "Erroneous interpretation of historical documents related to the epicenter of the 1927 Jericho earthquake in the Holy Land", *Journal of Seismology* 6 (2002), עמ׳ 469–476. המאמר עצמו לא נקרא (TODO:
