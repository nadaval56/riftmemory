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
    var map = L.map(el, { scrollWheelZoom: false }).setView([31.8, 35.2], 7);
    // מפת בסיס נקייה (CARTO), בגרסה בהירה או כהה לפי ערכת הנושא.
    // מפת OSM הרגילה מסמנת שטחי אש ואזורים צבאיים בפוליגונים ורודים, שמבלבלים עם שכבות האתר.
    var root = document.documentElement;
    var dark = root.dataset.theme
      ? root.dataset.theme === "dark"
      : window.matchMedia("(prefers-color-scheme: dark)").matches;
    L.tileLayer("https://{s}.basemaps.cartocdn.com/" + (dark ? "dark_all" : "light_all") + "/{z}/{x}/{y}{r}.png", {
      maxZoom: 12, subdomains: "abcd",
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
    }).addTo(map);

    var css = getComputedStyle(document.documentElement);
    var colors = {
      texts: css.getPropertyValue("--texts").trim(),
      archaeology: css.getPropertyValue("--archaeology").trim(),
      instrumental: css.getPropertyValue("--instrumental").trim(),
      live: css.getPropertyValue("--live").trim(),
      rust: css.getPropertyValue("--accent").trim()
    };
    var bounds = [];
    var faultBounds = [];

    // קווי ההעתקים (GEM / EMME), מקובצים לפי מקטע
    data.segments.forEach(function (s) {
      s.lines.forEach(function (line) {
        var latlngs = line.map(function (c) { return [c[1], c[0]]; });
        L.polyline(latlngs, { color: colors.rust, weight: 3, opacity: 0.85, dashArray: s.draft ? "6 5" : null })
          .bindTooltip(s.name, { sticky: true }).addTo(map);
        latlngs.forEach(function (p) { faultBounds.push(p); });
      });
    });

    data.live.forEach(function (q) {
      L.circleMarker([q.lat, q.lon], {
        radius: Math.max(3, q.mag * 1.6), color: colors.live, weight: 1, fillOpacity: 0.6
      }).bindPopup("<strong>" + (q.label || "") + "</strong><br>M" + q.mag + " · " + (ago(q.time_utc) || ""))
        .addTo(map);
      bounds.push([q.lat, q.lon]);
    });

    data.events.forEach(function (e) {
      L.circleMarker([e.lat, e.lon], {
        radius: 9, color: "#fff", weight: 2, fillColor: colors[e.kind] || colors.texts, fillOpacity: 1
      }).bindPopup('<a href="' + e.url + '"><strong>' + e.title + "</strong></a><br>" + e.year)
        .addTo(map);
      bounds.push([e.lat, e.lon]);
    });

    // תמיד רואים את כל קו השבר בארץ, ובנוסף את הרעידות שעל המפה
    // רעידות רחוקות (קפריסין, סוריה) נשארות על המפה אבל לא מרחיקות את המבט מהארץ
    var near = bounds.filter(function (p) { return p[0] > 29 && p[0] < 33.6 && p[1] > 34 && p[1] < 36.6; });
    var all = faultBounds.filter(function (p) { return p[0] < 33.4; }).concat(near);
    if (all.length > 1) map.fitBounds(all, { padding: [16, 16], maxZoom: 9 });
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
