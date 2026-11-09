/* The Smart Admin UI is light-only. Keycloak 26's login page switches to a dark palette when the
   browser prefers dark mode, so keep the PatternFly dark class off <html> to match the app. */
(function () {
  var DARK = "pf-v5-theme-dark";
  var root = document.documentElement;
  function strip() { if (root.classList.contains(DARK)) root.classList.remove(DARK); }
  strip();
  new MutationObserver(strip).observe(root, { attributes: true, attributeFilter: ["class"] });
})();
