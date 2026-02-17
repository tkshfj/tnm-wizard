type Mode = "auto" | "light" | "dark";

const STORAGE_KEY = "tnm-wizard-theme";
const ICONS: Record<Mode, string> = { auto: "\u{1F5A5}", light: "\u2600\uFE0F", dark: "\u{1F319}" };
const CYCLE: Record<Mode, Mode> = { auto: "light", light: "dark", dark: "auto" };

function getMode(): Mode {
  const v = localStorage.getItem(STORAGE_KEY);
  if (v === "light" || v === "dark") return v;
  return "auto";
}

function resolve(mode: Mode): string {
  if (mode === "light") return "medical";
  if (mode === "dark") return "medical-dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "medical-dark"
    : "medical";
}

function applyTheme(mode: Mode): void {
  document.documentElement.setAttribute("data-theme", resolve(mode));
}

function updateButton(mode: Mode): void {
  const btn = document.getElementById("theme-toggle");
  if (btn) btn.textContent = ICONS[mode];
}

// Apply immediately (also handled by inline script in <head> for FOUC prevention)
let currentMode = getMode();
applyTheme(currentMode);

// React to OS preference changes when in auto mode
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if (getMode() === "auto") applyTheme("auto");
});

function init(): void {
  updateButton(currentMode);

  const btn = document.getElementById("theme-toggle");
  if (btn) {
    btn.addEventListener("click", () => {
      currentMode = CYCLE[currentMode];
      localStorage.setItem(STORAGE_KEY, currentMode);
      applyTheme(currentMode);
      updateButton(currentMode);
    });
  }
}

// Module scripts may run after DOMContentLoaded has already fired
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
