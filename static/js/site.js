// זמן יחסי ("לפני 3 שעות") לפי השעון של הקורא, ומפות Leaflet.
(function () {
  function ago(iso) {
    var t = Date.parse(iso);
    if (isNaN(t)) return null;
    var m = Math.floor((Date.now() - t) / 60000);
    if (m < 60) return "לפני פחות משעה";
    var h = Math.floor(m / 60);
    if (h === 1) return "לפני שעה";
    if (h === 2) return "לפני שעתיים";
    if (h < 24) return "לפני " + h + " שעות";
    var d = Math.floor(h / 24);
    if (d === 1) return "אתמול";
    if (d === 2) return "לפני יומיים";
    return "לפני " + d + " ימים";
  }

  document.querySelectorAll("time[data-relative]").forEach(function (el) {
    var text = ago(el.getAttribute("datetime"));
    if (text) {
      el.textContent = text;
      el.title = new Date(el.getAttribute("datetime")).toLocaleString("he-IL", { timeZone: "Asia/Jerusalem" });
    }
  });

  var mapFocus = [];
  document.addEventListener("click", function (ev) {
    var a = ev.target.closest && ev.target.closest("[data-map-focus]");
    if (!a) return;
    ev.preventDefault();
    var key = a.getAttribute("data-map-focus");
    mapFocus.some(function (f) { return f(key); });
  });

  function initMap(el) {
    var data = JSON.parse(el.dataset.map);
    var map = L.map(el, { scrollWheelZoom: false, minZoom: 5, maxZoom: 10 }).setView([31.8, 35.2], 7);
    // אזורי לחיצה: מתחת לכל נקודה וקו יש צורה שקופה וגדולה יותר עם אותו חלון, כך שלחיצה
    // קרובה מספיקה. באצבע (מסך מגע) האזור גדול יותר, כי אי אפשר לכוון בדיוק של עכבר.
    var coarse = window.matchMedia && window.matchMedia("(pointer: coarse)").matches;
    var HIT = coarse ? 16 : 9;
    function hitDot(latlng, popup, layer) {
      return L.circleMarker(latlng, { radius: HIT, stroke: false, fill: true, fillOpacity: 0 }).bindPopup(popup).addTo(layer);
    }
    var css = getComputedStyle(document.documentElement);

    // מפת בסיס מקומית (Natural Earth, נחלת הכלל): ים, אגמים, נהרות ושמות ערים.
    // בלי שרת אריחים חיצוני: CARTO דורש מפתח, ו-OSM מסמן שטחים צבאיים בוורוד.
    map.createPane("base").style.zIndex = 200;
    map.createPane("cities").style.zIndex = 250;
    // סדר השכבות, מלמטה למעלה: קווי השבר, המקומות שנפגעו, הרעידות (היסטוריות ואחרונות).
    // כך לחיצה ליד מקום שנפגע פותחת אותו ולא את הקו שעובר לידו, והרעידות לא נבלעות במקומות.
    map.createPane("faults").style.zIndex = 380;
    map.createPane("damage").style.zIndex = 390;
    map.attributionControl.setPrefix(false);
    map.attributionControl.addAttribution('<a href="https://leafletjs.com">Leaflet</a> · <a href="https://www.naturalearthdata.com">Natural Earth</a>');
    fetch(data.basemap).then(function (r) { return r.json(); }).then(function (b) {
      var water = css.getPropertyValue("--map-water").trim();
      var poly = function (rings) { return rings.map(function (r) { return r.map(function (c) { return [c[1], c[0]]; }); }); };
      b.sea.concat(b.lakes).forEach(function (p) {
        L.polygon(poly(p), { pane: "base", stroke: false, fillColor: water, fillOpacity: 1, interactive: false }).addTo(map);
      });
      b.rivers.forEach(function (l) {
        L.polyline(l.map(function (c) { return [c[1], c[0]]; }), { pane: "base", color: water, weight: 1.5, interactive: false }).addTo(map);
      });
      var cities = b.cities.map(function (c) {
        return L.tooltip({ permanent: true, direction: "center", className: "city-label", pane: "cities", interactive: false })
          .setLatLng([c.lat, c.lon]).setContent(c.name);
      });
      var showCities = function () {
        var z = map.getZoom();
        b.cities.forEach(function (c, i) {
          var on = z >= 6 + c.rank;
          if (on && !map.hasLayer(cities[i])) cities[i].addTo(map);
          if (!on && map.hasLayer(cities[i])) map.removeLayer(cities[i]);
        });
      };
      map.on("zoomend", showCities);
      showCities();
    }).catch(function () {});
    var colors = {
      texts: css.getPropertyValue("--texts").trim(),
      archaeology: css.getPropertyValue("--archaeology").trim(),
      instrumental: css.getPropertyValue("--instrumental").trim(),
      live: css.getPropertyValue("--map-live").trim(),
      rust: css.getPropertyValue("--accent").trim()
    };
    var bounds = [];
    // קישורי "הצגה במפה" ברשימות: מפתח -> סמן
    var focusable = {};
    mapFocus.push(function (key) {
      var m = focusable[key];
      if (!m) return false;
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      map.setView(m.getLatLng(), Math.max(map.getZoom(), 9));
      m.openPopup();
      return true;
    });
    var faultBounds = [];
    var segBounds = [];

    function esc(t) {
      return String(t == null ? "" : t).replace(/[&<>"]/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
      });
    }

    // קווי ההעתקים (GEM / EMME), מקובצים לפי מקטע.
    // לחיצה על קו מסבירה מה הוא. שם המקטע כתוב פעם אחת, על הקו, באמצע הטווח הצפון-דרומי של המקטע.
    data.segments.forEach(function (s) {
      var lines = [], lo = 90, hi = -90;
      // בדף רעידה: המקטע שלה מודגש, והשאר חיוורים
      var dim = data.highlight && data.highlight !== s.id;
      var strong = data.highlight === s.id;
      s.lines.forEach(function (line) {
        var latlngs = line.map(function (c) { return [c[1], c[0]]; });
        var fault = L.polyline(latlngs, {
          pane: "faults",
          color: colors.rust, weight: strong ? 5 : dim ? 2 : 3, opacity: dim ? 0.35 : 0.9,
          dashArray: s.draft ? "6 5" : null
        })
          .bindPopup('<div class="map-popup"><strong>קו שבר פעיל (העתק)</strong><br>מקטע: ' + esc(s.name) +
            (s.note ? '<div class="src">' + esc(s.note) + "</div>" : "") +
            (s.history && s.history.length ? '<div class="src">רעידות היסטוריות במקטע: ' + s.history.map(function (h) {
              return '<a href="' + h.url + '">' + esc(h.title) + "</a>";
            }).join(" · ") + "</div>" : "") +
            '<div class="src">מקור הקו: GEM Global Active Faults, מודל EMME</div></div>')
          .addTo(map);
        L.polyline(latlngs, { pane: "faults", opacity: 0, weight: HIT * 1.4 }).bindPopup(fault.getPopup().getContent()).addTo(map);
        latlngs.forEach(function (p) { faultBounds.push(p); if (strong) segBounds.push(p); });
        lines.push(latlngs);
        latlngs.forEach(function (p) { lo = Math.min(lo, p[0]); hi = Math.max(hi, p[0]); });
      });
      var target = (lo + hi) / 2, mid = null;
      lines.forEach(function (ll) {
        for (var i = 1; i < ll.length && !mid; i++) {
          var a = ll[i - 1], b = ll[i];
          if ((a[0] - target) * (b[0] - target) <= 0 && a[0] !== b[0]) {
            var t = (target - a[0]) / (b[0] - a[0]);
            mid = [target, a[1] + t * (b[1] - a[1])];
          }
        }
      });
      if (mid) {
        L.tooltip({ permanent: true, direction: "right", offset: [8, 0], className: "seg-label" + (dim ? " dim" : "") })
          .setLatLng(mid).setContent(esc(s.name)).addTo(map);
      }
    });

    // שכבות נפרדות, כדי שאפשר יהיה להציג ולהסתיר כל אחת מתחת למפה
    var layers = { live: L.layerGroup().addTo(map), hist: L.layerGroup().addTo(map), dmg: L.layerGroup().addTo(map) };
    var surface = css.getPropertyValue("--surface").trim();

    // רעידות אחרונות (מדידה): נקודה כחולה מלאה עם מסגרת בהירה. הצבע והצורה שונים מהרעידות ההיסטוריות
    // (עיגול מקווקו בצבע השבר), והחלון שנפתח מתחיל בתווית "רעידה אחרונה".
    var newest = null;
    data.live.forEach(function (q) {
      var hit = data.dot_scale ? null : hitDot([q.lat, q.lon], "", layers.live);
      var m = L.circleMarker([q.lat, q.lon], {
        radius: data.dot_scale ? Math.max(2, (q.mag - 2) * data.dot_scale) : Math.max(4, q.mag * 1.8),
        color: data.dot_scale ? colors.live : surface, weight: data.dot_scale ? 0.5 : 1.5,
        fillColor: colors.live, fillOpacity: data.dot_scale ? 0.35 : 0.85
      }).bindPopup('<div class="map-popup"><span class="pop-kind pop-live">' + esc(data.live_kind || "רעידה אחרונה · נמדדה במכשירים") + "</span>" +
        "<strong>" + esc(q.label) + '</strong><br><bdi dir="ltr">M' + q.mag + "</bdi>" +
        (q.depth != null ? " · עומק " + q.depth + " ק״מ" : "") +
        '<div class="src">' + esc(q.local || ago(q.time_utc) || "") + "</div>" +
        (q.url ? '<div class="src"><a href="' + q.url + '"' + (q.url.indexOf("http") === 0 ? ' rel="noopener"' : "") + ">" +
          (q.url.indexOf("http") === 0 ? "הרשומה בקטלוג USGS ↗" : "לכל הפרטים ←") + "</a></div>" : "") + "</div>")
        .addTo(layers.live);
      if (hit) hit.setPopupContent(m.getPopup().getContent());
      if (q.key) focusable[q.key] = m;
      bounds.push([q.lat, q.lon]);
      if (!data.dot_scale && q.time_utc && (!newest || q.time_utc > newest.time_utc)) newest = q;
    });
    // הרעידה האחרונה ביותר: טבעת שמתרחבת פעמיים ונעצרת (בלי תנועה אם הקורא ביקש פחות תנועה)
    if (newest) {
      L.marker([newest.lat, newest.lon], {
        icon: L.divIcon({ className: "live-ring", iconSize: [34, 34] }), interactive: false, keyboard: false
      }).addTo(layers.live);
    }

    // מקומות שנפגעו: המקומות שהדפים מתארים בהם נזק (לא מוקדים). ריבוע קטן, ובלחיצה: מה קרה שם ובאיזו רעידה.
    var dmgBounds = [];
    var dmgLayer = layers.dmg;
    if (data.damage && data.damage.length) {
      map.attributionControl.addAttribution('<a href="https://www.geonames.org">GeoNames</a>');
    }
    (data.damage || []).forEach(function (d) {
      // הריבוע שרואים קטן, אבל אזור הלחיצה סביבו גדול (ב-CSS: .dmg::before הוא הריבוע)
      var icon = L.divIcon({ className: "dmg" + (d.doubtful ? " doubtful" : ""), iconSize: coarse ? [30, 30] : [18, 18] });
      var html = '<div class="map-popup"><strong>' + esc(d.name) + "</strong>" + d.entries.map(function (x) {
        return '<div class="dmg-entry"><a href="' + x.url + '">' + esc(x.title) + "</a>" +
          (x.place !== d.name ? " (" + esc(x.place) + ")" : "") + ": " + esc(x.what) +
          '<div class="src">' + esc(x.status) + "</div></div>";
      }).join("") + "</div>";
      L.marker([d.lat, d.lon], { icon: icon, keyboard: false, pane: "damage" }).bindPopup(html).addTo(dmgLayer);
      dmgBounds.push([d.lat, d.lon]);
    });

    // רעידות היסטוריות: המיקום משוער בלבד. עיגול גדול ושקוף מראה שאין כאן נקודה מדויקת,
    // והחלון שנפתח בלחיצה אומר לפי איזה חוקר נקבע המיקום ומפנה לביבליוגרפיה בדף הרעידה.
    var hist = [];
    data.events.forEach(function (e) {
      var popup = '<div class="map-popup"><span class="pop-kind pop-hist">רעידה היסטורית</span><a href="' + e.url + '"><strong>' + esc(e.title) + "</strong></a><br>" + esc(e.year) +
        "<br><strong>" + (e.label ? "הצעה אחת למוקד (מיקום משוער)" : "מיקום משוער") + "</strong>" +
        (e.source ? '<div class="src">לפי: ' + (e.source_url
          ? '<a href="' + esc(e.source_url) + '" rel="noopener">' + esc(e.source) + "</a>"
          : esc(e.source)) + "</div>" : "") +
        '<div class="src"><a href="' + e.url + '#bibliography">לביבליוגרפיה המלאה</a></div></div>';
      var area = L.circle([e.lat, e.lon], {
        radius: e.label ? 12000 : 30000, color: colors.rust, weight: 1.5, dashArray: "4 4",
        fillColor: colors.rust, fillOpacity: 0.15
      }).bindPopup(popup).addTo(layers.hist);
      hitDot([e.lat, e.lon], popup, layers.hist);
      L.circleMarker([e.lat, e.lon], {
        radius: 5.5, color: surface, weight: 2, fillColor: colors.rust, fillOpacity: 1
      }).bindPopup(popup).addTo(layers.hist);
      area.bindTooltip(e.label ? "הצעה: " + esc(e.label) : "מיקום משוער · " + esc(e.year),
        { permanent: e.perm !== false, direction: "right", offset: [12, 0], className: "approx-label" });
      hist.push([e.lat, e.lon]);
    });

    // המתגים שמתחת למפה (בתבנית: _macros.html): כל אחד מציג או מסתיר שכבה אחת
    var legend = document.querySelector('.map-legend[data-for="' + el.id + '"]');
    if (legend) {
      legend.querySelectorAll("input[data-layer]").forEach(function (box) {
        var layer = layers[box.getAttribute("data-layer")];
        var sync = function () {
          if (box.checked) map.addLayer(layer); else map.removeLayer(layer);
        };
        box.addEventListener("change", sync);
        sync(); // דפדפן שמשחזר מצב טופס (חזרה אחורה) עלול להשאיר תיבה לא מסומנת
      });
    }

    // תמיד רואים את כל קו השבר בארץ, ובנוסף את הרעידות הקרובות שעל המפה.
    // רעידות רחוקות (כרתים, סוריה) נשארות על המפה אבל לא מרחיקות את המבט מהארץ,
    // חוץ מבדף של הרעידה עצמה (focus).
    var inRegion = function (p) { return p[0] > 29 && p[0] < 33.6 && p[1] > 34 && p[1] < 36.6; };
    var near = bounds.concat(data.focus ? [] : hist).filter(inRegion);
    var all = faultBounds.filter(function (p) { return p[0] < 33.4; }).concat(near, data.focus ? hist : []);
    // דף רעידה עם מיקום משוער: המבט על המיקום (או ההצעות) ועל המקומות שנפגעו
    if (data.focus && hist.length) {
      map.fitBounds(L.latLngBounds(hist.concat(dmgBounds)).pad(0.25), { maxZoom: 9 });
      return;
    }
    // מפה של מקטע בלבד (בלי מיקום לרעידה): המבט על המקטע והמקומות שנפגעו, עם מעט סביבה
    if (data.focus && !hist.length && (segBounds.length || dmgBounds.length)) {
      all = segBounds.concat(near, dmgBounds);
      map.fitBounds(L.latLngBounds(all).pad(0.6), { maxZoom: 9 });
      return;
    }
    if (all.length > 1) map.fitBounds(all, { padding: [24, 24], maxZoom: 9 });
    else if (all.length === 1) map.setView(all[0], 8);
  }

  // הפס הנע: כפתור עצירה והפעלה (WCAG 2.2.2: תוכן שזז יותר מ-5 שניות צריך דרך לעצור אותו)
  var ticker = document.querySelector(".live-ticker");
  if (ticker) {
    var pause = ticker.querySelector(".lt-pause");
    pause.addEventListener("click", function () {
      var paused = ticker.classList.toggle("paused");
      pause.setAttribute("aria-pressed", paused ? "true" : "false");
      pause.setAttribute("aria-label", paused ? "הפעלת הפס הנע" : "עצירת הפס הנע");
      pause.firstElementChild.textContent = paused ? "▶" : "❚❚";
    });
  }

  // הלשונית של הדף הנוכחי מסומנת כבר בבנייה (aria-current). גיבוי לכתובות שונות של אותו דף,
  // למשל /riftmemory בלי לוכסן או /riftmemory/index.html: מסמנים לפי הנתיב.
  var nav = document.querySelector(".site-nav");
  if (nav && !nav.querySelector('[aria-current="page"]')) {
    var norm = function (u) { return u.replace(/index\.html$/, "").replace(/\/?$/, "/"); };
    var here = norm(location.pathname);
    nav.querySelectorAll("a").forEach(function (a) {
      if (norm(new URL(a.href, location.href).pathname) === here) a.setAttribute("aria-current", "page");
    });
  }

  // גרפים: לחיצה (או נגיעה) על נקודה או עמודה פותחת תווית. נקודות קטנות: הקרובה ביותר
  // בטווח של כמה פיקסלים, כדי שאפשר יהיה לפגוע בה גם באצבע.
  var tip = null, tipOn = null;
  function hideTip() { if (tip) tip.remove(); tip = null; if (tipOn) tipOn.classList.remove("is-on"); tipOn = null; }
  document.addEventListener("click", function (ev) {
    var svg = ev.target.closest && ev.target.closest("svg.chart");
    if (!svg) { hideTip(); return; }
    var hit = ev.target.closest("[data-tip]");
    if (!hit) {
      var best = null, bestD = 18;
      svg.querySelectorAll("circle[data-tip]").forEach(function (c) {
        var r = c.getBoundingClientRect(), d = Math.hypot(r.left + r.width / 2 - ev.clientX, r.top + r.height / 2 - ev.clientY);
        if (d < bestD) { bestD = d; best = c; }
      });
      hit = best;
    }
    hideTip();
    if (!hit || !hit.getAttribute("data-tip")) return;
    var box = hit.getBoundingClientRect();
    tip = document.createElement("div");
    tip.className = "chart-tip"; tip.setAttribute("role", "status");
    tip.textContent = hit.getAttribute("data-tip");
    document.body.appendChild(tip);
    var x = box.left + box.width / 2 + window.scrollX, y = box.top + window.scrollY;
    var half = tip.offsetWidth / 2, maxX = document.documentElement.clientWidth - 8 + window.scrollX;
    x = Math.min(Math.max(x, half + 8 + window.scrollX), maxX - half);
    tip.style.left = (x - tip.offsetWidth) + "px"; tip.style.top = y + "px";
    tip.style.transform = "translate(50%, calc(-100% - 8px))";
    if (hit.classList.contains("chart-dot")) { hit.classList.add("is-on"); tipOn = hit; }
  });
  document.addEventListener("keydown", function (ev) { if (ev.key === "Escape") hideTip(); });

  // חתך העומק: זום בצביטה (או בכפתורים), וגרירה לצדדים כשהתרשים מוגדל.
  // הזום "סמנטי": המיקומים מחושבים מחדש מהערכים שב-data-*, אז הנקודות מתרווחות ולא גדלות.
  document.querySelectorAll("svg[data-zoom]").forEach(function (svg) {
    var NS = "http://www.w3.org/2000/svg", ds = svg.dataset;
    var X0 = +ds.x0, X1 = +ds.x1, DMAX = +ds.dmax, W = +ds.w, H = +ds.h;
    var L = +ds.l, R = +ds.r, T = +ds.t, B = +ds.b, CW = W - L - R, CH = H - T - B;
    var MAXK = 12;
    // התצוגה: טווח x ‏[a, b] (a בצד ימין) וטווח עומק [d0, d1]
    var v = { a: X0, b: X1, d0: 0, d1: DMAX };
    var dots = svg.querySelectorAll("circle[data-x]"), rects = svg.querySelectorAll("rect[data-x1]");
    var labels = svg.querySelectorAll(".cz-bands text"), grid = svg.querySelector(".cz-grid");
    var ylab = svg.querySelector(".cz-ylabels"), xlab = svg.querySelector(".cz-xlabels");
    var angle = (labels[0] && /rotate\(([-\d.]+)\)/.exec(labels[0].getAttribute("transform")) || [0, 0])[1];
    function px(x) { return W - R - (x - v.a) / (v.b - v.a) * CW; }
    function py(d) { return T + (d - v.d0) / (v.d1 - v.d0) * CH; }
    function k() { return (X1 - X0) / (v.b - v.a); }
    function el(name, attrs, text) {
      var e = document.createElementNS(NS, name);
      for (var n in attrs) e.setAttribute(n, attrs[n]);
      if (text != null) e.textContent = text;
      return e;
    }
    function step(span, target) {
      var raw = span / target, p = Math.pow(10, Math.floor(Math.log10(raw)));
      return [1, 2, 5, 10].map(function (m) { return m * p; }).find(function (s) { return s >= raw; });
    }
    function clamp() {
      var w = v.b - v.a, h = v.d1 - v.d0;
      if (v.a < X0) { v.a = X0; v.b = X0 + w; }
      if (v.b > X1) { v.b = X1; v.a = X1 - w; }
      if (v.d0 < 0) { v.d0 = 0; v.d1 = h; }
      if (v.d1 > DMAX) { v.d1 = DMAX; v.d0 = DMAX - h; }
    }
    function draw() {
      hideTip();
      dots.forEach(function (c) {
        c.setAttribute("cx", px(+c.dataset.x).toFixed(1));
        c.setAttribute("cy", py(Math.min(+c.dataset.d, DMAX)).toFixed(1));
      });
      rects.forEach(function (r) {
        var p1 = px(+r.dataset.x1), p2 = px(+r.dataset.x2);
        r.setAttribute("x", Math.min(p1, p2).toFixed(1)); r.setAttribute("width", Math.abs(p2 - p1).toFixed(1));
      });
      // שם המקטע במרכז החלק הנראה של הרצועה; מקטע שיצא מהתצוגה — בלי שם
      labels.forEach(function (t) {
        var p1 = Math.max(Math.min(px(+t.dataset.x1), px(+t.dataset.x2)), L);
        var p2 = Math.min(Math.max(px(+t.dataset.x1), px(+t.dataset.x2)), W - R);
        t.style.display = p2 - p1 < 6 ? "none" : "";
        t.setAttribute("transform", "translate(" + ((p1 + p2) / 2).toFixed(1) + "," + (T - 5) + ") rotate(" + angle + ")");
      });
      [grid, ylab, xlab].forEach(function (g) { g.textContent = ""; });
      var sd = step(v.d1 - v.d0, 4);
      for (var d = Math.ceil(v.d0 / sd - 1e-6) * sd; d <= v.d1 + 1e-9; d += sd) {
        var y = py(d).toFixed(1), lbl = +d.toFixed(2);
        grid.appendChild(el("line", { "class": "chart-grid", x1: L, x2: W - R, y1: y, y2: y }));
        ylab.appendChild(el("text", { "class": "chart-label", x: L - 4, y: +y + 4, "text-anchor": "end", direction: "ltr" }, lbl));
      }
      var sx = step(v.b - v.a, 6);
      for (var x = Math.ceil(v.a / sx - 1e-6) * sx; x <= v.b + 1e-9; x += sx) {
        var X = px(x);
        if (X < L + 8 || X > W - R - 8) continue;
        xlab.appendChild(el("text", { "class": "chart-label", x: X.toFixed(1), y: H - 6, "text-anchor": "middle" }, "‏" + (+x.toFixed(2)) + "°"));
      }
      svg.classList.toggle("is-zoomed", k() > 1.01);
      if (reset) reset.disabled = k() <= 1.01;
    }
    // זום סביב נקודה במסך (sx, sy ביחידות ה-SVG)
    function zoomAt(f, sx, sy) {
      var nk = Math.min(Math.max(k() * f, 1), MAXK); f = nk / k();
      var fx = (W - R - sx) / CW, fy = (sy - T) / CH;
      var cx = v.a + fx * (v.b - v.a), cy = v.d0 + fy * (v.d1 - v.d0);
      var w = (X1 - X0) / nk, h = DMAX / nk;
      v.a = cx - fx * w; v.b = v.a + w; v.d0 = cy - fy * h; v.d1 = v.d0 + h;
      clamp(); draw();
    }
    function toSvg(clientX, clientY) {
      var r = svg.getBoundingClientRect();
      return [(clientX - r.left) / r.width * W, (clientY - r.top) / r.height * H];
    }
    // צביטה ביד אחת או שתיים, גרירה באצבע אחת (רק לצדדים; גלילה אנכית נשארת לדף)
    var pts = {}, last = null, moved = false;
    function state() {
      var ids = Object.keys(pts), p = ids.map(function (i) { return pts[i]; });
      if (p.length === 1) return { x: p[0][0], y: p[0][1], dist: 0, n: 1 };
      if (p.length >= 2) return { x: (p[0][0] + p[1][0]) / 2, y: (p[0][1] + p[1][1]) / 2,
        dist: Math.hypot(p[0][0] - p[1][0], p[0][1] - p[1][1]), n: 2 };
      return null;
    }
    svg.addEventListener("pointerdown", function (ev) {
      pts[ev.pointerId] = toSvg(ev.clientX, ev.clientY); last = state(); moved = false;
    });
    svg.addEventListener("pointermove", function (ev) {
      if (!pts[ev.pointerId]) return;
      pts[ev.pointerId] = toSvg(ev.clientX, ev.clientY);
      var s = state();
      if (!last || s.n !== last.n) { last = s; return; }
      if (s.n === 2 && last.dist > 0) {
        zoomAt(s.dist / last.dist, s.x, s.y); moved = true;
      }
      if (k() > 1.01 && (s.n === 2 || ev.pointerType !== "touch" || Math.abs(s.x - last.x) > Math.abs(s.y - last.y))) {
        var dx = (s.x - last.x) / CW * (v.b - v.a), dy = (s.y - last.y) / CH * (v.d1 - v.d0);
        if (Math.abs(s.x - last.x) + Math.abs(s.y - last.y) > 0.5) moved = true;
        v.a += dx; v.b += dx;
        if (s.n === 2 || ev.pointerType !== "touch") { v.d0 -= dy; v.d1 -= dy; }
        clamp(); draw();
      }
      last = s;
    });
    function up(ev) { delete pts[ev.pointerId]; last = state(); }
    ["pointerup", "pointercancel", "pointerleave"].forEach(function (t) { svg.addEventListener(t, up); });
    // אחרי גרירה או צביטה לא פותחים תווית
    svg.addEventListener("click", function (ev) { if (moved) { ev.stopPropagation(); moved = false; } }, true);
    svg.addEventListener("wheel", function (ev) {
      if (!ev.ctrlKey && !ev.metaKey) return;  // גלגלת רגילה גוללת את הדף
      ev.preventDefault();
      var p = toSvg(ev.clientX, ev.clientY);
      zoomAt(ev.deltaY < 0 ? 1.25 : 0.8, p[0], p[1]);
    }, { passive: false });
    svg.addEventListener("dblclick", function (ev) {
      var p = toSvg(ev.clientX, ev.clientY); zoomAt(2, p[0], p[1]);
    });
    // כפתורים, גם למקלדת ולמי שלא צובט
    var bar = document.createElement("div");
    bar.className = "chart-zoom";
    bar.innerHTML = '<span class="chart-zoom-hint">' +
      (matchMedia("(pointer: coarse)").matches ? "אפשר לקרב בצביטה" : "לקירוב: לחיצה כפולה או Ctrl וגלגלת") + "</span>" +
      '<button type="button" data-z="in" aria-label="הגדלה">+</button>' +
      '<button type="button" data-z="out" aria-label="הקטנה">−</button>' +
      '<button type="button" data-z="reset">איפוס</button>';
    svg.parentNode.insertBefore(bar, svg.nextSibling);
    var reset = bar.querySelector('[data-z="reset"]');
    bar.addEventListener("click", function (ev) {
      var b = ev.target.closest("button"); if (!b) return;
      hideTip();
      if (b.dataset.z === "reset") { v = { a: X0, b: X1, d0: 0, d1: DMAX }; draw(); }
      else zoomAt(b.dataset.z === "in" ? 2 : 0.5, L + CW / 2, T);  // אנכית: מפני הקרקע, שם רוב הרעידות
    });
    draw();
  });

  // איך מוצאים את מוקד-העל: האנימציה מתנגנת כשהתרשים נכנס למסך, ובכפתור "הפעלה חוזרת"
  var tri = document.querySelector(".tri");
  if (tri) {
    var play = function () { tri.classList.remove("play"); void tri.offsetWidth; tri.classList.add("play"); };
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (es) { if (es[0].isIntersecting) { play(); io.disconnect(); } }, { threshold: 0.5 });
      io.observe(tri);
    }
    tri.querySelector(".tri-replay").addEventListener("click", play);
  }

  // מצב כהה/בהיר: מחליף בין שני המצבים, וזוכר את הבחירה בדפדפן בלבד.
  var toggle = document.querySelector("[data-theme-toggle]");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var root = document.documentElement;
      var dark = root.dataset.theme
        ? root.dataset.theme === "dark"
        : window.matchMedia("(prefers-color-scheme: dark)").matches;
      root.dataset.theme = dark ? "light" : "dark";
      if (typeof PRIVACY !== "undefined") PRIVACY.set("riftmemory.theme", root.dataset.theme);
      else { try { localStorage.setItem("riftmemory.theme", root.dataset.theme); } catch (e) {} }
    });
  }

  // הערות שוליים: לחיצה על מספר ההערה פותחת את המקור בחלון צף בתחתית המסך.
  // לחיצה או נגיעה בכל מקום אחר (או Esc) סוגרת אותו.
  var sheet = document.getElementById("source-sheet");
  if (sheet) {
    var body = sheet.querySelector(".source-sheet-body");
    var label = sheet.querySelector(".source-sheet-label");
    var close = function () { sheet.hidden = true; };
    document.addEventListener("click", function (ev) {
      var ref = ev.target.closest && ev.target.closest("a.footnote-ref");
      if (ref) {
        var note = document.getElementById(decodeURIComponent(ref.getAttribute("href").slice(1)));
        if (!note) return;
        ev.preventDefault();
        body.innerHTML = note.innerHTML;
        label.textContent = "מקור " + ref.textContent;
        sheet.hidden = false;
        return;
      }
      if (!sheet.hidden && !(ev.target.closest && ev.target.closest(".source-sheet-body a"))) close();
    });
    document.addEventListener("keydown", function (ev) { if (ev.key === "Escape") close(); });
  }

  window.addEventListener("load", function () {
    if (!window.L) return;
    document.querySelectorAll(".map[data-map]").forEach(initMap);
  });
})();
