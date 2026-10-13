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

    var currentPlaces = [];
    var userCoords = null;
    var userMarker = null;
    var watchId = null;
    var routePolyline = null;
    var activePlace = null;

    var locateBtn = document.getElementById("map-locate-me");
    var recenterBtn = document.getElementById("map-recenter-btn");
    var startJourneyBtn = document.getElementById("map-start-journey-btn");

    var floatingBar = document.getElementById("map-floating-bar");
    var floatingRecenterBtn = document.getElementById("floating-recenter-btn");
    var floatingJourneyBtn = document.getElementById("floating-journey-btn");

    var journeyHud = document.getElementById("journey-hud");
    var journeyDestSelect = document.getElementById("journey-destination-select");
    var journeyStats = document.getElementById("journey-stats");
    var journeyDistVal = document.getElementById("journey-distance-val");
    var journeyTimeVal = document.getElementById("journey-time-val");
    var journeyNavBtn = document.getElementById("journey-turn-by-turn-link");
    var journeyRecenterBtn = document.getElementById("journey-recenter-action");
    var journeyCloseBtn = document.getElementById("journey-close-btn");

    function calculateDistanceKm(lat1, lon1, lat2, lon2) {
      var R = 6371; // Earth's radius in km
      var dLat = ((lat2 - lat1) * Math.PI) / 180;
      var dLon = ((lon2 - lon1) * Math.PI) / 180;
      var a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos((lat1 * Math.PI) / 180) *
          Math.cos((lat2 * Math.PI) / 180) *
          Math.sin(dLon / 2) *
          Math.sin(dLon / 2);
      var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      return R * c;
    }

    function formatTravelTime(distKm) {
      // Tripura highway & winding mountain road estimation (~1.35 road factor @ 38 km/h)
      var roadDist = distKm * 1.35;
      var totalMinutes = Math.round((roadDist / 38.0) * 60);
      if (totalMinutes < 5) return "Under 5 mins";
      if (totalMinutes < 60) return "~" + totalMinutes + " mins";
      var hrs = Math.floor(totalMinutes / 60);
      var mins = totalMinutes % 60;
      return "~" + hrs + " hr " + (mins > 0 ? mins + " mins" : "");
    }

    function popupHtml(place) {
      var image = place.image_url
        ? '<img src="' + place.image_url + '" alt="" style="width:100%;height:100px;object-fit:cover;border-radius:8px">'
        : "";
      return (
        '<div style="min-width:210px">' +
        image +
        '<strong style="display:block;margin-top:6px;font-size:1.02rem">' +
        place.name +
        "</strong>" +
        '<span style="color:#6b7280;font-size:.82rem">' +
        (place.category || "") +
        (place.district ? " · " + place.district : "") +
        "</span>" +
        '<div style="display:flex;gap:6px;margin-top:10px;flex-wrap:wrap">' +
        '<button class="btn btn--sm btn--journey" type="button" data-start-trip="' + place.id + '">Start Journey</button>' +
        '<a class="btn btn--sm btn--primary" href="https://www.google.com/maps/dir/?api=1&destination=' +
        place.lat.toFixed(6) + ',' + place.lng.toFixed(6) +
        '&travelmode=driving" target="_blank" rel="noopener noreferrer" data-live-directions data-lat="' +
        place.lat + '" data-lng="' + place.lng + '" data-name="' + place.name + '">Directions</a>' +
        '<a class="btn btn--sm btn--ghost" href="' + place.url + '">Details</a>' +
        '</div></div>'
      );
    }

    function renderPlaces(places) {
      currentPlaces = places || [];
      layer.clearLayers();
      results.innerHTML = "";
      var bounds = [];

      currentPlaces.forEach(function (place) {
        var marker = L.marker([place.lat, place.lng], { icon: makeIcon(false) });
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
          map.setView([place.lat, place.lng], 13);
          marker.openPopup();
        });
        results.appendChild(item);
      });

      if (userCoords) {
        bounds.push([userCoords.lat, userCoords.lng]);
      }

      if (bounds.length && !activePlace) {
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 11 });
      }

      if (journeyHud && journeyHud.style.display !== "none") {
        populateDestinationOptions(activePlace ? (activePlace.id || activePlace.slug) : null);
      }

      return currentPlaces.length;
    }

    /* Handle popup Start Journey click */
    map.on("popupopen", function (e) {
      var container = e.popup.getElement();
      if (!container) return;
      var tripBtn = container.querySelector("[data-start-trip]");
      if (tripBtn) {
        tripBtn.addEventListener("click", function (evt) {
          evt.preventDefault();
          var pId = tripBtn.getAttribute("data-start-trip");
          map.closePopup();
          startJourney(pId);
        });
      }
    });

    /* Live GPS tracking & marker updates */
    function updateUserMarker(lat, lng, accuracy) {
      userCoords = { lat: lat, lng: lng, accuracy: accuracy };

      var popupText = '<strong style="color:#2563eb">Your Live GPS Location</strong><br>Accuracy: ' + Math.round(accuracy) + 'm';
      if (!userMarker) {
        var liveIcon = L.divIcon({
          className: "",
          html: '<div style="background:#2563eb;width:20px;height:20px;border-radius:50%;border:3px solid #ffffff;box-shadow:0 0 14px rgba(37,99,235,0.85);animation:pulse 1.8s infinite;"></div>',
          iconSize: [22, 22],
          iconAnchor: [11, 11]
        });
        userMarker = L.marker([lat, lng], { icon: liveIcon, zIndexOffset: 1000 }).addTo(map);
        userMarker.bindPopup(popupText);
      } else {
        userMarker.setLatLng([lat, lng]);
        if (userMarker.getPopup()) {
          userMarker.getPopup().setContent(popupText);
        }
      }

      // Reveal Recenter and Journey buttons
      if (recenterBtn) recenterBtn.style.display = "inline-flex";
      if (startJourneyBtn) startJourneyBtn.style.display = "inline-flex";
      if (floatingBar) floatingBar.style.display = "flex";

      // If a journey is currently active, re-draw route and refresh metrics
      if (activePlace) {
        drawRouteTo(activePlace);
      }
    }

    function acquireLocation(onSuccess, onError) {
      if (!navigator.geolocation) {
        if (window.TripuraExplore) window.TripuraExplore.showToast("Geolocation is not supported by your browser.", "error");
        if (onError) onError();
        return;
      }

      if (locateBtn) {
        locateBtn.disabled = true;
        locateBtn.innerHTML = '<span class="spinner"></span> Locating…';
      }

      navigator.geolocation.getCurrentPosition(
        function (pos) {
          if (locateBtn) {
            locateBtn.disabled = false;
            locateBtn.innerHTML = '● Live GPS Active';
          }
          var uLat = pos.coords.latitude;
          var uLng = pos.coords.longitude;
          updateUserMarker(uLat, uLng, pos.coords.accuracy || 10);

          // Continuous background watch for smooth real-time tracking
          if (!watchId && navigator.geolocation.watchPosition) {
            watchId = navigator.geolocation.watchPosition(
              function (wPos) {
                updateUserMarker(wPos.coords.latitude, wPos.coords.longitude, wPos.coords.accuracy || 10);
              },
              function (wErr) {
                console.warn("GPS watch position notice:", wErr.message);
              },
              { enableHighAccuracy: true, maximumAge: 3000 }
            );
          }

          if (onSuccess) onSuccess(userCoords);
        },
        function (err) {
          if (locateBtn) {
            locateBtn.disabled = false;
            locateBtn.innerHTML = 'Live Location';
          }
          if (window.TripuraExplore) {
            window.TripuraExplore.showToast("Could not retrieve live GPS position: " + err.message, "error");
          }
          if (onError) onError(err);
        },
        {
          enableHighAccuracy: true,
          timeout: 12000,
          maximumAge: 0
        }
      );
    }

    function recenterMap() {
      if (!userCoords) {
        acquireLocation(function (coords) {
          map.setView([coords.lat, coords.lng], 14, { animate: true });
          if (userMarker) userMarker.openPopup();
          if (window.TripuraExplore) window.TripuraExplore.showToast("Map centered on your live GPS position.", "success");
        });
        return;
      }
      map.setView([userCoords.lat, userCoords.lng], 14, { animate: true });
      if (userMarker) userMarker.openPopup();
      if (window.TripuraExplore) window.TripuraExplore.showToast("Map recentered to your live GPS position.", "success");
    }

    function populateDestinationOptions(selectedIdOrSlug) {
      if (!journeyDestSelect) return;
      journeyDestSelect.innerHTML = '<option value="">-- Choose destination to travel to --</option>';

      var sorted = currentPlaces.slice();
      if (userCoords) {
        sorted.sort(function (a, b) {
          var dA = calculateDistanceKm(userCoords.lat, userCoords.lng, a.lat, a.lng);
          var dB = calculateDistanceKm(userCoords.lat, userCoords.lng, b.lat, b.lng);
          return dA - dB;
        });
      }

      sorted.forEach(function (place) {
        var opt = document.createElement("option");
        opt.value = place.id || place.slug;
        var distText = "";
        if (userCoords) {
          var dist = calculateDistanceKm(userCoords.lat, userCoords.lng, place.lat, place.lng);
          distText = " · " + dist.toFixed(1) + " km";
        }
        opt.textContent = place.name + distText + (place.district ? " (" + place.district + ")" : "");
        if (selectedIdOrSlug && (String(place.id) === String(selectedIdOrSlug) || place.slug === selectedIdOrSlug)) {
          opt.selected = true;
        }
        journeyDestSelect.appendChild(opt);
      });
    }

    function drawRouteTo(place) {
      if (!userCoords || !place) return;
      activePlace = place;

      if (routePolyline) {
        map.removeLayer(routePolyline);
      }

      // Draw active route polyline on Leaflet map
      routePolyline = L.polyline(
        [
          [userCoords.lat, userCoords.lng],
          [place.lat, place.lng]
        ],
        {
          color: "#059669",
          weight: 5,
          opacity: 0.9,
          dashArray: "8, 8"
        }
      ).addTo(map);

      var dist = calculateDistanceKm(userCoords.lat, userCoords.lng, place.lat, place.lng);
      var timeEst = formatTravelTime(dist);

      if (journeyStats) journeyStats.style.display = "grid";
      if (journeyDistVal) journeyDistVal.textContent = dist.toFixed(1) + " km";
      if (journeyTimeVal) journeyTimeVal.textContent = timeEst;

      if (journeyNavBtn) {
        journeyNavBtn.href =
          "https://www.google.com/maps/dir/?api=1&origin=" +
          userCoords.lat.toFixed(6) +
          "," +
          userCoords.lng.toFixed(6) +
          "&destination=" +
          place.lat.toFixed(6) +
          "," +
          place.lng.toFixed(6) +
          "&travelmode=driving";
      }

      // Fit map view to frame both live user location and destination
      map.fitBounds(
        [
          [userCoords.lat, userCoords.lng],
          [place.lat, place.lng]
        ],
        { padding: [70, 70], maxZoom: 14 }
      );
    }

    function startJourney(targetIdOrSlug) {
      if (!userCoords) {
        if (window.TripuraExplore) window.TripuraExplore.showToast("Acquiring your live GPS position to start journey…", "info");
        acquireLocation(function () {
          startJourney(targetIdOrSlug);
        });
        return;
      }

      if (journeyHud) {
        journeyHud.style.display = "block";
      }

      var chosen = null;
      if (targetIdOrSlug) {
        chosen = currentPlaces.find(function (p) {
          return String(p.id) === String(targetIdOrSlug) || p.slug === targetIdOrSlug;
        });
      }
      if (!chosen && journeyDestSelect && journeyDestSelect.value) {
        var selVal = journeyDestSelect.value;
        chosen = currentPlaces.find(function (p) {
          return String(p.id) === String(selVal) || p.slug === selVal;
        });
      }
      if (!chosen && currentPlaces.length) {
        // Pick nearest destination
        var sorted = currentPlaces.slice().sort(function (a, b) {
          return calculateDistanceKm(userCoords.lat, userCoords.lng, a.lat, a.lng) -
                 calculateDistanceKm(userCoords.lat, userCoords.lng, b.lat, b.lng);
        });
        chosen = sorted[0];
      }

      populateDestinationOptions(chosen ? (chosen.id || chosen.slug) : null);

      if (chosen) {
        drawRouteTo(chosen);
        if (startJourneyBtn) {
          startJourneyBtn.innerHTML = '● Trip to ' + (chosen.name.length > 14 ? chosen.name.slice(0, 12) + '…' : chosen.name);
        }
        if (window.TripuraExplore) {
          window.TripuraExplore.showToast("Journey started to " + chosen.name + "!", "success");
        }
      }
    }

    function endJourney() {
      if (routePolyline) {
        map.removeLayer(routePolyline);
        routePolyline = null;
      }
      activePlace = null;
      if (journeyHud) {
        journeyHud.style.display = "none";
      }
      if (startJourneyBtn) {
        startJourneyBtn.innerHTML = 'Start Journey';
      }
      if (window.TripuraExplore) {
        window.TripuraExplore.showToast("Journey ended.", "info");
      }
    }

    /* Event Listeners */
    if (locateBtn) {
      locateBtn.addEventListener("click", function () {
        acquireLocation(function (coords) {
          map.setView([coords.lat, coords.lng], 13);
          if (userMarker) userMarker.openPopup();
          if (window.TripuraExplore) window.TripuraExplore.showToast("Located your live position via GPS.", "success");
        });
      });
    }

    if (recenterBtn) recenterBtn.addEventListener("click", recenterMap);
    if (floatingRecenterBtn) floatingRecenterBtn.addEventListener("click", recenterMap);
    if (journeyRecenterBtn) journeyRecenterBtn.addEventListener("click", recenterMap);

    if (startJourneyBtn) {
      startJourneyBtn.addEventListener("click", function () {
        if (journeyHud && journeyHud.style.display !== "none") {
          recenterMap();
        } else {
          startJourney();
        }
      });
    }

    if (floatingJourneyBtn) {
      floatingJourneyBtn.addEventListener("click", function () {
        startJourney();
      });
    }

    if (journeyCloseBtn) journeyCloseBtn.addEventListener("click", endJourney);

    if (journeyDestSelect) {
      journeyDestSelect.addEventListener("change", function () {
        var val = journeyDestSelect.value;
        if (!val) return;
        var found = currentPlaces.find(function (p) {
          return String(p.id) === String(val) || p.slug === val;
        });
        if (found) {
          drawRouteTo(found);
          if (startJourneyBtn) {
            startJourneyBtn.innerHTML = '● Trip to ' + (found.name.length > 14 ? found.name.slice(0, 12) + '…' : found.name);
          }
        }
      });
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
            " verified destination" +
            (count === 1 ? "" : "s") +
            " with coordinates";
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
    var pName = placeMapElement.getAttribute("data-name") || "Destination";
    var mini = L.map(placeMapElement, { center: [lat, lng], zoom: 12, scrollWheelZoom: false });
    tileLayer().addTo(mini);
    var miniMarker = L.marker([lat, lng], { icon: makeIcon(false) }).addTo(mini);
    miniMarker.bindPopup(
      '<strong>' + pName + '</strong><br>' +
      '<a class="btn btn--sm btn--primary" style="margin-top:6px;display:inline-block;" ' +
      'href="https://www.google.com/maps/dir/?api=1&destination=' + lat.toFixed(6) + ',' + lng.toFixed(6) + '&travelmode=driving" ' +
      'target="_blank" rel="noopener noreferrer" data-live-directions data-lat="' + lat + '" data-lng="' + lng + '" data-name="' + pName + '">' +
      'Get directions</a>'
    );
  }
})();