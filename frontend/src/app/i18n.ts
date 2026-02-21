import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import enLocale from "../locales/en.json";
import trLocale from "../locales/tr.json";
import deLocale from "../locales/de.json";
import itLocale from "../locales/it.json";
import elLocale from "../locales/el.json";
import bgLocale from "../locales/bg.json";
import roLocale from "../locales/ro.json";
import sqLocale from "../locales/sq.json";
import { getLocaleFromPathname, resolveLocale, SUPPORTED_LOCALES } from "../lib/localeRouting";

export const LOCALE_STORAGE_KEY = "quidme_locale";

const getInitialLanguage = () => {
  if (typeof window === "undefined") return "en";
  const fromPath = getLocaleFromPathname(window.location.pathname);
  if (fromPath) return fromPath;
  const saved = localStorage.getItem(LOCALE_STORAGE_KEY);
  const normalizedSaved = resolveLocale(saved);
  if (normalizedSaved) return normalizedSaved;
  return "en";
};

const resources = {
  en: {
    translation: enLocale,
  },
  tr: {
    translation: trLocale,
  },
  de: {
    translation: deLocale,
  },
  it: {
    translation: itLocale,
  },
  el: {
    translation: elLocale,
  },
  bg: {
    translation: bgLocale,
  },
  ro: {
    translation: roLocale,
  },
  sq: {
    translation: sqLocale,
  },
} as const;

i18n.use(initReactI18next).init({
  resources,
  lng: getInitialLanguage(),
  supportedLngs: [...SUPPORTED_LOCALES],
  fallbackLng: "en",
  interpolation: { escapeValue: false }
});

export default i18n;
