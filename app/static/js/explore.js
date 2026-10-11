/* Explore page: submit the filter form on change and show a loading state.
   The form works perfectly without JavaScript - this only removes one click. */
(function () {
  "use strict";

  var form = document.getElementById("filter-form");
  if (!form) return;

  var region = document.getElementById("results-region");
  var submit = form.querySelector("[data-filter-submit]");
  var originalLabel = submit ? submit.innerHTML : "";

  form.querySelectorAll("select").forEach(function (select) {
    select.addEventListener("change", function () {
      if (submit) {
        submit.disabled = true;
        submit.innerHTML = '<span class="spinner" aria-hidden="true"></span> Applying…';
      }
      if (region) region.setAttribute("aria-busy", "true");
      form.submit();
    });
  });

  form.addEventListener("submit", function () {
    if (submit) {
      submit.disabled = true;
      submit.innerHTML = '<span class="spinner" aria-hidden="true"></span> Applying…';
    }
    if (region) region.setAttribute("aria-busy", "true");
  });

  // Restore the button if the navigation was cancelled (for example by the user).
  window.addEventListener("pageshow", function () {
    if (submit) {
      submit.disabled = false;
      submit.innerHTML = originalLabel;
    }
  });
})();