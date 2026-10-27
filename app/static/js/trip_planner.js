/* Trip planner: generate a plan with fetch(), render it day by day, and save it.
   The form still submits normally without JavaScript (see itineraries.trip_planner). */
(function () {
  "use strict";

  var form = document.getElementById("planner-form");
  if (!form) return;

  var configNode = document.getElementById("planner-config");
  var config = configNode ? JSON.parse(configNode.textContent || "{}") : {};
  var results = document.getElementById("planner-results");
  var status = document.getElementById("planner-status");
  var submitButton = form.querySelector("[data-planner-submit]");
  var submitLabel = submitButton ? submitButton.innerHTML : "Generate itinerary";
  var currentPlan = null;

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (character) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[character];
    });
  }

  function setBusy(busy) {
    if (!submitButton) return;
    submitButton.disabled = busy;
    submitButton.innerHTML = busy
      ? '<span class="spinner" aria-hidden="true"></span> Building your plan…'
      : submitLabel;
  }

  function payload(save) {
    var data = new FormData(form);
    return {
      duration_days: Number(data.get("duration_days")),
      starting_location: data.get("starting_location"),
      interests: data.getAll("interests"),
      budget: data.get("budget") || null,
      travel_date: data.get("travel_date") || null,
      save: !!save
    };
  }

  function stopHtml(stop) {
    var place = stop.place;
    var image = place.image_url
      ? '<img src="' + escapeHtml(place.image_url) + '" alt="" width="70" height="54" style="border-radius:8px;object-fit:cover">'
      : "";
    var leg =
      stop.leg_km !== null && stop.leg_km !== undefined
        ? '<p class="text-muted" style="font-size:.82rem;margin:10px 0 0">≈ ' + stop.leg_km + " km straight line from the previous stop</p>"
        : "";
    var directions = place.map_ready
      ? ""
      : "";
    var visitFacts = [];
    if (place.opening_info) visitFacts.push("Hours: " + escapeHtml(place.opening_info));
    if (place.closed_day) visitFacts.push("Closed: " + escapeHtml(place.closed_day));
    if (place.typical_visit_hours) visitFacts.push("Suggested visit: " + escapeHtml(place.typical_visit_hours) + " hours");
    if (place.entry_fee_indian) visitFacts.push("Indian visitors: " + escapeHtml(place.entry_fee_indian));
    if (place.entry_fee_foreign) visitFacts.push("International visitors: " + escapeHtml(place.entry_fee_foreign));
    var visitDetails = visitFacts.length
      ? '<p class="text-muted" style="font-size:.82rem;margin:8px 0 0">' + visitFacts.join(" · ") + "</p>"
      : "";
    return (
      '<li class="timeline__item">' +
      '<span class="timeline__marker">' +
      stop.stop_order +
      "</span>" +
      '<div class="timeline__body">' +
      '<div class="between" style="align-items:flex-start">' +
      "<div>" +
      '<h4 style="margin:0;font-size:1rem"><a href="' + escapeHtml(place.url) + '">' + escapeHtml(place.name) + "</a></h4>" +
      '<p class="text-muted" style="font-size:.85rem;margin:4px 0 0">' +
      escapeHtml(place.category || "") +
      (place.locality ? " · " + escapeHtml(place.locality) : "") +
      (place.district ? " · " + escapeHtml(place.district) : "") +
      "</p></div>" +
      image +
      "</div>" +
      visitDetails +
      leg +
      directions +
      "</div></li>"
    );
  }

  function render(plan, saved) {
    currentPlan = plan;
    var days = plan.days || [];
    var totalStops = days.reduce(function (sum, day) {
      return sum + (day.stops ? day.stops.length : 0);
    }, 0);

    var html = '<section aria-labelledby="plan-heading">';
    html += '<div class="section-head"><div><p class="eyebrow">Suggested plan</p>';
    html +=
      '<h2 id="plan-heading">' +
      days.length +
      " day" +
      (days.length === 1 ? "" : "s") +
      " · " +
      totalStops +
      " stop" +
      (totalStops === 1 ? "" : "s") +
      "</h2>";
    html += '<p>Matched ' + plan.matched_count + " published destination(s) for your interests.</p></div></div>";

    (plan.warnings || []).forEach(function (warning) {
      html += '<div class="alert alert--warning">' + escapeHtml(warning) + "</div>";
    });
    (plan.notes || []).forEach(function (note) {
      html += '<div class="alert alert--info">' + escapeHtml(note) + "</div>";
    });

    if (days.length) {
      html += '<div class="grid grid--2" style="margin-top:24px">';
      days.forEach(function (day) {
        html += '<div class="day-column"><div class="between"><h3 style="margin:0">Day ' + day.day + "</h3>";
        html +=
          '<span class="badge badge--muted">' +
          day.stops.length +
          " stop" +
          (day.stops.length === 1 ? "" : "s") +
          "</span></div>";
        html += '<ol class="timeline" style="margin-top:16px">' + day.stops.map(stopHtml).join("") + "</ol></div>";
      });
      html += "</div>";

      html += '<div class="card" style="padding:16px;margin-top:24px"><h3 style="margin-top:0">Save this plan</h3>';
      if (config.isAuthenticated) {
        html += '<p class="text-muted">Save it to your account to reorder stops and share a read-only link.</p>';
        html += '<button class="btn btn--primary" type="button" id="save-plan-button">Save this itinerary</button>';
      } else {
        html += '<p class="text-muted">Sign in to save this plan, reorder stops and share a read-only link.</p>';
        html += '<a class="btn btn--primary" href="' + escapeHtml(config.loginUrl) + '">Sign in to save</a>';
      }
      html += "</div>";
    } else {
      html +=
        '<div class="empty-state"><h3>No matching destinations</h3><p>' +
        escapeHtml((plan.warnings || ["Try selecting more interests."]).slice(-1)[0]) +
        "</p></div>";
    }
    html += "</section>";

    results.innerHTML = html;

    var saveButton = document.getElementById("save-plan-button");
    if (saveButton) {
      saveButton.addEventListener("click", function () {
        saveButton.disabled = true;
        saveButton.innerHTML = '<span class="spinner"></span> Saving…';
        window.TripuraExplore.apiFetch(config.saveUrl, { method: "POST", body: payload(true) })
          .then(function (data) {
            window.TripuraExplore.showToast("Itinerary saved.", "success");
            if (data.saved && data.saved.url) {
              window.location.href = data.saved.url;
            }
          })
          .catch(function (error) {
            saveButton.disabled = false;
            saveButton.textContent = "Save this itinerary";
            if (error.status === 401) {
              window.TripuraExplore.showToast("Please sign in to save trips.", "info");
              window.setTimeout(function () {
                window.location.href = config.loginUrl;
              }, 900);
              return;
            }
            window.TripuraExplore.showToast(error.message, "error");
          });
      });
    }
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    setBusy(true);
    status.innerHTML = "";

    window.TripuraExplore.apiFetch(config.apiUrl, { method: "POST", body: payload(false) })
      .then(function (data) {
        render(data.plan);
        results.scrollIntoView({ behavior: "smooth", block: "start" });
      })
      .catch(function (error) {
        status.innerHTML = '<div class="alert alert--error">' + escapeHtml(error.message) + "</div>";
      })
      .finally(function () {
        setBusy(false);
      });
  });

  var initialNode = document.getElementById("planner-initial-plan");
  if (initialNode) {
    var initial = JSON.parse(initialNode.textContent || "{}");
    if (initial.days) render(initial);
  }
})();
