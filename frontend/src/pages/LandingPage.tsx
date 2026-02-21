import { motion } from "framer-motion";
import { CreditCard, HandCoins, Repeat, Wallet } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";
import { LOCALE_STORAGE_KEY } from "../app/i18n";
import { replaceLocaleInPathname } from "../lib/localeRouting";
import { useSeo } from "../lib/useSeo";
import QuidmeLogo from "../components/QuidmeLogo";
import LocaleLink from "../components/LocaleLink";

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

  useSeo({
    title: t("pages.landing.seo.title"),
    description: t("pages.landing.seo.description"),
    keywords: t("pages.landing.seo.keywords", { returnObjects: true }) as string[],
    canonicalPath: `/${currentLanguage}`,
    locale: currentLanguage === "tr" ? "tr_TR" : "en_GB",
    structuredData: {
      "@context": "https://schema.org",
      "@graph": [
        {
          "@type": "Organization",
          name: "Quidme",
          url: window.location.origin,
          logo: `${window.location.origin}/quidme-logo.svg`,
        },
        {
          "@type": "SoftwareApplication",
          name: "Quidme",
          applicationCategory: "BusinessApplication",
          operatingSystem: "Web",
          description: t("pages.landing.seo.description"),
          offers: {
            "@type": "Offer",
            price: "0",
            priceCurrency: "GBP",
          },
        },
      ],
    },
  });

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
          <QuidmeLogo
            alt={t("layouts.dashboard.logo_alt")}
            containerClassName="h-12 w-12"
            logoClassName="h-10 w-10"
            withBadge={false}
          />
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
              <LocaleLink
                to="signup"
                className="rounded-full bg-[#ee9a0d] px-6 py-3 text-sm font-semibold text-white shadow-[0_10px_24px_rgba(190,105,0,0.35)]"
              >
                {t("app.get_started")}
              </LocaleLink>
              <LocaleLink
                to="login"
                className="rounded-full border border-[#cd9033] bg-white/70 px-6 py-3 text-sm font-semibold text-[#653300]"
              >
                {t("pages.landing.sign_in")}
              </LocaleLink>
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
              <QuidmeLogo alt="Quidme coin logo" containerClassName="h-10 w-10" logoClassName="h-8 w-8" withBadge={false} />
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

        <section className="mt-12 grid gap-4 md:mt-14 md:grid-cols-3">
          <div className="rounded-2xl border border-[#e6bc74] bg-white/75 p-5">
            <div className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-[#ffe4b2] text-[#7b470d]">
              <Wallet className="h-5 w-5" />
            </div>
            <h2 className="mt-3 text-lg font-semibold text-[#4f2b00]">{t("pages.landing.for_who.sole_traders_title")}</h2>
            <p className="mt-1 text-sm text-[#7b4f1a]">{t("pages.landing.for_who.sole_traders_body")}</p>
          </div>

          <div className="rounded-2xl border border-[#e6bc74] bg-white/75 p-5">
            <div className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-[#ffe4b2] text-[#7b470d]">
              <Repeat className="h-5 w-5" />
            </div>
            <h2 className="mt-3 text-lg font-semibold text-[#4f2b00]">{t("pages.landing.for_who.subscriptions_title")}</h2>
            <p className="mt-1 text-sm text-[#7b4f1a]">{t("pages.landing.for_who.subscriptions_body")}</p>
          </div>

          <div className="rounded-2xl border border-[#e6bc74] bg-white/75 p-5">
            <div className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-[#ffe4b2] text-[#7b470d]">
              <HandCoins className="h-5 w-5" />
            </div>
            <h2 className="mt-3 text-lg font-semibold text-[#4f2b00]">{t("pages.landing.for_who.refunds_title")}</h2>
            <p className="mt-1 text-sm text-[#7b4f1a]">{t("pages.landing.for_who.refunds_body")}</p>
          </div>
        </section>

        <section className="mt-8 rounded-3xl border border-[#e1b361] bg-[#fff4da]/90 p-6 md:p-8">
          <div className="inline-flex h-11 w-11 items-center justify-center rounded-full bg-[#ffd28b] text-[#6e3d07]">
            <CreditCard className="h-6 w-6" />
          </div>
          <h2 className="mt-3 text-2xl font-bold text-[#4f2b00]">{t("pages.landing.benefits.title")}</h2>
          <p className="mt-2 max-w-3xl text-sm text-[#7b4f1a] md:text-base">{t("pages.landing.benefits.body")}</p>
        </section>
      </main>
    </div>
  );
};

export default LandingPage;
