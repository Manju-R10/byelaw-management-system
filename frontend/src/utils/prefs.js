/** Small persisted UI preferences (applied to the document root). */
const DENSITY_KEY = "blms_density";
const LANG_KEY = "blms_lang";

export const prefs = {
  getDensity: () => localStorage.getItem(DENSITY_KEY) || "comfortable",
  setDensity: (value) => {
    localStorage.setItem(DENSITY_KEY, value);
    applyDensity();
  },
  getLang: () => localStorage.getItem(LANG_KEY) || "en",
  setLang: (value) => localStorage.setItem(LANG_KEY, value),
};

export function applyDensity() {
  document.body.classList.toggle("density-compact", prefs.getDensity() === "compact");
}
