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

  function initMap(el) {
    var data = JSON.parse(el.dataset.map);
    var map = L.map(el, { scrollWheelZoom: false, minZoom: 5, maxZoom: 10 }).setView([31.8, 35.2], 7);
    var css = getComputedStyle(document.documentElement);

    // מפת בסיס מקומית (Natural Earth, נחלת הכלל): ים, אגמים, נהרות ושמות ערים.
    // בלי שרת אריחים חיצוני: CARTO דורש מפתח, ו-OSM מסמן שטחים צבאיים בוורוד.
    map.createPane("base").style.zIndex = 200;
    map.createPane("cities").style.zIndex = 250;
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
      live: css.getPropertyValue("--quake").trim(),
      rust: css.getPropertyValue("--accent").trim()
    };
    var bounds = [];
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
        L.polyline(latlngs, {
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

    data.live.forEach(function (q) {
      L.circleMarker([q.lat, q.lon], {
        radius: data.dot_scale ? Math.max(2, (q.mag - 2) * data.dot_scale) : Math.max(3, q.mag * 1.6),
        color: colors.live, weight: data.dot_scale ? 0.5 : 1, fillOpacity: data.dot_scale ? 0.35 : 0.6
      }).bindPopup('<div class="map-popup"><strong>' + esc(q.label) + '</strong><br><bdi dir="ltr">M' + q.mag + "</bdi>" +
        (q.depth != null ? " · עומק " + q.depth + " ק״מ" : "") +
        '<div class="src">' + esc(q.local || ago(q.time_utc) || "") + "</div>" +
        (q.url ? '<div class="src"><a href="' + q.url + '">לכל הפרטים ←</a></div>' : "") + "</div>")
        .addTo(map);
      bounds.push([q.lat, q.lon]);
    });

    // מקומות שנפגעו: המקומות שהדפים מתארים בהם נזק (לא מוקדים). ריבוע קטן, ובלחיצה: מה קרה שם ובאיזו רעידה.
    var dmgBounds = [];
    if (data.damage && data.damage.length) map.attributionControl.addAttribution('<a href="https://www.geonames.org">GeoNames</a>');
    (data.damage || []).forEach(function (d) {
      var icon = L.divIcon({ className: "dmg" + (d.doubtful ? " doubtful" : ""), iconSize: [8, 8] });
      var html = '<div class="map-popup"><strong>' + esc(d.name) + "</strong>" + d.entries.map(function (x) {
        return '<div class="dmg-entry"><a href="' + x.url + '">' + esc(x.title) + "</a>" +
          (x.place !== d.name ? " (" + esc(x.place) + ")" : "") + ": " + esc(x.what) +
          '<div class="src">' + esc(x.status) + "</div></div>";
      }).join("") + "</div>";
      L.marker([d.lat, d.lon], { icon: icon, keyboard: false }).bindPopup(html).addTo(map);
      dmgBounds.push([d.lat, d.lon]);
    });

    // רעידות היסטוריות: המיקום משוער בלבד. עיגול גדול ושקוף מראה שאין כאן נקודה מדויקת,
    // והחלון שנפתח בלחיצה אומר לפי איזה חוקר נקבע המיקום ומפנה לביבליוגרפיה בדף הרעידה.
    var hist = [];
    data.events.forEach(function (e) {
      var popup = '<div class="map-popup"><a href="' + e.url + '"><strong>' + esc(e.title) + "</strong></a><br>" + esc(e.year) +
        "<br><strong>מיקום משוער</strong>" +
        (e.source ? '<div class="src">לפי: ' + (e.source_url
          ? '<a href="' + esc(e.source_url) + '" rel="noopener">' + esc(e.source) + "</a>"
          : esc(e.source)) + "</div>" : "") +
        '<div class="src"><a href="' + e.url + '#bibliography">לביבליוגרפיה המלאה</a></div></div>';
      var area = L.circle([e.lat, e.lon], {
        radius: 30000, color: colors.rust, weight: 1.5, dashArray: "4 4",
        fillColor: colors.rust, fillOpacity: 0.15
      }).bindPopup(popup).addTo(map);
      L.circleMarker([e.lat, e.lon], {
        radius: 4, stroke: false, fillColor: colors.rust, fillOpacity: 1
      }).bindPopup(popup).addTo(map);
      area.bindTooltip("מיקום משוער · " + esc(e.year), { permanent: true, direction: "right", offset: [12, 0], className: "approx-label" });
      hist.push([e.lat, e.lon]);
    });

    // תמיד רואים את כל קו השבר בארץ, ובנוסף את הרעידות הקרובות שעל המפה.
    // רעידות רחוקות (כרתים, סוריה) נשארות על המפה אבל לא מרחיקות את המבט מהארץ,
    // חוץ מבדף של הרעידה עצמה (focus).
    var inRegion = function (p) { return p[0] > 29 && p[0] < 33.6 && p[1] > 34 && p[1] < 36.6; };
    var near = bounds.concat(data.focus ? [] : hist).filter(inRegion);
    var all = faultBounds.filter(function (p) { return p[0] < 33.4; }).concat(near, data.focus ? hist : []);
    // מפה של מקטע בלבד (בלי מיקום לרעידה): המבט על המקטע והמקומות שנפגעו, עם מעט סביבה
    if (data.focus && !hist.length && (segBounds.length || dmgBounds.length)) {
      all = segBounds.concat(near, dmgBounds);
      map.fitBounds(L.latLngBounds(all).pad(0.6), { maxZoom: 9 });
      return;
    }
    if (all.length > 1) map.fitBounds(all, { padding: [24, 24], maxZoom: 9 });
    else if (all.length === 1) map.setView(all[0], 8);
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
      try { localStorage.setItem("riftmemory.theme", root.dataset.theme); } catch (e) {}
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
