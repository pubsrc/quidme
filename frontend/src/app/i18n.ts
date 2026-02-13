import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import enLocale from "../locales/en.json";
import trLocale from "../locales/tr.json";

export const LOCALE_STORAGE_KEY = "quidme_locale";

const getInitialLanguage = () => {
  if (typeof window === "undefined") return "en";
  const saved = localStorage.getItem(LOCALE_STORAGE_KEY);
  if (saved === "en" || saved === "tr") return saved;
  return "en";
};

const resources = {
  en: {
    translation: enLocale,
  },
  tr: {
    translation: trLocale,
  },
} as const;

i18n.use(initReactI18next).init({
  resources,
  lng: getInitialLanguage(),
  supportedLngs: ["en", "tr"],
  fallbackLng: "en",
  interpolation: { escapeValue: false }
});

export default i18n;
