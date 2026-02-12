import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const resources = {
  en: {
    translation: {
      hero_title: "Sell products faster with Quidme",
      hero_subtitle: "Create product checkouts, manage subscriptions, track sales, and issue refunds in one place.",
      get_started: "Get Started",
      login: "Log In",
      signup: "Sign Up",
      start_accepting: "Start accepting payment",
      start_accepting_body: "Create a Stripe Express account to start receiving payouts.",
      create_link: "Create Payment Link",
      create_subscription: "Create Subscription Link"
    }
  }
} as const;

i18n.use(initReactI18next).init({
  resources,
  lng: "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false }
});

export default i18n;
