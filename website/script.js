(() => {
  "use strict";

  const DEFAULTS = Object.freeze({
    mode: "dark",
    colorA: "#00D9FF",
    colorB: "#E33BFF"
  });
  const STORAGE_KEY = "leos-site-theme-v1";
  const root = document.documentElement;
  const toggle = document.querySelector(".menu-toggle");
  const nav = document.querySelector("#navigation");
  const themeToggle = document.querySelector("#theme-toggle");
  const themePanel = document.querySelector("#theme-panel");
  const themeClose = document.querySelector("#theme-close");
  const modeButtons = [...document.querySelectorAll("[data-theme-mode]")];
  const colorAInput = document.querySelector("#theme-color-a");
  const colorBInput = document.querySelector("#theme-color-b");
  const colorAValue = document.querySelector("#theme-color-a-value");
  const colorBValue = document.querySelector("#theme-color-b-value");
  const resetButton = document.querySelector("#theme-reset");
  const status = document.querySelector("#theme-status");
  const themeColorMeta = document.querySelector('meta[name="theme-color"]');

  let preferences = { ...DEFAULTS };
  let appearanceTimer = null;

  function normalizeColor(value, fallback) {
    return typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value.trim())
      ? value.trim().toUpperCase()
      : fallback;
  }

  function loadPreferences() {
    try {
      const saved = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "null");
      if (saved && typeof saved === "object") {
        preferences = {
          mode: ["dark", "light", "auto"].includes(saved.mode) ? saved.mode : DEFAULTS.mode,
          colorA: normalizeColor(saved.colorA, DEFAULTS.colorA),
          colorB: normalizeColor(saved.colorB, DEFAULTS.colorB)
        };
      }
    } catch {
      // Private browsing or disabled storage: keep working with in-memory defaults.
      preferences = { ...DEFAULTS };
    }
  }

  function savePreferences() {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
      if (status) status.textContent = "Vos choix sont enregistrés dans ce navigateur.";
    } catch {
      if (status) status.textContent = "Préférences actives pour cette visite (stockage indisponible).";
    }
  }

  function resolveAppearance() {
    if (preferences.mode !== "auto") return preferences.mode;
    const hour = new Date().getHours();
    return hour >= 7 && hour < 19 ? "light" : "dark";
  }

  function syncColorControls() {
    if (colorAInput) colorAInput.value = preferences.colorA;
    if (colorBInput) colorBInput.value = preferences.colorB;
    if (colorAValue) colorAValue.value = preferences.colorA;
    if (colorBValue) colorBValue.value = preferences.colorB;
  }

  function contrastRatio(hex, foreground) {
    const channels = [1, 3, 5].map(index => parseInt(hex.slice(index, index + 2), 16) / 255);
    const linear = channels.map(value => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4);
    const luminance = 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
    const other = foreground === "#FFFFFF" ? 1 : 0;
    return (Math.max(luminance, other) + 0.05) / (Math.min(luminance, other) + 0.05);
  }

  function chooseGradientTextColor() {
    const whiteScore = Math.min(contrastRatio(preferences.colorA, "#FFFFFF"), contrastRatio(preferences.colorB, "#FFFFFF"));
    const darkScore = Math.min(contrastRatio(preferences.colorA, "#071015"), contrastRatio(preferences.colorB, "#071015"));
    return whiteScore >= darkScore ? "#FFFFFF" : "#071015";
  }

  function applyPreferences() {
    const appearance = resolveAppearance();
    root.dataset.appearance = appearance;
    root.dataset.appearanceMode = preferences.mode;
    root.style.setProperty("--a", preferences.colorA);
    root.style.setProperty("--b", preferences.colorB);
    root.style.setProperty("--gradient", "linear-gradient(112deg, " + preferences.colorA + " 0%, " + preferences.colorB + " 100%)");
    root.style.setProperty("--gradient-ink", chooseGradientTextColor());
    if (themeColorMeta) themeColorMeta.setAttribute("content", appearance === "light" ? "#F4F6FA" : "#090B10");
    modeButtons.forEach(button => {
      button.setAttribute("aria-pressed", String(button.dataset.themeMode === preferences.mode));
    });
    syncColorControls();
    scheduleAppearanceUpdate();
  }

  function scheduleAppearanceUpdate() {
    if (appearanceTimer) window.clearTimeout(appearanceTimer);
    if (preferences.mode !== "auto") return;

    const now = new Date();
    const next = new Date(now);
    const hour = now.getHours();
    if (hour < 7) {
      next.setHours(7, 0, 0, 0);
    } else if (hour < 19) {
      next.setHours(19, 0, 0, 0);
    } else {
      next.setDate(next.getDate() + 1);
      next.setHours(7, 0, 0, 0);
    }
    const delay = Math.max(1000, next.getTime() - now.getTime() + 250);
    appearanceTimer = window.setTimeout(() => {
      const currentAppearance = root.dataset.appearance;
      const newAppearance = resolveAppearance();
      if (currentAppearance !== newAppearance) applyPreferences();
      else scheduleAppearanceUpdate();
    }, delay);
  }

  function updateColor(which, value) {
    const color = normalizeColor(value, DEFAULTS[which]);
    preferences[which] = color;
    applyPreferences();
    savePreferences();
  }

  function setPanelOpen(open) {
    if (!themePanel || !themeToggle) return;
    themePanel.hidden = !open;
    themeToggle.setAttribute("aria-expanded", String(open));
    if (open) {
      const firstControl = themePanel.querySelector("[data-theme-mode]");
      if (firstControl) firstControl.focus();
    } else {
      themeToggle.focus();
    }
  }

  loadPreferences();
  applyPreferences();

  if (themeToggle && themePanel) {
    themeToggle.addEventListener("click", () => setPanelOpen(themePanel.hidden));
  }
  if (themeClose) themeClose.addEventListener("click", () => setPanelOpen(false));

  modeButtons.forEach(button => {
    button.addEventListener("click", () => {
      if (!["dark", "light", "auto"].includes(button.dataset.themeMode)) return;
      preferences.mode = button.dataset.themeMode;
      applyPreferences();
      savePreferences();
    });
  });

  if (colorAInput) colorAInput.addEventListener("input", event => updateColor("colorA", event.currentTarget.value));
  if (colorBInput) colorBInput.addEventListener("input", event => updateColor("colorB", event.currentTarget.value));

  if (resetButton) {
    resetButton.addEventListener("click", () => {
      preferences = { ...DEFAULTS };
      applyPreferences();
      savePreferences();
      if (status) status.textContent = "Thème LEOS par défaut restauré.";
    });
  }

  document.addEventListener("pointerdown", event => {
    if (!themePanel || themePanel.hidden) return;
    if (themePanel.contains(event.target) || themeToggle.contains(event.target)) return;
    setPanelOpen(false);
  });

  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && themePanel && !themePanel.hidden) setPanelOpen(false);
  });

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && preferences.mode === "auto") {
      applyPreferences();
    }
  });

  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const isOpen = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!isOpen));
      toggle.setAttribute("aria-label", isOpen ? "Ouvrir le menu" : "Fermer le menu");
      nav.classList.toggle("is-open", !isOpen);
    });

    nav.querySelectorAll("a").forEach(link => {
      link.addEventListener("click", () => {
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Ouvrir le menu");
        nav.classList.remove("is-open");
      });
    });
  }

  const year = document.querySelector("#year");
  if (year) year.textContent = String(new Date().getFullYear());
})();