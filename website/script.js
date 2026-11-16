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
  let logoRenderToken = 0;
  const logoCache = new Map();

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


  function hexToRgb(hex) {
    return [1, 3, 5].map(index => parseInt(hex.slice(index, index + 2), 16));
  }

  function rgbToHsl(red, green, blue) {
    const r = red / 255, g = green / 255, b = blue / 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    const delta = max - min;
    let hue = 0;
    let saturation = 0;
    const lightness = (max + min) / 2;
    if (delta !== 0) {
      saturation = delta / (1 - Math.abs(2 * lightness - 1));
      if (max === r) hue = ((g - b) / delta) % 6;
      else if (max === g) hue = (b - r) / delta + 2;
      else hue = (r - g) / delta + 4;
      hue *= 60;
      if (hue < 0) hue += 360;
    }
    return [hue, saturation, lightness];
  }

  function hslToRgb(hue, saturation, lightness) {
    const chroma = (1 - Math.abs(2 * lightness - 1)) * saturation;
    const segment = hue / 60;
    const second = chroma * (1 - Math.abs((segment % 2) - 1));
    let rgb;
    if (segment < 1) rgb = [chroma, second, 0];
    else if (segment < 2) rgb = [second, chroma, 0];
    else if (segment < 3) rgb = [0, chroma, second];
    else if (segment < 4) rgb = [0, second, chroma];
    else if (segment < 5) rgb = [second, 0, chroma];
    else rgb = [chroma, 0, second];
    const offset = lightness - chroma / 2;
    return rgb.map(value => Math.round((value + offset) * 255));
  }

  function recolorBrandingLogos() {
    const logos = [...document.querySelectorAll("[data-themeable-logo]")];
    if (!logos.length) return;
    const token = ++logoRenderToken;
    const cacheKey = preferences.colorA + ":" + preferences.colorB;
    const cached = logoCache.get(cacheKey);
    if (cached) {
      logos.forEach(logo => { logo.src = cached; });
      return;
    }

    const originalSource = logos[0].dataset.logoSource || logos[0].getAttribute("src");
    if (!originalSource) return;
    const sourceImage = new Image();
    sourceImage.onload = () => {
      if (token !== logoRenderToken) return;
      try {
        const canvas = document.createElement("canvas");
        canvas.width = sourceImage.naturalWidth;
        canvas.height = sourceImage.naturalHeight;
        const context = canvas.getContext("2d", { willReadFrequently: true });
        if (!context) return;
        context.drawImage(sourceImage, 0, 0);
        const image = context.getImageData(0, 0, canvas.width, canvas.height);
        const pixels = image.data;
        const start = hexToRgb(preferences.colorA);
        const end = hexToRgb(preferences.colorB);

        // Re-map only chromatic parts of the official cyan-to-magenta artwork.
        // Source lightness and low-saturation metallic highlights stay intact.
        for (let index = 0; index < pixels.length; index += 4) {
          if (pixels[index + 3] === 0) continue;
          const [hue, saturation, lightness] = rgbToHsl(
            pixels[index], pixels[index + 1], pixels[index + 2]
          );
          if (saturation < 0.16 || lightness < 0.055 || lightness > 0.94) continue;
          const position = Math.max(0, Math.min(1, (hue - 180) / 120));
          const targetRgb = start.map((channel, channelIndex) =>
            channel + (end[channelIndex] - channel) * position
          );
          const [targetHue, targetSaturation] = rgbToHsl(...targetRgb);
          const recolored = hslToRgb(targetHue, Math.max(0.18, targetSaturation), lightness);
          pixels[index] = recolored[0];
          pixels[index + 1] = recolored[1];
          pixels[index + 2] = recolored[2];
        }

        context.putImageData(image, 0, 0);
        const themedUrl = canvas.toDataURL("image/png");
        if (token !== logoRenderToken) return;
        if (logoCache.size > 8) logoCache.clear();
        logoCache.set(cacheKey, themedUrl);
        logos.forEach(logo => { logo.src = themedUrl; });
      } catch {
        // Keep the official source image if the browser blocks canvas access.
      }
    };
    sourceImage.onerror = () => {
      // The original image remains visible when canvas processing is unavailable.
    };
    sourceImage.src = originalSource;
  }


  function relativeLuminance(hex) {
    const channels = [1, 3, 5].map(index => parseInt(hex.slice(index, index + 2), 16) / 255);
    const linear = channels.map(value =>
      value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4
    );
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
  }

  function contrastBetween(first, second) {
    const firstLuminance = relativeLuminance(first);
    const secondLuminance = relativeLuminance(second);
    return (Math.max(firstLuminance, secondLuminance) + 0.05) /
      (Math.min(firstLuminance, secondLuminance) + 0.05);
  }

  function resolveAccentTextColor(accent, appearance) {
    const surfaces = appearance === "light"
      ? ["#F4F6FA", "#FFFFFF", "#E9EEF4"]
      : ["#090B10", "#121720", "#182732"];
    if (surfaces.every(surface => contrastBetween(accent, surface) >= 4.5)) return accent;
    return appearance === "light" ? "#1C2430" : "#F4F7FB";
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
    root.style.setProperty("--a-text", resolveAccentTextColor(preferences.colorA, appearance));
    root.style.setProperty("--b-text", resolveAccentTextColor(preferences.colorB, appearance));
    root.style.setProperty("--gradient-text", "linear-gradient(112deg, " + resolveAccentTextColor(preferences.colorA, appearance) + " 0%, " + resolveAccentTextColor(preferences.colorB, appearance) + " 100%)");
    root.style.setProperty("--gradient", "linear-gradient(112deg, " + preferences.colorA + " 0%, " + preferences.colorB + " 100%)");
    root.style.setProperty("--gradient-ink", chooseGradientTextColor());
    if (themeColorMeta) themeColorMeta.setAttribute("content", appearance === "light" ? "#F4F6FA" : "#090B10");
    modeButtons.forEach(button => {
      button.setAttribute("aria-pressed", String(button.dataset.themeMode === preferences.mode));
    });
    syncColorControls();
    recolorBrandingLogos();
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

  function setPanelOpen(open, restoreFocus = false) {
    if (!themePanel || !themeToggle) return;
    themePanel.hidden = !open;
    themeToggle.setAttribute("aria-expanded", String(open));
    if (open) {
      const firstControl = themePanel.querySelector("[data-theme-mode]");
      if (firstControl) firstControl.focus();
    } else if (restoreFocus) {
      themeToggle.focus();
    }
  }

  loadPreferences();
  applyPreferences();

  if (themeToggle && themePanel) {
    themeToggle.addEventListener("click", () => setPanelOpen(themePanel.hidden));
  }
  if (themeClose) themeClose.addEventListener("click", () => setPanelOpen(false, true));

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
    if (event.key === "Escape" && themePanel && !themePanel.hidden) setPanelOpen(false, true);
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