/* Leaflet map for /map plus the small location map on a destination page.
   Marker data always comes from /api/places/map (published records only).

   === NAVIGATION SYSTEM ===
   Provides Google Maps-style live driving navigation:
   - Real GPS tracking via watchPosition
   - OSRM routing for actual road routes with turn instructions
   - Smooth animated car marker with heading rotation
   - Follow-me camera mode
   - Route progress, deviation detection, and rerouting
   - Pause/Resume/End journey controls
   - Arrival detection
*/
(function () {
  "use strict";

  var settingsNode = document.getElementById("map-settings");
  if (!settingsNode) return;
  var settings = JSON.parse(settingsNode.textContent || "{}");

  function sharedDirectionsUrl(destination, origin) {
    var build = window.TripuraExplore && window.TripuraExplore.buildGoogleMapsUrl;
    if (typeof build !== "function" || !destination) return null;
    return build(
      Number(destination.lat),
      Number(destination.lng),
      origin ? Number(origin.lat) : null,
      origin ? Number(origin.lng) : null
    );
  }

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

  /* ================================================================
     OSRM Routing Service (free, no API key required)
     Uses the public OSRM demo server for route calculation.
     ================================================================ */
  var OSRM_BASE = "https://router.project-osrm.org/route/v1/driving/";

  function fetchOSRMRoute(fromLat, fromLng, toLat, toLng, callback) {
    // OSRM expects longitude,latitude order
    var url = OSRM_BASE +
      fromLng.toFixed(6) + "," + fromLat.toFixed(6) + ";" +
      toLng.toFixed(6) + "," + toLat.toFixed(6) +
      "?overview=full&geometries=geojson&steps=true&annotations=distance,duration";

    fetch(url)
      .then(function (response) {
        if (!response.ok) throw new Error("OSRM request failed (" + response.status + ")");
        return response.json();
      })
      .then(function (data) {
        if (data.code !== "Ok" || !data.routes || !data.routes.length) {
          callback(new Error("No route found"), null);
          return;
        }
        var route = data.routes[0];
        var coords = route.geometry.coordinates.map(function (c) {
          // GeoJSON is [lng, lat] -> convert to [lat, lng] for Leaflet
          return [c[1], c[0]];
        });

        // Extract turn-by-turn steps
        var steps = [];
        if (route.legs) {
          route.legs.forEach(function (leg) {
            if (leg.steps) {
              leg.steps.forEach(function (step) {
                steps.push({
                  instruction: buildInstruction(step),
                  distance: step.distance,
                  duration: step.duration,
                  maneuver: step.maneuver,
                  name: step.name || "",
                  // step start location in [lat, lng]
                  location: [step.maneuver.location[1], step.maneuver.location[0]]
                });
              });
            }
          });
        }

        callback(null, {
          coordinates: coords,
          distance: route.distance,       // meters
          duration: route.duration,        // seconds
          steps: steps
        });
      })
      .catch(function (err) {
        callback(err, null);
      });
  }

  function buildInstruction(step) {
    var m = step.maneuver;
    var type = m.type || "";
    var modifier = m.modifier || "";
    var name = step.name || "";

    if (type === "depart") return "Head " + (modifier || "north") + (name ? " on " + name : "");
    if (type === "arrive") return "Arrive at your destination" + (name ? " (" + name + ")" : "");
    if (type === "turn") return "Turn " + modifier + (name ? " onto " + name : "");
    if (type === "new name") return "Continue onto " + name;
    if (type === "merge") return "Merge " + modifier + (name ? " onto " + name : "");
    if (type === "fork") return "Take the " + modifier + " fork" + (name ? " onto " + name : "");
    if (type === "roundabout" || type === "rotary") {
      var exit = m.exit ? " (exit " + m.exit + ")" : "";
      return "Enter roundabout" + exit + (name ? ", onto " + name : "");
    }
    if (type === "end of road") return "Turn " + modifier + (name ? " onto " + name : "");
    return (modifier ? modifier.charAt(0).toUpperCase() + modifier.slice(1) : "Continue") +
      (name ? " on " + name : "");
  }

  function getManeuverSvg(maneuver) {
    var type = (maneuver && maneuver.type) || "";
    var modifier = (maneuver && maneuver.modifier) || "";

    if (type === "arrive") {
      return '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/></svg>';
    }
    if (modifier.indexOf("left") !== -1) {
      return '<svg viewBox="0 0 24 24"><polyline points="14 15 9 15 9 5"/><polyline points="13 9 9 5 5 9"/></svg>';
    }
    if (modifier.indexOf("right") !== -1) {
      return '<svg viewBox="0 0 24 24"><polyline points="10 15 15 15 15 5"/><polyline points="11 9 15 5 19 9"/></svg>';
    }
    if (type === "roundabout" || type === "rotary") {
      return '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="5" fill="none"/><polyline points="12 7 12 2"/><polyline points="9 3 12 0 15 3"/></svg>';
    }
    // Default: straight arrow
    return '<svg viewBox="0 0 24 24"><polyline points="12 19 12 5"/><polyline points="5 12 12 5 19 12"/></svg>';
  }

  /* ================================================================
     CAR MARKER SVG
     Clean top-down vehicle icon for navigation
     ================================================================ */
  var CAR_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40">' +
    '<g transform="translate(20,20)">' +
    // Car body
    '<rect x="-8" y="-16" width="16" height="32" rx="5" ry="7" fill="#1d4ed8" stroke="#1e3a5f" stroke-width="1.2"/>' +
    // Windshield
    '<rect x="-6" y="-10" width="12" height="6" rx="2" fill="#93c5fd" opacity="0.8"/>' +
    // Rear window
    '<rect x="-5" y="7" width="10" height="4" rx="1.5" fill="#93c5fd" opacity="0.6"/>' +
    // Headlights
    '<circle cx="-5" cy="-15" r="1.5" fill="#fbbf24"/>' +
    '<circle cx="5" cy="-15" r="1.5" fill="#fbbf24"/>' +
    // Direction indicator (front point)
    '<polygon points="0,-19 -3,-15 3,-15" fill="#60a5fa"/>' +
    '</g></svg>';

  function makeCarIcon() {
    return L.divIcon({
      className: "nav-vehicle-icon",
      html: CAR_SVG,
      iconSize: [40, 40],
      iconAnchor: [20, 20]
    });
  }

  /* ================================================================
     UTILITY FUNCTIONS
     ================================================================ */
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

  function distanceMeters(lat1, lng1, lat2, lng2) {
    return calculateDistanceKm(lat1, lng1, lat2, lng2) * 1000;
  }

  function formatDistance(meters) {
    if (meters < 1000) return Math.round(meters) + " m";
    return (meters / 1000).toFixed(1) + " km";
  }

  function formatDuration(seconds) {
    if (seconds < 60) return "< 1 min";
    var mins = Math.round(seconds / 60);
    if (mins < 60) return mins + " min";
    var hrs = Math.floor(mins / 60);
    var rem = mins % 60;
    return hrs + " hr" + (rem > 0 ? " " + rem + " min" : "");
  }

  function bearing(lat1, lng1, lat2, lng2) {
    var dLng = ((lng2 - lng1) * Math.PI) / 180;
    var y = Math.sin(dLng) * Math.cos((lat2 * Math.PI) / 180);
    var x =
      Math.cos((lat1 * Math.PI) / 180) * Math.sin((lat2 * Math.PI) / 180) -
      Math.sin((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.cos(dLng);
    var brng = (Math.atan2(y, x) * 180) / Math.PI;
    return (brng + 360) % 360;
  }

  /** Find the nearest point on a polyline to a given point.
      Returns { index, point: [lat, lng], distance (meters), progress (0..1) } */
  function nearestPointOnRoute(routeCoords, lat, lng) {
    var best = { index: 0, point: routeCoords[0], distance: Infinity, progress: 0 };
    var totalDist = 0;
    var segDists = [];
    for (var i = 0; i < routeCoords.length - 1; i++) {
      var d = distanceMeters(routeCoords[i][0], routeCoords[i][1], routeCoords[i + 1][0], routeCoords[i + 1][1]);
      segDists.push(d);
      totalDist += d;
    }

    var cumDist = 0;
    for (var j = 0; j < routeCoords.length - 1; j++) {
      var snapped = snapToSegment(routeCoords[j], routeCoords[j + 1], [lat, lng]);
      var dist = distanceMeters(lat, lng, snapped.point[0], snapped.point[1]);
      if (dist < best.distance) {
        var segProgress = segDists[j] > 0 ? snapped.t : 0;
        best = {
          index: j,
          point: snapped.point,
          distance: dist,
          progress: totalDist > 0 ? (cumDist + segProgress * segDists[j]) / totalDist : 0
        };
      }
      cumDist += segDists[j];
    }
    // Also check the last point
    var lastDist = distanceMeters(lat, lng, routeCoords[routeCoords.length - 1][0], routeCoords[routeCoords.length - 1][1]);
    if (lastDist < best.distance) {
      best = {
        index: routeCoords.length - 1,
        point: routeCoords[routeCoords.length - 1],
        distance: lastDist,
        progress: 1
      };
    }

    return best;
  }

  function snapToSegment(a, b, p) {
    var dx = b[0] - a[0];
    var dy = b[1] - a[1];
    if (dx === 0 && dy === 0) return { point: a, t: 0 };
    var t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy);
    t = Math.max(0, Math.min(1, t));
    return {
      point: [a[0] + t * dx, a[1] + t * dy],
      t: t
    };
  }

  function isValidCoord(lat, lng) {
    return typeof lat === "number" && typeof lng === "number" &&
      !isNaN(lat) && !isNaN(lng) &&
      lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180;
  }

  function isInTripuraRegion(lat, lng) {
    // Broad check for Tripura + surrounding area
    return lat >= 22 && lat <= 25 && lng >= 91 && lng <= 93;
  }

  /* ================================================================
     NAVIGATION STATE
     ================================================================ */
  var NavState = {
    IDLE: "idle",
    LOCATING: "locating",
    ROUTE_PREVIEW: "route_preview",
    STARTING: "starting",
    NAVIGATING: "navigating",
    PAUSED: "paused",
    REROUTING: "rerouting",
    LOCATION_LOST: "location_lost",
    ARRIVED: "arrived",
    ERROR: "error"
  };

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
    var userCoords = null;          // { lat, lng, accuracy, heading, timestamp }
    var userMarker = null;
    var watchId = null;
    var routePolyline = null;
    var activePlace = null;
    var placeMarkers = {};
    var initialUrlParams = new URLSearchParams(window.location.search);
    var hasUrlTarget = !!(
      initialUrlParams.get("place_id") ||
      initialUrlParams.get("id") ||
      initialUrlParams.get("slug") ||
      initialUrlParams.get("place") ||
      initialUrlParams.get("name") ||
      initialUrlParams.get("destination") ||
      initialUrlParams.get("lat")
    );

    // Legacy sidebar buttons
    var locateBtn = document.getElementById("map-locate-me");
    var recenterBtn = document.getElementById("map-recenter-btn");
    var startJourneyBtn = document.getElementById("map-start-journey-btn");

    // Floating bar
    var floatingBar = document.getElementById("map-floating-bar");
    var floatingRecenterBtn = document.getElementById("floating-recenter-btn");
    var floatingJourneyBtn = document.getElementById("floating-journey-btn");

    // Legacy journey HUD
    var journeyHud = document.getElementById("journey-hud");
    var journeyDestSelect = document.getElementById("journey-destination-select");
    var journeyStats = document.getElementById("journey-stats");
    var journeyDistVal = document.getElementById("journey-distance-val");
    var journeyTimeVal = document.getElementById("journey-time-val");
    var journeyNavBtn = document.getElementById("journey-turn-by-turn-link");
    var journeyRecenterBtn = document.getElementById("journey-recenter-action");
    var journeyCloseBtn = document.getElementById("journey-close-btn");

    // Route preview panel
    var routePreviewPanel = document.getElementById("route-preview-panel");
    var routePreviewDestName = document.getElementById("route-preview-dest-name");
    var routePreviewDistance = document.getElementById("route-preview-distance");
    var routePreviewTime = document.getElementById("route-preview-time");
    var routePreviewStartBtn = document.getElementById("route-preview-start");
    var routePreviewGmaps = document.getElementById("route-preview-gmaps");
    var routePreviewCloseBtn = document.getElementById("route-preview-close");

    // Navigation HUD elements
    var navHud = document.getElementById("nav-hud");
    var navInstructionBar = document.getElementById("nav-instruction-bar");
    var navManeuverIcon = document.getElementById("nav-maneuver-icon");
    var navManeuverText = document.getElementById("nav-maneuver-text");
    var navManeuverDistance = document.getElementById("nav-maneuver-distance");
    var navGpsQuality = document.getElementById("nav-gps-quality");
    var navBottomBar = document.getElementById("nav-bottom-bar");
    var navRemainingDist = document.getElementById("nav-remaining-dist");
    var navEta = document.getElementById("nav-eta");
    var navDestName = document.getElementById("nav-dest-name");
    var navRecenterBtn = document.getElementById("nav-recenter-btn");
    var navPauseBtn = document.getElementById("nav-pause-btn");
    var navEndBtn = document.getElementById("nav-end-btn");
    var navStatusBar = document.getElementById("nav-status-bar");
    var navStatusText = document.getElementById("nav-status-text");
    var navArrivalOverlay = document.getElementById("nav-arrival-overlay");
    var navArrivalDest = document.getElementById("nav-arrival-dest");
    var navArrivalClose = document.getElementById("nav-arrival-close");
    var navArrivalNew = document.getElementById("nav-arrival-new");

    /* ================================================================
       NAVIGATION STATE MANAGER
       ================================================================ */
    var nav = {
      state: NavState.IDLE,
      destination: null,           // place object from currentPlaces
      routeCoords: null,           // [[lat, lng], ...]
      routeSteps: null,            // turn-by-turn steps from OSRM
      routeDistance: 0,            // total route distance in meters
      routeDuration: 0,            // total route duration in seconds
      currentStepIndex: 0,
      // GPS
      rawGps: null,                // { lat, lng, accuracy, heading, speed, timestamp }
      displayPosition: null,       // { lat, lng } - snapped/smoothed
      currentHeading: 0,
      // Vehicle
      carMarker: null,
      accuracyCircle: null,
      // Route display
      activeRouteLayer: null,
      remainingRouteLayer: null,
      travelledRouteLayer: null,
      destinationMarker: null,
      // Camera
      followMode: true,
      // Tracking
      navWatchId: null,
      animFrameId: null,
      lastAnimTime: 0,
      // Interpolation
      interpFrom: null,
      interpTo: null,
      interpStartTime: 0,
      interpDuration: 500,         // ms
      // Rerouting
      lastRerouteTime: 0,
      rerouteThrottleMs: 15000,    // min 15s between reroutes
      deviationCount: 0,
      deviationThreshold: 50,      // meters off route to trigger reroute
      // Arrival
      arrivalRadius: 60,           // meters
      arrivalCount: 0,
      arrivalRequired: 3,          // consecutive readings near dest
      // Progress
      routeProgress: 0,            // 0..1
      remainingDistance: 0,
      remainingDuration: 0,
      // Stale GPS
      staleThresholdMs: 15000,
      // GPS noise filter
      lastValidGps: null,
      minMovementMeters: 3
    };

    function setNavState(newState) {
      var oldState = nav.state;
      nav.state = newState;
      updateNavUI();
      if (window.TripuraExplore) {
        console.log("[Nav] " + oldState + " → " + newState);
      }
    }

    /* ================================================================
       UI UPDATE based on nav state
       ================================================================ */
    function updateNavUI() {
      var isNav = nav.state === NavState.NAVIGATING || nav.state === NavState.PAUSED ||
                  nav.state === NavState.REROUTING || nav.state === NavState.LOCATION_LOST;
      var isPreview = nav.state === NavState.ROUTE_PREVIEW;
      var isLocating = nav.state === NavState.LOCATING || nav.state === NavState.STARTING;

      // Navigation HUD visibility
      if (navHud) navHud.style.display = isNav ? "block" : "none";
      if (navBottomBar) navBottomBar.style.display = isNav ? "flex" : "none";

      // Route preview panel
      if (routePreviewPanel) routePreviewPanel.style.display = isPreview ? "block" : "none";

      // Legacy HUD - hide during active navigation (use new UI)
      if (journeyHud && isNav) journeyHud.style.display = "none";

      // Status bar
      if (navStatusBar) {
        if (isLocating) {
          navStatusBar.style.display = "flex";
          navStatusBar.className = "nav-status-bar";
          if (navStatusText) navStatusText.textContent = "Acquiring GPS…";
        } else if (nav.state === NavState.REROUTING) {
          navStatusBar.style.display = "flex";
          navStatusBar.className = "nav-status-bar nav-rerouting";
          if (navStatusText) navStatusText.textContent = "Rerouting…";
        } else if (nav.state === NavState.LOCATION_LOST) {
          navStatusBar.style.display = "flex";
          navStatusBar.className = "nav-status-bar nav-location-lost";
          if (navStatusText) navStatusText.textContent = "GPS signal lost";
        } else {
          navStatusBar.style.display = "none";
        }
      }

      // Arrival overlay
      if (navArrivalOverlay) {
        navArrivalOverlay.style.display = nav.state === NavState.ARRIVED ? "flex" : "none";
      }

      // Pause button text
      if (navPauseBtn) {
        if (nav.state === NavState.PAUSED) {
          navPauseBtn.textContent = "▶ Resume";
          navPauseBtn.className = "nav-ctrl-btn nav-ctrl-btn--resume";
          navPauseBtn.title = "Resume navigation";
          navPauseBtn.setAttribute("aria-label", "Resume navigation");
        } else {
          navPauseBtn.innerHTML = "⏸ Pause";
          navPauseBtn.className = "nav-ctrl-btn nav-ctrl-btn--pause";
          navPauseBtn.title = "Pause navigation";
          navPauseBtn.setAttribute("aria-label", "Pause navigation");
        }
      }

      // Floating bar: hide during active nav (bottom bar replaces it)
      if (floatingBar) {
        floatingBar.style.display = (isNav || isPreview) ? "none" : (userCoords ? "flex" : "none");
      }

      // Update GPS quality indicator
      if (navGpsQuality && nav.rawGps) {
        var acc = nav.rawGps.accuracy;
        if (acc <= 15) {
          navGpsQuality.className = "gps-quality gps-quality--good";
          navGpsQuality.textContent = "GPS ±" + Math.round(acc) + "m";
        } else if (acc <= 50) {
          navGpsQuality.className = "gps-quality gps-quality--fair";
          navGpsQuality.textContent = "GPS ±" + Math.round(acc) + "m";
        } else {
          navGpsQuality.className = "gps-quality gps-quality--poor";
          navGpsQuality.textContent = "GPS ±" + Math.round(acc) + "m";
        }
      }
    }

    /* ================================================================
       POPUP HTML (preserved from original)
       ================================================================ */
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
        '<a class="btn btn--sm btn--ghost" href="' + place.url + '">Details</a>' +
        '</div></div>'
      );
    }

    /* ================================================================
       RENDER PLACES (preserved from original, with minor fix)
       ================================================================ */
    function renderPlaces(places) {
      currentPlaces = places || [];
      layer.clearLayers();
      placeMarkers = {};
      results.innerHTML = "";
      var bounds = [];

      currentPlaces.forEach(function (place) {
        var marker = L.marker([place.lat, place.lng], { icon: makeIcon(false) });
        marker.bindPopup(popupHtml(place));
        marker.addTo(layer);
        bounds.push([place.lat, place.lng]);
        if (place.id != null) placeMarkers[String(place.id)] = marker;
        if (place.slug) placeMarkers[place.slug] = marker;

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

      if (bounds.length && !activePlace && !hasUrlTarget && nav.state === NavState.IDLE) {
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
          initiateJourney(pId);
        });
      }
    });

    /* ================================================================
       USER LOCATION - GPS TRACKING
       ================================================================ */
    function updateUserMarker(lat, lng, accuracy, heading, speed, timestamp) {
      if (!isValidCoord(lat, lng)) {
        console.warn("[GPS] Invalid coordinates rejected:", lat, lng);
        return;
      }

      // Filter GPS noise: reject readings that moved < minMovement and have poor accuracy
      if (nav.lastValidGps && accuracy > 30) {
        var moved = distanceMeters(nav.lastValidGps.lat, nav.lastValidGps.lng, lat, lng);
        if (moved < nav.minMovementMeters) {
          return; // Skip noisy micro-jumps
        }
      }

      var now = timestamp || Date.now();
      userCoords = { lat: lat, lng: lng, accuracy: accuracy, heading: heading, timestamp: now };
      nav.lastValidGps = { lat: lat, lng: lng, accuracy: accuracy, timestamp: now };

      if (window.TripuraExplore && window.TripuraExplore.setLiveLocationCache) {
        window.TripuraExplore.setLiveLocationCache(lat, lng, accuracy);
      }

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
      if (floatingBar && nav.state === NavState.IDLE) floatingBar.style.display = "flex";

      // During active navigation, feed position to navigation system
      if (nav.state === NavState.NAVIGATING || nav.state === NavState.REROUTING ||
          nav.state === NavState.LOCATION_LOST) {
        onNavigationGpsUpdate(lat, lng, accuracy, heading, speed, now);
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
          updateUserMarker(uLat, uLng, pos.coords.accuracy || 10, pos.coords.heading, pos.coords.speed, pos.timestamp);

          // Start continuous background watch for smooth real-time tracking
          startBackgroundWatch();

          if (onSuccess) onSuccess(userCoords);
        },
        function (err) {
          if (locateBtn) {
            locateBtn.disabled = false;
            locateBtn.innerHTML = 'Live Location';
          }
          if (window.TripuraExplore) {
            if (err.code === 1) {
              window.TripuraExplore.showToast("Location access denied. Please enable GPS permission in your browser settings.", "error");
            } else if (err.code === 2) {
              window.TripuraExplore.showToast("GPS position unavailable. Please ensure GPS is enabled.", "error");
            } else if (err.code === 3) {
              window.TripuraExplore.showToast("GPS timed out. Please try again in an open area.", "error");
            } else {
              window.TripuraExplore.showToast("Could not retrieve live GPS position: " + err.message, "error");
            }
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

    function startBackgroundWatch() {
      if (watchId !== null) return; // prevent multiple watchers
      if (!navigator.geolocation || !navigator.geolocation.watchPosition) return;

      watchId = navigator.geolocation.watchPosition(
        function (wPos) {
          updateUserMarker(
            wPos.coords.latitude,
            wPos.coords.longitude,
            wPos.coords.accuracy || 10,
            wPos.coords.heading,
            wPos.coords.speed,
            wPos.timestamp
          );
        },
        function (wErr) {
          console.warn("[GPS] watch position notice:", wErr.message);
          if (nav.state === NavState.NAVIGATING && wErr.code !== 1) {
            setNavState(NavState.LOCATION_LOST);
          }
        },
        { enableHighAccuracy: true, maximumAge: 3000, timeout: 15000 }
      );
    }

    function stopBackgroundWatch() {
      if (watchId !== null) {
        navigator.geolocation.clearWatch(watchId);
        watchId = null;
      }
    }

    /* ================================================================
       NAVIGATION GPS UPDATE HANDLER
       Called each time a new GPS reading arrives during navigation
       ================================================================ */
    function onNavigationGpsUpdate(lat, lng, accuracy, heading, speed, timestamp) {
      nav.rawGps = { lat: lat, lng: lng, accuracy: accuracy, heading: heading, speed: speed, timestamp: timestamp };

      // Detect stale GPS
      if (Date.now() - timestamp > nav.staleThresholdMs) {
        return; // Skip stale readings
      }

      // If location was lost, restore to navigating
      if (nav.state === NavState.LOCATION_LOST) {
        setNavState(NavState.NAVIGATING);
      }

      // Snap to route
      var snapped = null;
      if (nav.routeCoords && nav.routeCoords.length > 1) {
        var nearest = nearestPointOnRoute(nav.routeCoords, lat, lng);

        // Check for route deviation
        var deviationMeters = nearest.distance;
        var effectiveThreshold = Math.max(nav.deviationThreshold, accuracy * 1.5);

        if (deviationMeters > effectiveThreshold) {
          nav.deviationCount++;
          if (nav.deviationCount >= 3) {
            // Consistent deviation - trigger reroute
            triggerReroute(lat, lng);
            nav.deviationCount = 0;
          }
          // Use raw GPS position when off route
          snapped = { lat: lat, lng: lng };
        } else {
          nav.deviationCount = 0;
          snapped = { lat: nearest.point[0], lng: nearest.point[1] };
          nav.routeProgress = nearest.progress;

          // Update remaining distance/duration
          nav.remainingDistance = nav.routeDistance * (1 - nav.routeProgress);
          nav.remainingDuration = nav.routeDuration * (1 - nav.routeProgress);

          // Update current step
          updateCurrentStep(nearest);

          // Draw travelled/remaining route
          updateRouteProgress(nearest.index);
        }
      } else {
        snapped = { lat: lat, lng: lng };
      }

      // Calculate heading
      var newHeading = nav.currentHeading;
      if (heading !== null && heading !== undefined && !isNaN(heading) && speed > 1) {
        newHeading = heading;
      } else if (nav.displayPosition) {
        var moved = distanceMeters(nav.displayPosition.lat, nav.displayPosition.lng, snapped.lat, snapped.lng);
        if (moved > 5) {
          newHeading = bearing(nav.displayPosition.lat, nav.displayPosition.lng, snapped.lat, snapped.lng);
        }
      }
      nav.currentHeading = newHeading;

      // Set up interpolation for smooth movement
      nav.interpFrom = nav.displayPosition || snapped;
      nav.interpTo = snapped;
      nav.interpStartTime = performance.now();

      // Start animation if not running
      if (!nav.animFrameId) {
        nav.animFrameId = requestAnimationFrame(animateVehicle);
      }

      // Update HUD stats
      updateNavigationHUD();

      // Check arrival
      checkArrival(lat, lng, accuracy);
    }

    /* ================================================================
       VEHICLE ANIMATION
       Smoothly interpolates the car marker between GPS positions
       ================================================================ */
    function animateVehicle(timestamp) {
      if (nav.state !== NavState.NAVIGATING && nav.state !== NavState.REROUTING &&
          nav.state !== NavState.LOCATION_LOST) {
        nav.animFrameId = null;
        return;
      }

      if (nav.interpFrom && nav.interpTo && nav.carMarker) {
        var elapsed = timestamp - nav.interpStartTime;
        var t = Math.min(1, elapsed / nav.interpDuration);
        // Ease-out cubic
        t = 1 - Math.pow(1 - t, 3);

        var interpLat = nav.interpFrom.lat + (nav.interpTo.lat - nav.interpFrom.lat) * t;
        var interpLng = nav.interpFrom.lng + (nav.interpTo.lng - nav.interpFrom.lng) * t;

        nav.carMarker.setLatLng([interpLat, interpLng]);
        nav.displayPosition = { lat: interpLat, lng: interpLng };

        // Rotate car marker
        var el = nav.carMarker.getElement();
        if (el) {
          // Leaflet markers point up by default. Our SVG car points up (north).
          // Rotate by heading degrees clockwise from north.
          el.style.transform = el.style.transform.replace(/rotate\([^)]*\)/, "") +
            " rotate(" + nav.currentHeading + "deg)";
          el.style.transformOrigin = "center center";
        }

        // Update accuracy circle
        if (nav.accuracyCircle && nav.rawGps) {
          nav.accuracyCircle.setLatLng([interpLat, interpLng]);
          nav.accuracyCircle.setRadius(nav.rawGps.accuracy);
        }

        // Follow-me camera
        if (nav.followMode && t >= 0.5) {
          map.setView([interpLat, interpLng], map.getZoom(), { animate: true, duration: 0.5 });
        }
      }

      if (nav.interpFrom && nav.interpTo) {
        var done = (performance.now() - nav.interpStartTime) >= nav.interpDuration;
        if (done) {
          nav.displayPosition = nav.interpTo;
          nav.animFrameId = null;
        } else {
          nav.animFrameId = requestAnimationFrame(animateVehicle);
        }
      } else {
        nav.animFrameId = null;
      }
    }

    /* ================================================================
       UPDATE CURRENT TURN-BY-TURN STEP
       ================================================================ */
    function updateCurrentStep(nearest) {
      if (!nav.routeSteps || !nav.routeSteps.length) return;

      // Find the current step based on route progress
      var idx = nav.currentStepIndex;
      while (idx < nav.routeSteps.length - 1) {
        var stepLoc = nav.routeSteps[idx + 1].location;
        var distToNext = distanceMeters(
          nearest.point[0], nearest.point[1],
          stepLoc[0], stepLoc[1]
        );
        if (distToNext < 30) {
          // We've passed this step, advance
          idx++;
        } else {
          break;
        }
      }
      nav.currentStepIndex = idx;
    }

    /* ================================================================
       UPDATE ROUTE PROGRESS VISUAL
       Shows travelled portion in grey, remaining in green
       ================================================================ */
    function updateRouteProgress(segIndex) {
      if (!nav.routeCoords || nav.routeCoords.length < 2) return;

      // Remove old layers
      if (nav.travelledRouteLayer) map.removeLayer(nav.travelledRouteLayer);
      if (nav.remainingRouteLayer) map.removeLayer(nav.remainingRouteLayer);

      var travelled = nav.routeCoords.slice(0, segIndex + 2);
      var remaining = nav.routeCoords.slice(segIndex + 1);

      if (travelled.length >= 2) {
        nav.travelledRouteLayer = L.polyline(travelled, {
          color: "#94a3b8",
          weight: 5,
          opacity: 0.5
        }).addTo(map);
      }

      if (remaining.length >= 2) {
        nav.remainingRouteLayer = L.polyline(remaining, {
          color: "#1d4ed8",
          weight: 6,
          opacity: 0.9
        }).addTo(map);
      }
    }

    /* ================================================================
       UPDATE NAVIGATION HUD
       ================================================================ */
    function updateNavigationHUD() {
      // Remaining distance
      if (navRemainingDist) {
        navRemainingDist.textContent = formatDistance(nav.remainingDistance);
      }

      // ETA
      if (navEta) {
        navEta.textContent = nav.remainingDuration == null ? "Unavailable" : formatDuration(nav.remainingDuration);
      }

      // Destination name
      if (navDestName && nav.destination) {
        var dname = nav.destination.name;
        navDestName.textContent = dname.length > 16 ? dname.slice(0, 14) + "…" : dname;
      }

      // Current instruction
      if (nav.routeSteps && nav.routeSteps.length > 0) {
        var step = nav.routeSteps[Math.min(nav.currentStepIndex, nav.routeSteps.length - 1)];
        if (navManeuverText) navManeuverText.textContent = step.instruction;
        if (navManeuverIcon) navManeuverIcon.innerHTML = getManeuverSvg(step.maneuver);

        // Distance to next maneuver
        if (navManeuverDistance && nav.displayPosition && nav.currentStepIndex < nav.routeSteps.length - 1) {
          var nextStep = nav.routeSteps[nav.currentStepIndex + 1];
          var distToManeuver = distanceMeters(
            nav.displayPosition.lat, nav.displayPosition.lng,
            nextStep.location[0], nextStep.location[1]
          );
          navManeuverDistance.textContent = "In " + formatDistance(distToManeuver);
        } else if (navManeuverDistance) {
          navManeuverDistance.textContent = "";
        }
      }

      // GPS quality
      updateNavUI();
    }

    /* ================================================================
       CHECK ARRIVAL
       ================================================================ */
    function checkArrival(lat, lng, accuracy) {
      if (!nav.destination) return;

      var distToDest = distanceMeters(lat, lng, nav.destination.lat, nav.destination.lng);
      var effectiveRadius = Math.max(nav.arrivalRadius, accuracy);

      if (distToDest <= effectiveRadius) {
        nav.arrivalCount++;
        if (nav.arrivalCount >= nav.arrivalRequired) {
          handleArrival();
        }
      } else {
        nav.arrivalCount = 0;
      }
    }

    function handleArrival() {
      setNavState(NavState.ARRIVED);
      if (navArrivalDest && nav.destination) {
        navArrivalDest.textContent = nav.destination.name;
      }
      if (window.TripuraExplore) {
        window.TripuraExplore.showToast("🎉 You've arrived at " + nav.destination.name + "!", "success");
      }
    }

    /* ================================================================
       REROUTING
       ================================================================ */
    function triggerReroute(lat, lng) {
      var now = Date.now();
      if (now - nav.lastRerouteTime < nav.rerouteThrottleMs) return;
      if (nav.state === NavState.REROUTING) return;
      if (!nav.destination) return;

      nav.lastRerouteTime = now;
      setNavState(NavState.REROUTING);

      if (window.TripuraExplore) {
        window.TripuraExplore.showToast("You appear to be off route. Recalculating…", "info");
      }

      fetchOSRMRoute(lat, lng, nav.destination.lat, nav.destination.lng, function (err, result) {
        if (nav.state !== NavState.REROUTING) return; // navigation ended while rerouting

        if (err || !result) {
          console.warn("[Nav] Reroute failed:", err);
          setNavState(NavState.NAVIGATING); // continue with old route
          return;
        }

        // Replace route
        clearRouteDisplay();
        nav.routeCoords = result.coordinates;
        nav.routeDistance = result.distance;
        nav.routeDuration = result.duration;
        nav.routeSteps = result.steps;
        nav.currentStepIndex = 0;
        nav.routeProgress = 0;
        nav.remainingDistance = result.distance;
        nav.remainingDuration = result.duration;

        // Draw new route
        nav.activeRouteLayer = L.polyline(nav.routeCoords, {
          color: "#1d4ed8",
          weight: 6,
          opacity: 0.9
        }).addTo(map);

        setNavState(NavState.NAVIGATING);
      });
    }

    /* ================================================================
       ROUTE DISPLAY HELPERS
       ================================================================ */
    function clearRouteDisplay() {
      if (nav.activeRouteLayer) { map.removeLayer(nav.activeRouteLayer); nav.activeRouteLayer = null; }
      if (nav.remainingRouteLayer) { map.removeLayer(nav.remainingRouteLayer); nav.remainingRouteLayer = null; }
      if (nav.travelledRouteLayer) { map.removeLayer(nav.travelledRouteLayer); nav.travelledRouteLayer = null; }
      if (routePolyline) { map.removeLayer(routePolyline); routePolyline = null; }
    }

    /* ================================================================
       INITIATE JOURNEY (NEW FLOW)
       Step 1: Locate user
       Step 2: Show route preview with OSRM route
       Step 3: User clicks Start Navigation
       ================================================================ */
    function initiateJourney(targetIdOrSlug) {
      // Find the destination
      var chosen = null;
      if (typeof targetIdOrSlug === "object" && targetIdOrSlug !== null && targetIdOrSlug.lat != null) {
        chosen = targetIdOrSlug;
      } else if (targetIdOrSlug) {
        chosen = currentPlaces.find(function (p) {
          return String(p.id) === String(targetIdOrSlug) || p.slug === targetIdOrSlug;
        });
      }
      if (!chosen) {
        if (window.TripuraExplore) window.TripuraExplore.showToast("Destination not found.", "error");
        return;
      }

      nav.destination = chosen;

      // Validate destination coordinates
      if (!isValidCoord(chosen.lat, chosen.lng)) {
        if (window.TripuraExplore) window.TripuraExplore.showToast("This destination has invalid coordinates.", "error");
        return;
      }

      // Step 1: Get user location
      if (!userCoords) {
        setNavState(NavState.LOCATING);
        acquireLocation(function () {
          showRoutePreview(chosen);
        }, function () {
          setNavState(NavState.IDLE);
          if (window.TripuraExplore) {
            window.TripuraExplore.showToast("Select a starting point on the map to preview this route.", "info");
          }
          map.once("click", function (event) {
            if (!nav.destination || String(nav.destination.id) !== String(chosen.id)) return;
            userCoords = {
              lat: event.latlng.lat, lng: event.latlng.lng,
              accuracy: 0, heading: null, timestamp: Date.now(), manual: true
            };
            L.marker([userCoords.lat, userCoords.lng])
              .addTo(map).bindPopup("Selected route starting point").openPopup();
            showRoutePreview(chosen);
          });
        });
        return;
      }

      showRoutePreview(chosen);
    }

    /* ================================================================
       SHOW ROUTE PREVIEW
       Fetches OSRM route and shows preview panel
       ================================================================ */
    function showRoutePreview(place) {
      if (!userCoords) return;
      setNavState(NavState.ROUTE_PREVIEW);
      activePlace = place;

      // Show loading
      if (routePreviewDestName) routePreviewDestName.textContent = "Loading route to " + place.name + "…";
      if (routePreviewDistance) routePreviewDistance.textContent = "…";
      if (routePreviewTime) routePreviewTime.textContent = "…";
      if (routePreviewStartBtn) routePreviewStartBtn.disabled = true;

      // Fetch real route from OSRM
      fetchOSRMRoute(userCoords.lat, userCoords.lng, place.lat, place.lng, function (err, result) {
        if (nav.state !== NavState.ROUTE_PREVIEW) return; // user cancelled

        if (err || !result) {
          console.warn("[Route] OSRM route failed, falling back to straight line:", err);
          // Fallback: show straight-line preview
          showStraightLinePreview(place);
          return;
        }

        // Store route data
        nav.routeCoords = result.coordinates;
        nav.routeDistance = result.distance;
        nav.routeDuration = result.duration;
        nav.routeSteps = result.steps;
        nav.remainingDistance = result.distance;
        nav.remainingDuration = result.duration;

        // Draw the route
        clearRouteDisplay();
        nav.activeRouteLayer = L.polyline(result.coordinates, {
          color: "#1d4ed8",
          weight: 6,
          opacity: 0.85
        }).addTo(map);

        // Add destination marker
        if (nav.destinationMarker) map.removeLayer(nav.destinationMarker);
        nav.destinationMarker = L.marker([place.lat, place.lng], {
          icon: L.divIcon({
            className: "",
            html: '<div style="background:#dc2626;width:14px;height:14px;border-radius:50%;border:3px solid #ffffff;box-shadow:0 0 8px rgba(220,38,38,0.5);"></div>',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
          }),
          zIndexOffset: 900
        }).addTo(map);
        nav.destinationMarker.bindPopup("<strong>" + place.name + "</strong><br><em>Destination</em>");

        // Fit view
        map.fitBounds([
          [userCoords.lat, userCoords.lng],
          [place.lat, place.lng]
        ], { padding: [70, 70], maxZoom: 14 });

        // Update preview panel
        if (routePreviewDestName) routePreviewDestName.textContent = place.name;
        if (routePreviewDistance) routePreviewDistance.textContent = formatDistance(result.distance);
        if (routePreviewTime) routePreviewTime.textContent = formatDuration(result.duration);
        if (routePreviewStartBtn) routePreviewStartBtn.disabled = false;

        // Google Maps link
        if (routePreviewGmaps) {
          routePreviewGmaps.href = sharedDirectionsUrl(place, userCoords) || "#";
        }

        // Also update legacy HUD if visible
        updateLegacyHUD(place, result.distance, result.duration);
      });
    }

    function showStraightLinePreview(place) {
      clearRouteDisplay();

      routePolyline = L.polyline(
        [[userCoords.lat, userCoords.lng], [place.lat, place.lng]],
        { color: "#059669", weight: 5, opacity: 0.9, dashArray: "8, 8" }
      ).addTo(map);

      var dist = calculateDistanceKm(userCoords.lat, userCoords.lng, place.lat, place.lng);
      var distMeters = dist * 1000;

      // Keep this as a visual straight-line preview only. It is not a routable path.
      nav.routeCoords = [];
      nav.routeDistance = distMeters;
      nav.routeDuration = null;
      nav.routeSteps = [];
      nav.remainingDistance = distMeters;
      nav.remainingDuration = null;

      map.fitBounds(
        [[userCoords.lat, userCoords.lng], [place.lat, place.lng]],
        { padding: [70, 70], maxZoom: 14 }
      );

      if (routePreviewDestName) routePreviewDestName.textContent = place.name + " (straight line)";
      if (routePreviewDistance) routePreviewDistance.textContent = dist.toFixed(1) + " km (approx)";
      if (routePreviewTime) routePreviewTime.textContent = "Unavailable — route service did not return a route";
      if (routePreviewStartBtn) routePreviewStartBtn.disabled = true;

      if (routePreviewGmaps) {
        routePreviewGmaps.href = sharedDirectionsUrl(place, userCoords) || "#";
      }

      updateLegacyHUD(place, distMeters, null);
    }

    function updateLegacyHUD(place, distMeters, duration) {
      if (journeyStats) journeyStats.style.display = "grid";
      if (journeyDistVal) journeyDistVal.textContent = formatDistance(distMeters);
      if (journeyTimeVal) journeyTimeVal.textContent = duration == null ? "Unavailable" : formatDuration(duration);
      if (journeyNavBtn && userCoords) {
        journeyNavBtn.href = sharedDirectionsUrl(place, userCoords) || "#";
      }
    }

    /* ================================================================
       START NAVIGATION (after preview)
       ================================================================ */
    function startNavigation() {
      if (!userCoords || !nav.destination) return;
      if (!nav.routeCoords || nav.routeCoords.length < 2) {
        if (window.TripuraExplore) window.TripuraExplore.showToast("No valid route available. Try again.", "error");
        return;
      }

      setNavState(NavState.STARTING);

      // Reset navigation state
      nav.currentStepIndex = 0;
      nav.routeProgress = 0;
      nav.deviationCount = 0;
      nav.arrivalCount = 0;
      nav.followMode = true;

      // Create car marker at current position
      if (nav.carMarker) map.removeLayer(nav.carMarker);
      nav.carMarker = L.marker([userCoords.lat, userCoords.lng], {
        icon: makeCarIcon(),
        zIndexOffset: 2000,
        interactive: false
      }).addTo(map);
      nav.displayPosition = { lat: userCoords.lat, lng: userCoords.lng };

      // Create accuracy circle
      if (nav.accuracyCircle) map.removeLayer(nav.accuracyCircle);
      nav.accuracyCircle = L.circle([userCoords.lat, userCoords.lng], {
        radius: userCoords.accuracy || 10,
        className: "nav-accuracy-circle",
        interactive: false
      }).addTo(map);

      // Hide user blue dot during navigation (car replaces it)
      if (userMarker) userMarker.setOpacity(0);

      // Ensure GPS tracking is active
      startBackgroundWatch();

      // Set navigation zoom and center
      map.setView([userCoords.lat, userCoords.lng], 17, { animate: true });

      // Handle user manual map interaction - disable follow mode
      map.on("dragstart", onUserMapInteraction);
      map.on("zoomstart", onUserZoomInteraction);

      setNavState(NavState.NAVIGATING);

      if (window.TripuraExplore) {
        window.TripuraExplore.showToast("Navigation started to " + nav.destination.name + "!", "success");
      }
    }

    var _userInitiatedZoom = false;
    function onUserMapInteraction() {
      nav.followMode = false;
    }
    function onUserZoomInteraction() {
      // Only disable follow on user-initiated zoom (not programmatic)
      // We use a flag to distinguish
      if (!_userInitiatedZoom) return;
      nav.followMode = false;
    }

    /* ================================================================
       PAUSE / RESUME / END NAVIGATION
       ================================================================ */
    function pauseNavigation() {
      if (nav.state !== NavState.NAVIGATING) return;
      setNavState(NavState.PAUSED);
      nav.followMode = false;
      if (window.TripuraExplore) window.TripuraExplore.showToast("Navigation paused.", "info");
    }

    function resumeNavigation() {
      if (nav.state !== NavState.PAUSED) return;

      if (!userCoords) {
        setNavState(NavState.LOCATING);
        acquireLocation(function () {
          nav.followMode = true;
          setNavState(NavState.NAVIGATING);

          // Check if we need to reroute (may have moved while paused)
          if (nav.routeCoords) {
            var nearest = nearestPointOnRoute(nav.routeCoords, userCoords.lat, userCoords.lng);
            if (nearest.distance > nav.deviationThreshold * 2) {
              triggerReroute(userCoords.lat, userCoords.lng);
            }
          }
        }, function () {
          setNavState(NavState.PAUSED);
        });
        return;
      }

      nav.followMode = true;
      setNavState(NavState.NAVIGATING);
      map.setView([userCoords.lat, userCoords.lng], 17, { animate: true });
    }

    function endNavigation() {
      // Clean up navigation layers
      clearRouteDisplay();
      if (nav.carMarker) { map.removeLayer(nav.carMarker); nav.carMarker = null; }
      if (nav.accuracyCircle) { map.removeLayer(nav.accuracyCircle); nav.accuracyCircle = null; }
      if (nav.destinationMarker) { map.removeLayer(nav.destinationMarker); nav.destinationMarker = null; }

      // Cancel animation
      if (nav.animFrameId) { cancelAnimationFrame(nav.animFrameId); nav.animFrameId = null; }

      // Remove map interaction listeners
      map.off("dragstart", onUserMapInteraction);
      map.off("zoomstart", onUserZoomInteraction);

      // Show user marker again
      if (userMarker) userMarker.setOpacity(1);

      // Reset nav state
      nav.destination = null;
      nav.routeCoords = null;
      nav.routeSteps = null;
      nav.routeDistance = 0;
      nav.routeDuration = 0;
      nav.currentStepIndex = 0;
      nav.displayPosition = null;
      nav.interpFrom = null;
      nav.interpTo = null;
      nav.routeProgress = 0;
      nav.remainingDistance = 0;
      nav.remainingDuration = 0;
      nav.deviationCount = 0;
      nav.arrivalCount = 0;
      nav.followMode = false;
      activePlace = null;

      // Hide all navigation UI
      setNavState(NavState.IDLE);

      // Hide legacy HUD
      if (journeyHud) journeyHud.style.display = "none";
      if (routePreviewPanel) routePreviewPanel.style.display = "none";

      // Reset start journey button
      if (startJourneyBtn) startJourneyBtn.innerHTML = 'Start Journey';

      // Restore map to browsing state
      if (userCoords) {
        map.setView([userCoords.lat, userCoords.lng], 13, { animate: true });
      } else {
        map.setView(settings.center, settings.zoom, { animate: true });
      }

      if (window.TripuraExplore) window.TripuraExplore.showToast("Navigation ended.", "info");
    }

    function recenterNavigation() {
      if (nav.state === NavState.NAVIGATING || nav.state === NavState.PAUSED) {
        nav.followMode = true;
        if (nav.displayPosition) {
          map.setView([nav.displayPosition.lat, nav.displayPosition.lng], 17, { animate: true });
        } else if (userCoords) {
          map.setView([userCoords.lat, userCoords.lng], 17, { animate: true });
        }
        if (window.TripuraExplore) window.TripuraExplore.showToast("Map recentered.", "success");
      }
    }

    /* ================================================================
       LEGACY JOURNEY FUNCTIONS (preserved for backward compat)
       ================================================================ */
    function recenterMap() {
      if (nav.state === NavState.NAVIGATING || nav.state === NavState.PAUSED) {
        recenterNavigation();
        return;
      }

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
      initiateJourney(place.id || place.slug);
    }

    function startJourney(targetIdOrSlug) {
      if (!userCoords) {
        if (window.TripuraExplore) window.TripuraExplore.showToast("Acquiring your live GPS position to start journey…", "info");
        acquireLocation(function () {
          startJourney(targetIdOrSlug);
        });
        return;
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

      if (!chosen) {
        // Show journey HUD to let user pick a destination
        if (journeyHud) journeyHud.style.display = "block";
        populateDestinationOptions(null);
        if (window.TripuraExplore) window.TripuraExplore.showToast("Select a destination to start your journey.", "info");
        return;
      }

      initiateJourney(chosen.id || chosen.slug);

      if (startJourneyBtn) {
        startJourneyBtn.innerHTML = '● Trip to ' + (chosen.name.length > 14 ? chosen.name.slice(0, 12) + '…' : chosen.name);
      }
    }

    function endJourney() {
      if (nav.state !== NavState.IDLE) {
        endNavigation();
        return;
      }

      // Legacy cleanup
      if (routePolyline) {
        map.removeLayer(routePolyline);
        routePolyline = null;
      }
      activePlace = null;
      if (journeyHud) journeyHud.style.display = "none";
      if (routePreviewPanel) routePreviewPanel.style.display = "none";
      if (startJourneyBtn) startJourneyBtn.innerHTML = 'Start Journey';
      if (window.TripuraExplore) window.TripuraExplore.showToast("Journey ended.", "info");
    }

    /* ================================================================
       EVENT LISTENERS
       ================================================================ */

    // Locate me button
    if (locateBtn) {
      locateBtn.addEventListener("click", function () {
        acquireLocation(function (coords) {
          map.setView([coords.lat, coords.lng], 13);
          if (userMarker) userMarker.openPopup();
          if (window.TripuraExplore) window.TripuraExplore.showToast("Located your live position via GPS.", "success");
        });
      });
    }

    // Recenter buttons
    if (recenterBtn) recenterBtn.addEventListener("click", recenterMap);
    if (floatingRecenterBtn) floatingRecenterBtn.addEventListener("click", recenterMap);
    if (journeyRecenterBtn) journeyRecenterBtn.addEventListener("click", recenterMap);

    // Start journey buttons
    if (startJourneyBtn) {
      startJourneyBtn.addEventListener("click", function () {
        if (nav.state !== NavState.IDLE) {
          recenterNavigation();
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

    // Legacy journey HUD controls
    if (journeyCloseBtn) journeyCloseBtn.addEventListener("click", endJourney);

    if (journeyDestSelect) {
      journeyDestSelect.addEventListener("change", function () {
        var val = journeyDestSelect.value;
        if (!val) return;
        var found = currentPlaces.find(function (p) {
          return String(p.id) === String(val) || p.slug === val;
        });
        if (found) {
          initiateJourney(found.id || found.slug);
          if (startJourneyBtn) {
            startJourneyBtn.innerHTML = '● Trip to ' + (found.name.length > 14 ? found.name.slice(0, 12) + '…' : found.name);
          }
        }
      });
    }

    // Route preview controls
    if (routePreviewStartBtn) {
      routePreviewStartBtn.addEventListener("click", function () {
        startNavigation();
      });
    }

    if (routePreviewCloseBtn) {
      routePreviewCloseBtn.addEventListener("click", function () {
        clearRouteDisplay();
        if (nav.destinationMarker) { map.removeLayer(nav.destinationMarker); nav.destinationMarker = null; }
        nav.destination = null;
        nav.routeCoords = null;
        nav.routeSteps = null;
        activePlace = null;
        setNavState(NavState.IDLE);
        if (startJourneyBtn) startJourneyBtn.innerHTML = 'Start Journey';
      });
    }

    // Navigation controls
    if (navPauseBtn) {
      navPauseBtn.addEventListener("click", function () {
        if (nav.state === NavState.PAUSED) {
          resumeNavigation();
        } else {
          pauseNavigation();
        }
      });
    }

    if (navEndBtn) {
      navEndBtn.addEventListener("click", function () {
        endNavigation();
      });
    }

    if (navRecenterBtn) {
      navRecenterBtn.addEventListener("click", function () {
        recenterNavigation();
      });
    }

    // Arrival overlay controls
    if (navArrivalClose) {
      navArrivalClose.addEventListener("click", function () {
        endNavigation();
      });
    }

    if (navArrivalNew) {
      navArrivalNew.addEventListener("click", function () {
        endNavigation();
        // Show journey starter
        if (journeyHud) journeyHud.style.display = "block";
        populateDestinationOptions(null);
      });
    }

    function handleUrlDestination(places) {
      var urlParams = new URLSearchParams(window.location.search);
      var targetId = urlParams.get("place_id") || urlParams.get("id");
      var providerId = urlParams.get("osm_id");
      var providerType = urlParams.get("osm_type");
      var targetSlug = urlParams.get("slug") || urlParams.get("place");
      var targetName = urlParams.get("name") || urlParams.get("title");
      var targetDest = urlParams.get("destination");
      var targetLat = parseFloat(urlParams.get("lat") || urlParams.get("latitude"));
      var targetLng = parseFloat(urlParams.get("lng") || urlParams.get("longitude"));

      if ((isNaN(targetLat) || isNaN(targetLng)) && targetDest && targetDest.indexOf(",") !== -1) {
        var dParts = targetDest.split(",");
        targetLat = parseFloat(dParts[0]);
        targetLng = parseFloat(dParts[1]);
      }

      var wantDirections = urlParams.get("directions") === "1" || urlParams.get("route") === "1";

      if (!targetId && !targetSlug && !targetName && isNaN(targetLat) && isNaN(targetLng)) {
        return;
      }

      var matchedPlace = null;
      // OSM search results are separate from the published destination
      // directory. Never match their numeric provider ID against a local DB
      // ID, or snap their coordinates to a nearby destination marker.
      if (places && places.length && !providerId) {
        matchedPlace = places.find(function (p) {
          if (targetId && String(p.id) === String(targetId)) return true;
          if (targetSlug && p.slug === targetSlug) return true;
          if (!isNaN(targetLat) && !isNaN(targetLng) && Math.abs(p.lat - targetLat) < 0.0005 && Math.abs(p.lng - targetLng) < 0.0005) return true;
          return false;
        });
      }

      if ((isNaN(targetLat) || isNaN(targetLng)) && matchedPlace && isValidCoord(matchedPlace.lat, matchedPlace.lng)) {
        targetLat = matchedPlace.lat;
        targetLng = matchedPlace.lng;
      }

      if (isNaN(targetLat) || isNaN(targetLng) || !isValidCoord(targetLat, targetLng)) {
        if (window.TripuraExplore && window.TripuraExplore.showToast) {
          var dispName = targetName || (matchedPlace ? matchedPlace.name : "Destination");
          window.TripuraExplore.showToast("Coordinates for " + dispName + " are unavailable or pending verification.", "info");
        }
        return;
      }

      var destName = targetName || (matchedPlace ? matchedPlace.name : "Selected Destination");

      // Requirement 4: Center the map on the selected destination
      map.setView([targetLat, targetLng], 14);

      // Requirement 5: Display a marker for the selected place and open popup
      var targetMarker = null;
      if (matchedPlace) {
        targetMarker = placeMarkers[String(matchedPlace.id)] || placeMarkers[matchedPlace.slug];
      }
      if (!targetMarker) {
        var customObj = matchedPlace || {
          id: providerId && providerType ? providerType + "/" + providerId : (targetId || null),
          osm_type: providerType || null,
          osm_id: providerId || null,
          slug: targetSlug || "",
          name: destName,
          lat: targetLat,
          lng: targetLng,
          category: "",
          district: ""
        };
        targetMarker = L.marker([targetLat, targetLng], { icon: makeIcon(true) }).addTo(layer);
        targetMarker.bindPopup(popupHtml(customObj));
        matchedPlace = customObj;
      }

      if (targetMarker) {
        targetMarker.openPopup();
      }

      if (results && matchedPlace) {
        var items = results.querySelectorAll(".map-result");
        items.forEach(function (btn) {
          if (btn.textContent.indexOf(matchedPlace.name) !== -1) {
            btn.classList.add("is-selected");
            btn.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }
        });
      }

      var destToRoute = matchedPlace || {
        id: targetId || "dest",
        slug: targetSlug || "dest",
        name: destName,
        lat: targetLat,
        lng: targetLng
      };
      activePlace = destToRoute;

      // Requirement 5: Provide a way to start or display a route from user location
      if (wantDirections) {
        initiateJourney(destToRoute);
      } else if (typeof populateDestinationOptions === "function") {
        populateDestinationOptions(destToRoute.id || destToRoute.slug);
      }
    }

    window.TripuraMap = {
      selectDestination: function (targetIdOrSlug, lat, lng, name, wantRoute) {
        if (isValidCoord(lat, lng)) {
          map.setView([lat, lng], 14);
          var m = placeMarkers[String(targetIdOrSlug)];
          if (m) m.openPopup();
          if (wantRoute) {
            initiateJourney(targetIdOrSlug);
          }
        }
      }
    };

    /* ================================================================
       LOAD DESTINATIONS (preserved from original)
       ================================================================ */
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
          if (hasUrlTarget) {
            handleUrlDestination(data.places);
            hasUrlTarget = false;
          }
        })
        .catch(function (error) {
          status.textContent = "Could not load the map data.";
          messageBox.innerHTML = '<div class="alert alert--error">' + error.message + "</div>";
          if (hasUrlTarget) {
            handleUrlDestination([]);
            hasUrlTarget = false;
          }
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

    if (window.TripuraExplore && window.TripuraExplore.getLiveLocationCache) {
      var initialCache = window.TripuraExplore.getLiveLocationCache();
      if (initialCache && initialCache.coords) {
        updateUserMarker(
          initialCache.coords.latitude,
          initialCache.coords.longitude,
          initialCache.coords.accuracy || 10
        );
      }
    }

    /* ================================================================
       CLEANUP on page unload
       ================================================================ */
    window.addEventListener("beforeunload", function () {
      stopBackgroundWatch();
      if (nav.animFrameId) cancelAnimationFrame(nav.animFrameId);
    });
  }

  /* ================================================================
     LIST FALLBACK (preserved from original)
     ================================================================ */
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
    var place = { lat: lat, lng: lng };
    var directionsUrl = sharedDirectionsUrl(place, null) || "#";
    var mini = L.map(placeMapElement, { center: [lat, lng], zoom: 12, scrollWheelZoom: false });
    tileLayer().addTo(mini);
    var miniMarker = L.marker([lat, lng], { icon: makeIcon(false) }).addTo(mini);
    miniMarker.bindPopup(
      '<strong>' + pName + '</strong><br>' +
      '<a class="btn btn--sm btn--primary" style="margin-top:6px;display:inline-block;" ' +
      'href="' + directionsUrl + '" ' +
      'target="_blank" rel="noopener noreferrer" data-live-directions data-lat="' + lat + '" data-lng="' + lng + '" data-name="' + pName + '">' +
      'Get directions</a>'
    );
  }
})();
