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
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 12,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    var css = getComputedStyle(document.documentElement);
    var colors = {
      texts: css.getPropertyValue("--texts").trim(),
      archaeology: css.getPropertyValue("--archaeology").trim(),
      instrumental: css.getPropertyValue("--instrumental").trim(),
      live: css.getPropertyValue("--live").trim(),
      rust: css.getPropertyValue("--rust").trim()
    };
    var bounds = [];

    data.segments.forEach(function (s) {
      var b = [[s.bbox[0], s.bbox[1]], [s.bbox[2], s.bbox[3]]];
      L.rectangle(b, { color: colors.rust, weight: 1, fillOpacity: 0.12 })
        .bindTooltip(s.name).addTo(map);
      bounds.push(b[0], b[1]);
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

    if (bounds.length > 1) map.fitBounds(bounds, { padding: [20, 20], maxZoom: 9 });
    else if (bounds.length === 1) map.setView(bounds[0], 8);
  }

  window.addEventListener("load", function () {
    if (!window.L) return;
    document.querySelectorAll(".map[data-map]").forEach(initMap);
  });
})();
