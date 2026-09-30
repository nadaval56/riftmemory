/* אנימציית הסמל: הפעלה חוזרת.
   האנימציה עצמה ב-site.css ("הסמל") ומתנגנת פעם אחת בטעינה, בלי JS בכלל.
   הקובץ הזה רק מנגן אותה שוב:
     - כשהסמל חוזר למסך אחרי שיצא ממנו לגמרי (גלילה למטה ובחזרה);
     - 15 שניות אחרי הפעם הקודמת, כל עוד הוא על המסך.
   השעון מתאפס בכל ניגון, כך שאחרי ניגון בגלילה לא יבוא מיד ניגון מתוזמן.
   לא מתנגן כשהלשונית ברקע, כשהקורא ביקש פחות תנועה, או כשבחר "עצירת אנימציות".

   הפעלה מחדש של אנימציית CSS: animation: none על כל החלקים, קריאת פריסה אחת
   כדי שהדפדפן יחיל את זה, ואז ניקוי. האנימציה מתחילה מאפס, כולל ההשהיות.

   אותה לוגיקה כמו assets/js/brand-anim.js באתר העב"מים (nadaval56/UFO). */
(function () {
  var marks = document.querySelectorAll('.rift-mark');
  if (!marks.length || !('IntersectionObserver' in window)) return;

  var EVERY_MS = 15000;
  var reduce = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
  var state = new Map();

  function still() {
    return (reduce && reduce.matches) || document.documentElement.classList.contains('a11y-still');
  }

  function replay(svg) {
    state.get(svg).last = performance.now();
    if (still()) return;
    var parts = svg.querySelectorAll('*');
    parts.forEach(function (el) { el.style.animation = 'none'; });
    void svg.getBoundingClientRect().width;
    parts.forEach(function (el) { el.style.animation = ''; });
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      var s = state.get(e.target);
      if (e.isIntersecting) {
        if (s.left) { replay(e.target); s.left = false; }
        s.visible = true;
      } else {
        s.visible = false;
        s.left = true;
      }
    });
  });

  marks.forEach(function (svg) {
    state.set(svg, { visible: false, left: false, last: performance.now() });
    io.observe(svg);
  });

  setInterval(function () {
    if (document.hidden) return;
    var now = performance.now();
    state.forEach(function (s, svg) {
      if (s.visible && now - s.last >= EVERY_MS) replay(svg);
    });
  }, 1000);

  document.addEventListener('visibilitychange', function () {
    if (document.hidden) return;
    var now = performance.now();
    state.forEach(function (s) { s.last = Math.max(s.last, now - EVERY_MS + 3000); });
  });
})();
