export type AppTheme = "aurora-night" | "mist-light";

const THEME_STORAGE_KEY = "smart-streetlight-mobile-theme";

export function getStoredTheme(): AppTheme {
  const theme = localStorage.getItem(THEME_STORAGE_KEY);
  return theme === "mist-light" ? "mist-light" : "aurora-night";
}

export function saveTheme(theme: AppTheme) {
  localStorage.setItem(THEME_STORAGE_KEY, theme);
  document.documentElement.dataset.theme = theme;
}

export function applyStoredTheme() {
  saveTheme(getStoredTheme());
}
