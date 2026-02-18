import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { LOCALE_STORAGE_KEY } from "../app/i18n";
import { replaceLocaleInPathname } from "../lib/localeRouting";

const snapshotIdeas = [
  { titleKey: "pages.landing.ideas.piano", image: "/landing-piano.svg" },
  { titleKey: "pages.landing.ideas.lunch", image: "/landing-lunch.svg" },
  { titleKey: "pages.landing.ideas.spanish", image: "/landing-spanish.svg" },
  { titleKey: "pages.landing.ideas.maths", image: "/landing-maths.svg" },
];

const LandingPage = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const currentLanguage = (i18n.resolvedLanguage || "en").startsWith("tr") ? "tr" : "en";

  const setLanguage = async (lang: "en" | "tr") => {
    await i18n.changeLanguage(lang);
    localStorage.setItem(LOCALE_STORAGE_KEY, lang);
    navigate(replaceLocaleInPathname(location.pathname, lang), { replace: true });
  };

  return (
    <div className="quidme-landing min-h-screen">
      <div className="quidme-orb quidme-orb--a" aria-hidden />
      <div className="quidme-orb quidme-orb--b" aria-hidden />
      <div className="quidme-orb quidme-orb--c" aria-hidden />

      <header className="relative z-10 mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-6 md:px-10">
        <div className="flex items-center gap-3">
          <img src="/quidme-logo.svg" alt={t("layouts.dashboard.logo_alt")} className="h-11 w-11 rounded-full" />
          <div>
            <div className="text-xl font-semibold tracking-tight text-[#5a3000]">{t("pages.landing.brand")}</div>
          </div>
        </div>

        <div>
          <label htmlFor="landing-language" className="sr-only">
            {t("layouts.dashboard.language.label")}
          </label>
          <select
            id="landing-language"
            value={currentLanguage}
            onChange={(e) => setLanguage(e.target.value as "en" | "tr")}
            aria-label={t("layouts.dashboard.language.label")}
            className="h-10 rounded-full border border-[#d89c35] bg-white/80 px-4 text-sm font-semibold text-[#603400] backdrop-blur outline-none transition hover:bg-white"
          >
            <option value="en">🇬🇧 English</option>
            <option value="tr">🇹🇷 Türkçe</option>
          </select>
        </div>
      </header>

      <main className="relative z-10 mx-auto w-full max-w-7xl px-6 pb-16 pt-6 md:px-10 md:pt-10">
        <section className="grid items-center gap-10 lg:grid-cols-2">
          <div>
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55 }}
              className="text-4xl font-bold leading-tight text-[#472700] md:text-6xl"
            >
              {t("pages.landing.tagline")}
            </motion.h1>
            <p className="mt-5 text-lg font-medium text-[#6e4311] md:text-xl">{t("app.hero_title")}</p>
            <p className="mt-3 max-w-xl text-base text-[#7f5420] md:text-lg">{t("app.hero_subtitle")}</p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to="signup"
                className="rounded-full bg-[#ee9a0d] px-6 py-3 text-sm font-semibold text-white shadow-[0_10px_24px_rgba(190,105,0,0.35)]"
              >
                {t("app.get_started")}
              </Link>
              <Link
                to="login"
                className="rounded-full border border-[#cd9033] bg-white/70 px-6 py-3 text-sm font-semibold text-[#653300]"
              >
                {t("pages.landing.sign_in")}
              </Link>
            </div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, delay: 0.1 }}
            className="rounded-3xl border border-[#e1b361] bg-[#fff2cf]/90 p-7 shadow-[0_24px_50px_rgba(161,88,0,0.25)]"
          >
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold uppercase tracking-[0.16em] text-[#8f5d1b]">{t("pages.landing.snapshot_title")}</div>
              <img src="/quidme-logo.svg" alt="Quidme coin logo" className="h-9 w-9" />
            </div>

            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {snapshotIdeas.map((item, index) => (
                <motion.div
                  key={item.image}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.35, delay: 0.2 + index * 0.1 }}
                  whileHover={{ y: -4, scale: 1.01 }}
                  className="rounded-2xl border border-[#e7bf76] bg-white/70 p-3"
                >
                  <motion.div
                    animate={{ y: [0, -4, 0] }}
                    transition={{ repeat: Infinity, duration: 3, delay: index * 0.2 }}
                    className="overflow-hidden rounded-xl border border-[#f0d29d]"
                  >
                    <img src={item.image} alt={t(item.titleKey)} className="h-24 w-full object-cover" />
                  </motion.div>
                  <div className="mt-2 text-xs font-medium leading-snug text-[#7f5120]">{t(item.titleKey)}</div>
                </motion.div>
              ))}
            </div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.55 }}
              className="mt-6 rounded-2xl bg-gradient-to-r from-[#f3a11c] via-[#ffb534] to-[#f5c45f] p-4 text-white"
            >
              <div className="text-sm font-medium text-white/90">{t("pages.landing.snapshot_footer_subtitle")}</div>
              <div className="mt-2 text-xl font-bold">{t("pages.landing.snapshot_footer_title")}</div>
            </motion.div>
          </motion.div>
        </section>
      </main>
    </div>
  );
};

export default LandingPage;
