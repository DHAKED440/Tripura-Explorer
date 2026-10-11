/* Leaflet map for /map plus the small location map on a destination page.
   Marker data always comes from /api/places/map (published records only). */
(function () {
  "use strict";

  var settingsNode = document.getElementById("map-settings");
  if (!settingsNode) return;
  var settings = JSON.parse(settingsNode.textContent || "{}");

  function readJson(node) {
    try {
      return JSON.parse(node.textContent || "{}");
    } catch (error) {
      return {};
    }
  }

  var mapElement = document.getElementById("map");
  var placeMapElement = document.getElementById("place-map");

  if (!window.L) {
    var message = document.getElementById("map-message");
    if (message) {
      message.innerHTML =
        '<div class="alert alert--error">The map library could not be loaded from the CDN. ' +
        "The destination list below still works, and every card links to the details page.</div>";
    }
    if (mapElement) mapElement.style.display = "none";
    if (placeMapElement) placeMapElement.style.display = "none";
    loadListFallback();
    return;
  }

  function tileLayer() {
    return L.tileLayer(settings.tile_url, {
      maxZoom: settings.max_zoom || 18,
      attribution: settings.attribution
    });
  }

  function makeIcon(approximate) {
    return L.divIcon({
      className: "",
      html:
        '<div class="marker-pin ' +
        (approximate ? "marker-pin--approximate" : "") +
        '"><span>●</span></div>',
      iconSize: [30, 30],
      iconAnchor: [15, 28],
      popupAnchor: [0, -26]
    });
  }

  /* ---------------------------------------------------------------- main map */
  if (mapElement) {
    var map = L.map(mapElement, {
      center: settings.center,
      zoom: settings.zoom,
      scrollWheelZoom: true
    });
    tileLayer().addTo(map);

    var layer = L.layerGroup().addTo(map);
    var status = document.getElementById("map-status");
    var results = document.getElementById("map-results");
    var messageBox = document.getElementById("map-message");
    var categorySelect = document.getElementById("map-category");
    var districtSelect = document.getElementById("map-district");
    var verifiedCheckbox = document.getElementById("map-verified");

    function popupHtml(place) {
      var image = place.image_url
        ? '<img src="' + place.image_url + '" alt="" style="width:100%;height:90px;object-fit:cover;border-radius:8px">'
        : "";
      return (
        '<div style="min-width:180px">' +
        image +
        '<strong style="display:block;margin-top:6px">' +
        place.name +
        "</strong>" +
        '<span style="color:#6b7280;font-size:.82rem">' +
        (place.category || "") +
        (place.district ? " · " + place.district : "") +
        "</span>" +
        (place.coordinates_verified ? "" : '<br><span class="badge badge--pending">approximate</span>') +
        '<br><a href="' + place.url + '">View details</a></div>'
      );
    }

    function renderPlaces(places) {
      layer.clearLayers();
      results.innerHTML = "";
      var bounds = [];
      places.forEach(function (place) {
        var marker = L.marker([place.lat, place.lng], { icon: makeIcon(!place.coordinates_verified) });
        marker.bindPopup(popupHtml(place));
        marker.addTo(layer);
        bounds.push([place.lat, place.lng]);

        var item = document.createElement("button");
        item.type = "button";
        item.className = "map-result";
        item.innerHTML =
          (place.image_url ? '<img src="' + place.image_url + '" alt="">' : "") +
          "<span><strong>" +
          place.name +
          '</strong><br><span style="color:#6b7280;font-size:.8rem">' +
          (place.category || "") +
          "</span></span>";
        item.addEventListener("click", function () {
          map.setView([place.lat, place.lng], 12);
          marker.openPopup();
        });
        results.appendChild(item);
      });
      if (bounds.length) {
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 11 });
      }
      return bounds.length;
    }

    function load() {
      var params = new URLSearchParams();
      if (categorySelect.value) params.set("category", categorySelect.value);
      if (districtSelect.value) params.set("district", districtSelect.value);
      if (verifiedCheckbox.checked) params.set("verified", "1");

      status.textContent = "Loading destinations…";
      results.setAttribute("aria-busy", "true");
      messageBox.innerHTML = "";

      fetch("/api/places/map?" + params.toString(), { headers: { Accept: "application/json" } })
        .then(function (response) {
          if (!response.ok) throw new Error("Map data request failed (" + response.status + ")");
          return response.json();
        })
        .then(function (data) {
          var count = renderPlaces(data.places);
          status.textContent =
            count +
            " destination" +
            (count === 1 ? "" : "s") +
            " with coordinates" +
            (data.coordinates_verified < count ? " · " + (count - data.coordinates_verified) + " approximate" : "");
          if (data.published_without_coordinates) {
            messageBox.innerHTML =
              '<div class="alert alert--warning">' +
              data.published_without_coordinates +
              " published destination(s) have no coordinates yet, so they are not on the map.</div>";
          }
          if (!count) {
            status.textContent = "No destination matches these filters.";
          }
        })
        .catch(function (error) {
          status.textContent = "Could not load the map data.";
          messageBox.innerHTML = '<div class="alert alert--error">' + error.message + "</div>";
        })
        .finally(function () {
          results.removeAttribute("aria-busy");
        });
    }

    document.querySelector("[data-map-apply]").addEventListener("click", load);
    document.querySelector("[data-map-reset]").addEventListener("click", function () {
      categorySelect.value = "";
      districtSelect.value = "";
      verifiedCheckbox.checked = false;
      map.setView(settings.center, settings.zoom);
      load();
    });
    load();
  }

  function loadListFallback() {
    var results = document.getElementById("map-results");
    var status = document.getElementById("map-status");
    if (!results) return;
    fetch("/api/places/map", { headers: { Accept: "application/json" } })
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        if (status) status.textContent = data.count + " destinations with coordinates";
        data.places.forEach(function (place) {
          var link = document.createElement("a");
          link.className = "map-result";
          link.href = place.url;
          link.innerHTML = "<span><strong>" + place.name + "</strong></span>";
          results.appendChild(link);
        });
      })
      .catch(function () {
        if (status) status.textContent = "Map data could not be loaded.";
      });
  }

  /* ------------------------------------------------------- destination map */
  if (placeMapElement) {
    var lat = parseFloat(placeMapElement.getAttribute("data-lat"));
    var lng = parseFloat(placeMapElement.getAttribute("data-lng"));
    var approximate = placeMapElement.getAttribute("data-approximate") === "true";
    var mini = L.map(placeMapElement, { center: [lat, lng], zoom: 12, scrollWheelZoom: false });
    tileLayer().addTo(mini);
    var miniMarker = L.marker([lat, lng], { icon: makeIcon(approximate) }).addTo(mini);
    miniMarker.bindPopup(placeMapElement.getAttribute("data-name") || "Destination");
  }
})();