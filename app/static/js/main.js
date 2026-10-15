/* Tripura Explore - shared UI behaviour.
   Kept deliberately small: navigation, flash messages, tabs, confirm dialogs,
   copy buttons and the favourite toggle. */
(function () {
  "use strict";

  var csrfMeta = document.querySelector('meta[name="csrf-token"]');
  var csrfToken = csrfMeta ? csrfMeta.getAttribute("content") : "";

  /** fetch() wrapper that adds the CSRF header and normalises errors. */
  function apiFetch(url, options) {
    var opts = Object.assign({ method: "GET" }, options || {});
    opts.headers = Object.assign({ Accept: "application/json" }, opts.headers || {});
    if (opts.body && typeof opts.body !== "string") {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(opts.body);
    }
    var method = (opts.method || "GET").toUpperCase();
    if (["POST", "PATCH", "PUT", "DELETE"].indexOf(method) !== -1) {
      opts.headers["X-CSRFToken"] = csrfToken;
    }
    return fetch(url, opts).then(function (response) {
      return response
        .json()
        .catch(function () {
          return null;
        })
        .then(function (data) {
          if (!response.ok) {
            var message =
              (data && (data.message || (data.errors || []).join(" "))) ||
              "Request failed with status " + response.status;
            var error = new Error(message);
            error.status = response.status;
            error.data = data;
            throw error;
          }
          return data;
        });
    });
  }

  function showToast(message, kind) {
    var stack = document.getElementById("flash-stack");
    if (!stack) {
      stack = document.createElement("div");
      stack.className = "flash-stack";
      stack.id = "flash-stack";
      stack.setAttribute("role", "status");
      stack.setAttribute("aria-live", "polite");
      document.body.appendChild(stack);
    }
    var type = kind || "info";
    var alert = document.createElement("div");
    alert.className = "alert alert--" + (type === "error" ? "error" : type === "success" ? "success" : "info");
    var span = document.createElement("span");
    span.textContent = message;
    alert.appendChild(span);
    stack.appendChild(alert);
    window.setTimeout(function () {
      alert.remove();
    }, 7000);
  }

  /* --- mobile navigation ------------------------------------------------- */
  var navToggle = document.querySelector("[data-nav-toggle]");
  var nav = document.getElementById("primary-navigation");
  if (navToggle && nav) {
    navToggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  /* --- flash messages ---------------------------------------------------- */
  function wireFlashStack() {
    document.querySelectorAll("[data-dismiss-flash]").forEach(function (button) {
      button.addEventListener("click", function () {
        var alert = button.closest(".alert");
        if (alert) alert.remove();
      });
    });
  }
  wireFlashStack();

  /* --- confirmation before destructive actions --------------------------- */
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      var message = form.getAttribute("data-confirm") || "Are you sure?";
      if (!window.confirm(message)) {
        event.preventDefault();
      }
    });
  });

  /* --- tabs (destination details) ---------------------------------------- */
  var tabList = document.querySelectorAll('[role="tab"]');
  if (tabList.length) {
    function selectTab(tab) {
      tabList.forEach(function (item) {
        item.setAttribute("aria-selected", item === tab ? "true" : "false");
        var panel = document.getElementById(item.getAttribute("aria-controls"));
        if (panel) panel.hidden = item !== tab;
      });
    }
    tabList.forEach(function (tab, index) {
      tab.addEventListener("click", function () {
        selectTab(tab);
      });
      tab.addEventListener("keydown", function (event) {
        var next = null;
        if (event.key === "ArrowRight") next = tabList[(index + 1) % tabList.length];
        if (event.key === "ArrowLeft") next = tabList[(index - 1 + tabList.length) % tabList.length];
        if (next) {
          event.preventDefault();
          selectTab(next);
          next.focus();
        }
      });
    });
    var hashPanel = window.location.hash && document.querySelector(window.location.hash);
    if (hashPanel && hashPanel.id === "report") {
      var reportTab = document.querySelector('[aria-controls="panel-report"]');
      if (reportTab) selectTab(reportTab);
    }
  }

  /* --- copy to clipboard -------------------------------------------------- */
  document.querySelectorAll("[data-copy-target]").forEach(function (button) {
    button.addEventListener("click", function () {
      var target = document.querySelector(button.getAttribute("data-copy-target"));
      if (!target) return;
      target.select();
      var done = function () {
        showToast("Copied to the clipboard.", "success");
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(target.value).then(done, done);
      } else {
        document.execCommand("copy");
        done();
      }
    });
  });

  /* --- favourites --------------------------------------------------------- */
  document.querySelectorAll("[data-favorite-toggle]").forEach(function (button) {
    button.addEventListener("click", function () {
      var placeId = button.getAttribute("data-place-id");
      var active = button.classList.contains("is-active");
      var url = active ? "/api/favorites/" + placeId : "/api/favorites";
      var options = active
        ? { method: "DELETE" }
        : { method: "POST", body: { place_id: Number(placeId) } };

      button.disabled = true;
      apiFetch(url, options)
        .then(function (data) {
          var nowActive = !!data.is_favorite;
          button.classList.toggle("is-active", nowActive);
          button.setAttribute("aria-pressed", nowActive ? "true" : "false");
          var name = button.getAttribute("data-place-name") || "Destination";
          showToast(
            nowActive ? "Saved " + name + " to your favourites." : "Removed " + name + " from your favourites.",
            "success"
          );
        })
        .catch(function (error) {
          if (error.status === 401) {
            showToast("Please sign in to save favourites.", "info");
            window.setTimeout(function () {
              window.location.href = "/auth/login?next=" + encodeURIComponent(window.location.pathname);
            }, 900);
            return;
          }
          showToast(error.message, "error");
        })
        .finally(function () {
          button.disabled = false;
        });
    });
  });

  /* --- live directions with device geolocation ---------------------------- */
  var userLocationCache = null;

  function buildGoogleMapsUrl(destLat, destLng, originLat, originLng) {
    if (typeof destLat !== "number" || typeof destLng !== "number" || isNaN(destLat) || isNaN(destLng) || !isFinite(destLat) || !isFinite(destLng)) {
      return null;
    }
    if (typeof originLat !== "undefined" && originLat !== null && (typeof originLat !== "number" || isNaN(originLat) || !isFinite(originLat))) {
      originLat = null;
    }
    if (typeof originLng !== "undefined" && originLng !== null && (typeof originLng !== "number" || isNaN(originLng) || !isFinite(originLng))) {
      originLng = null;
    }

    if (destLat < 22.9 || destLat > 24.6 || destLng < 91.0 || destLng > 92.4) {
      return null;
    }

    var url = "https://www.google.com/maps/dir/?api=1&destination=" + destLat.toFixed(7) + "," + destLng.toFixed(7);

    if (originLat !== null && originLng !== null && typeof originLat === "number" && typeof originLng === "number") {
      if (originLat >= -90 && originLat <= 90 && originLng >= -180 && originLng <= 180) {
        url += "&origin=" + originLat.toFixed(5) + "," + originLng.toFixed(5);
      }
    }

    url += "&travelmode=driving";
    return url;
  }

  function setLiveLocationCache(lat, lng, accuracy) {
    if (typeof lat === "number" && typeof lng === "number" && !isNaN(lat) && !isNaN(lng)) {
      userLocationCache = {
        coords: { latitude: lat, longitude: lng, accuracy: accuracy || 10 },
        timestamp: Date.now()
      };
    }
  }

  function getLiveLocationCache() {
    // Only return if fresh (< 25 seconds) to avoid stale vehicle positions
    if (userLocationCache && (Date.now() - userLocationCache.timestamp < 25000)) {
      return userLocationCache;
    }
    return null;
  }

  function initLiveDirections() {
    document.addEventListener("click", function (event) {
      var invalidButton = event.target.closest("[data-invalid-directions]");
      if (invalidButton) {
        event.preventDefault();
        var invalidName = invalidButton.getAttribute("data-name") || "Destination";
        var invalidLat = invalidButton.getAttribute("data-lat");
        var invalidLng = invalidButton.getAttribute("data-lng");
        showToast("Directions are unavailable because the coordinates for " + invalidName + " are outside Tripura or need verification.", "error");
        console.error("[Directions Error] Invalid Tripura destination coordinates:", {
          name: invalidName, latitude: invalidLat, longitude: invalidLng
        });
        return;
      }
      var btn = event.target.closest("[data-live-directions]");
      if (!btn) return;

      var placeId = btn.getAttribute("data-place-id") || null;
      var latAttr = btn.getAttribute("data-lat");
      var lngAttr = btn.getAttribute("data-lng");
      var name = btn.getAttribute("data-name") || "Destination";
      var fallbackUrl = btn.getAttribute("href") || "";
      var customDest = btn.getAttribute("data-destination") || null;

      var destLat = parseFloat(latAttr);
      var destLng = parseFloat(lngAttr);

      // Validate destination coordinates strictly
      if (isNaN(destLat) || isNaN(destLng) || !isFinite(destLat) || !isFinite(destLng) ||
          destLat < 22.9 || destLat > 24.6 || destLng < 91.0 || destLng > 92.4 ||
          (destLat === 0 && destLng === 0)) {
        event.preventDefault();
        showToast("Directions are unavailable because the coordinates for " + name + " are outside Tripura or need verification.", "error");
        console.error("[Directions Error] Invalid Tripura destination coordinates:", {
          placeId: placeId,
          name: name,
          latAttr: latAttr,
          lngAttr: lngAttr
        });
        return;
      }

      event.preventDefault();

      var slug = btn.getAttribute("data-slug") || "";
      var mapParams = new URLSearchParams();
      if (placeId) mapParams.set("place_id", placeId);
      if (slug) mapParams.set("slug", slug);
      if (name) mapParams.set("name", name);
      mapParams.set("lat", destLat.toFixed(5));
      mapParams.set("lng", destLng.toFixed(5));
      mapParams.set("destination", destLat.toFixed(5) + "," + destLng.toFixed(5));
      mapParams.set("directions", "1");

      var targetMapUrl = "/map?" + mapParams.toString();

      console.info("[Tripura Explorer Directions Navigation]", {
        destinationId: placeId,
        destinationSlug: slug,
        destinationName: name,
        destinationLatitude: destLat,
        destinationLongitude: destLng,
        targetMapUrl: targetMapUrl
      });

      if (window.location.pathname === "/map" && window.TripuraMap && typeof window.TripuraMap.selectDestination === "function") {
        window.TripuraMap.selectDestination(placeId || slug, destLat, destLng, name, true);
      } else {
        window.location.href = targetMapUrl;
      }
    });
  }
  initLiveDirections();

  window.TripuraExplore = {
    apiFetch: apiFetch,
    csrfToken: csrfToken,
    showToast: showToast,
    setLiveLocationCache: setLiveLocationCache,
    getLiveLocationCache: getLiveLocationCache,
    buildGoogleMapsUrl: buildGoogleMapsUrl
  };
})();
