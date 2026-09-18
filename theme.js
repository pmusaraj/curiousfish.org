(() => {
  const root = document.documentElement;
  const system = window.matchMedia("(prefers-color-scheme: dark)");
  const key = "curiousfish-theme";
  let preference = "system";
  let button;

  try {
    const saved = localStorage.getItem(key);
    if (saved === "light" || saved === "dark") preference = saved;
  } catch {
    // The toggle still works when storage is unavailable.
  }

  const systemTheme = () => system.matches ? "dark" : "light";
  const opposite = (theme) => theme === "dark" ? "light" : "dark";
  const nextTheme = () => preference === "system" ? opposite(systemTheme()) :
    preference === systemTheme() ? "system" : systemTheme();

  function apply() {
    if (preference === "system") delete root.dataset.theme;
    else root.dataset.theme = preference;

    const effective = preference === "system" ? systemTheme() : preference;
    document.querySelectorAll('meta[name="theme-color"]').forEach((meta) => {
      meta.content = effective === "dark" ? "#141c28" : "#f9fbfd";
    });
    if (button) {
      button.dataset.preference = preference;
      const current = preference === "system" ? `system (${effective})` : preference;
      const label = `Theme: ${current}. Switch to ${nextTheme()}.`;
      button.setAttribute("aria-label", label);
      button.title = label;
    }
  }

  // Apply saved overrides before rendering the body.
  apply();
  system.addEventListener("change", apply);
  window.addEventListener("storage", (event) => {
    if (event.key !== key && event.key !== null) return;
    preference = ["light", "dark"].includes(event.newValue) ? event.newValue : "system";
    apply();
  });
  document.addEventListener("DOMContentLoaded", () => {
    button = document.querySelector(".theme-toggle");
    if (!button) return;
    button.hidden = false;
    apply();
    button.addEventListener("click", () => {
      preference = nextTheme();
      try {
        if (preference === "system") localStorage.removeItem(key);
        else localStorage.setItem(key, preference);
      } catch {
        // Keep the in-memory preference for this page.
      }
      apply();
    });
  });
})();
