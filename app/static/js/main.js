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

  function initLiveDirections() {
    document.addEventListener("click", function (event) {
      var btn = event.target.closest("[data-live-directions]");
      if (!btn) return;

      var lat = btn.getAttribute("data-lat");
      var lng = btn.getAttribute("data-lng");
      var name = btn.getAttribute("data-name") || "Destination";
      var fallbackUrl = btn.getAttribute("href") || "";

      var destination = "";
      if (lat && lng && !isNaN(parseFloat(lat)) && !isNaN(parseFloat(lng))) {
        destination = parseFloat(lat).toFixed(6) + "," + parseFloat(lng).toFixed(6);
      } else if (name) {
        destination = encodeURIComponent(name + ", Tripura, India");
      }

      if (!destination && !fallbackUrl) return;

      function openMaps(originCoords) {
        var finalUrl = "https://www.google.com/maps/dir/?api=1";
        if (originCoords) {
          finalUrl += "&origin=" + encodeURIComponent(originCoords);
        }
        finalUrl += "&destination=" + (destination || "") + "&travelmode=driving";

        var win = window.open(finalUrl, "_blank", "noopener,noreferrer");
        if (!win || win.closed || typeof win.closed === "undefined") {
          window.location.href = finalUrl;
        }
      }

      // If we already have a recent live GPS reading (< 5 minutes old)
      if (userLocationCache && (Date.now() - userLocationCache.timestamp < 300000)) {
        event.preventDefault();
        openMaps(userLocationCache.coords.latitude.toFixed(6) + "," + userLocationCache.coords.longitude.toFixed(6));
        return;
      }

      if (!navigator.geolocation) {
        event.preventDefault();
        openMaps(null);
        return;
      }

      event.preventDefault();

      var originalPointer = btn.style.pointerEvents;
      btn.style.pointerEvents = "none";
      showToast("Acquiring your exact live GPS location...", "info");

      var timer = window.setTimeout(function () {
        btn.style.pointerEvents = originalPointer;
        showToast("Opening directions with device GPS location...", "info");
        openMaps(null);
      }, 7000);

      navigator.geolocation.getCurrentPosition(
        function (pos) {
          window.clearTimeout(timer);
          btn.style.pointerEvents = originalPointer;
          userLocationCache = {
            coords: pos.coords,
            timestamp: Date.now()
          };
          openMaps(pos.coords.latitude.toFixed(6) + "," + pos.coords.longitude.toFixed(6));
        },
        function (err) {
          window.clearTimeout(timer);
          btn.style.pointerEvents = originalPointer;
          if (err.code === err.PERMISSION_DENIED) {
            showToast("Location access denied. Launching maps with device GPS.", "info");
          } else {
            showToast("Opening directions using device GPS.", "info");
          }
          openMaps(null);
        },
        {
          enableHighAccuracy: true,
          timeout: 7000,
          maximumAge: 0
        }
      );
    });
  }
  initLiveDirections();

  window.TripuraExplore = {
    apiFetch: apiFetch,
    csrfToken: csrfToken,
    showToast: showToast
  };
})();