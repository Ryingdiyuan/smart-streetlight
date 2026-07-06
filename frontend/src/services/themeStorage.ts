export type AppTheme = "light" | "dark";

const THEME_STORAGE_KEY = "smart-streetlight-theme";

function isTheme(value: string | null): value is AppTheme {
  return value === "light" || value === "dark";
}

export function applyTheme(theme: AppTheme) {
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
}

export function getStoredTheme(): AppTheme {
  const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
  return isTheme(savedTheme) ? savedTheme : "dark";
}

export function saveTheme(theme: AppTheme) {
  localStorage.setItem(THEME_STORAGE_KEY, theme);
  applyTheme(theme);
}

export function initTheme() {
  applyTheme(getStoredTheme());
}
