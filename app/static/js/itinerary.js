/* Saved trip page: remove a stop, move a stop to another day and reorder stops
   inside a day by dragging. Every change is saved to the owner's account. */
(function () {
  "use strict";

  var root = document.getElementById("itinerary-root");
  if (!root) return;

  var configNode = document.getElementById("itinerary-config");
  var config = configNode ? JSON.parse(configNode.textContent || "{}") : {};
  var apiBase = config.apiBase || root.getAttribute("data-api-base");
  var status = document.getElementById("itinerary-status");
  var daysContainer = document.getElementById("itinerary-days");
  var maxPerDay = config.maxPerDay || 3;
  var dragged = null;

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (character) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[character];
    });
  }

  function setStatus(message, kind) {
    status.innerHTML = message
      ? '<div class="alert alert--' + (kind || "info") + '">' + escapeHtml(message) + "</div>"
      : "";
  }

  function stopRow(stop, durationDays) {
    var place = stop.place || {};
    var dayOptions = "";
    for (var day = 1; day <= durationDays; day += 1) {
      dayOptions +=
        '<option value="' + day + '"' + (day === stop.day_number ? " selected" : "") + ">" + day + "</option>";
    }
    return (
      '<li class="timeline__item" data-stop-id="' + stop.id + '" draggable="true">' +
      '<button class="drag-handle" type="button" aria-label="Reorder stop">⠿</button>' +
      '<div class="timeline__body">' +
      '<div class="between" style="align-items:flex-start"><div>' +
      '<h4 style="margin:0;font-size:1rem"><a href="' + escapeHtml(place.url) + '">' + escapeHtml(place.name) + "</a></h4>" +
      '<p class="text-muted" style="font-size:.84rem;margin:4px 0 0">' +
      escapeHtml(place.category || "") +
      (place.locality ? " · " + escapeHtml(place.locality) : "") +
      "</p></div>" +
      '<button class="icon-button" type="button" data-remove-stop="' + stop.id + '" aria-label="Remove ' + escapeHtml(place.name) + '">✕</button>' +
      "</div>" +
      '<div class="cluster" style="margin-top:10px">' +
      '<label class="text-muted" style="font-size:.82rem" for="day-move-' + stop.id + '">Day</label>' +
      '<select id="day-move-' + stop.id + '" data-move-stop="' + stop.id + '" style="width:auto;padding:6px 10px">' +
      dayOptions +
      "</select>" +
      (place.directions_url
        ? '<a class="btn btn--ghost btn--sm" href="/map?place_id=' + encodeURIComponent(place.id || '') + '&slug=' + encodeURIComponent(place.slug || '') + '&name=' + encodeURIComponent(place.name || '') + '&lat=' + (place.latitude != null ? Number(place.latitude).toFixed(5) : '') + '&lng=' + (place.longitude != null ? Number(place.longitude).toFixed(5) : '') + '&destination=' + (place.latitude != null && place.longitude != null ? Number(place.latitude).toFixed(5) + ',' + Number(place.longitude).toFixed(5) : '') + '&directions=1" data-live-directions data-place-id="' + (place.id || '') + '" data-slug="' + (place.slug || '') + '" data-lat="' + (place.latitude != null ? place.latitude : '') + '" data-lng="' + (place.longitude != null ? place.longitude : '') + '" data-name="' + escapeHtml(place.name || '') + '">Directions</a>'
        : "") +
      "</div></div></li>"
    );
  }

  function render(itinerary) {
    if (!itinerary || !itinerary.days) return;
    var html = "";
    itinerary.days.forEach(function (day) {
      html += '<div class="day-column" data-day="' + day.day + '">';
      html += '<div class="between"><h3 style="margin:0">Day ' + day.day + "</h3>";
      html +=
        '<span class="badge badge--muted" data-day-count>' +
        day.stops.length +
        " stop" +
        (day.stops.length === 1 ? "" : "s") +
        "</span></div>";
      html += '<ul class="timeline" style="margin-top:16px" data-sortable-day="' + day.day + '">';
      html += day.stops.map(function (stop) {
        return stopRow(stop, itinerary.duration_days);
      }).join("");
      html += "</ul></div>";
    });
    daysContainer.innerHTML = html;
    wire();
  }

  function handleError(error) {
    if (error.status === 403) {
      setStatus("You can only change your own trips.", "error");
      return;
    }
    setStatus(error.message, "error");
  }

  function removeStop(stopId) {
    window.TripuraExplore.apiFetch(apiBase + "/stops/" + stopId, { method: "DELETE" })
      .then(function (data) {
        render(data.itinerary);
        setStatus("Stop removed.", "success");
      })
      .catch(handleError);
  }

  function moveStop(stopId, dayNumber) {
    window.TripuraExplore.apiFetch(apiBase + "/stops/" + stopId, {
      method: "PATCH",
      body: { day_number: Number(dayNumber) }
    })
      .then(function (data) {
        render(data.itinerary);
        setStatus("Stop moved to day " + dayNumber + ".", "success");
      })
      .catch(handleError);
  }

  function saveOrder(dayNumber, list) {
    var order = Array.prototype.map.call(list.querySelectorAll("[data-stop-id]"), function (item) {
      return Number(item.getAttribute("data-stop-id"));
    });
    window.TripuraExplore.apiFetch(apiBase + "/stops", {
      method: "PATCH",
      body: { day_number: Number(dayNumber), order: order }
    })
      .then(function (data) {
        render(data.itinerary);
        setStatus("New order saved.", "success");
      })
      .catch(handleError);
  }

  function wire() {
    daysContainer.querySelectorAll("[data-remove-stop]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (window.confirm("Remove this stop from the trip?")) {
          removeStop(button.getAttribute("data-remove-stop"));
        }
      });
    });

    daysContainer.querySelectorAll("[data-move-stop]").forEach(function (select) {
      select.addEventListener("change", function () {
        moveStop(select.getAttribute("data-move-stop"), select.value);
      });
    });

    daysContainer.querySelectorAll("[data-sortable-day]").forEach(function (list) {
      list.addEventListener("dragstart", function (event) {
        var item = event.target.closest("[data-stop-id]");
        if (!item) return;
        dragged = item;
        item.classList.add("is-dragging");
      });
      list.addEventListener("dragend", function () {
        if (dragged) dragged.classList.remove("is-dragging");
        dragged = null;
      });
      list.addEventListener("dragover", function (event) {
        event.preventDefault();
        var target = event.target.closest("[data-stop-id]");
        if (!target || !dragged || target === dragged) return;
        var box = target.getBoundingClientRect();
        var after = event.clientY > box.top + box.height / 2;
        list.insertBefore(dragged, after ? target.nextSibling : target);
      });
      list.addEventListener("drop", function () {
        saveOrder(list.getAttribute("data-sortable-day"), list);
      });
    });
  }

  wire();
})();