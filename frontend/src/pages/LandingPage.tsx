import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

const snapshotIdeas = [
  { title: "Piano lessons for children", image: "/landing-piano.svg" },
  { title: "Home made lunch in Indian cuisine", image: "/landing-lunch.svg" },
  { title: "Spanish language lessons", image: "/landing-spanish.svg" },
  { title: "Online Maths tuitions", image: "/landing-maths.svg" },
];

const LandingPage = () => {
  const { t } = useTranslation();

  return (
    <div className="quidme-landing min-h-screen">
      <div className="quidme-orb quidme-orb--a" aria-hidden />
      <div className="quidme-orb quidme-orb--b" aria-hidden />
      <div className="quidme-orb quidme-orb--c" aria-hidden />

      <header className="relative z-10 mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-6 md:px-10">
        <div className="flex items-center gap-3">
          <img src="/quidme-logo.svg" alt="Quidme logo" className="h-11 w-11 rounded-full" />
          <div>
            <div className="text-xl font-semibold tracking-tight text-[#5a3000]">Quidme</div>
            <div className="text-xs font-medium uppercase tracking-[0.16em] text-[#8c5a1a]">Product Selling</div>
          </div>
        </div>

        <div className="space-x-3">
          <Link
            to="/login"
            className="rounded-full border border-[#d89c35] bg-white/65 px-5 py-2 text-sm font-semibold text-[#603400] backdrop-blur hover:bg-white"
          >
            {t("login")}
          </Link>
          <Link
            to="/signup"
            className="rounded-full bg-[#ef9f1c] px-5 py-2 text-sm font-semibold text-white shadow-[0_8px_20px_rgba(203,118,0,0.35)] hover:bg-[#e58f00]"
          >
            {t("get_started")}
          </Link>
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
              {t("hero_title")}
            </motion.h1>
            <p className="mt-5 text-lg font-medium text-[#6e4311] md:text-xl">Small app for small businesses</p>
            <p className="mt-3 max-w-xl text-base text-[#7f5420] md:text-lg">{t("hero_subtitle")}</p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to="/signup"
                className="rounded-full bg-[#ee9a0d] px-6 py-3 text-sm font-semibold text-white shadow-[0_10px_24px_rgba(190,105,0,0.35)]"
              >
                {t("get_started")}
              </Link>
              <Link
                to="/login"
                className="rounded-full border border-[#cd9033] bg-white/70 px-6 py-3 text-sm font-semibold text-[#653300]"
              >
                Sign in
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
              <div className="text-sm font-semibold uppercase tracking-[0.16em] text-[#8f5d1b]">Quidme Snapshot</div>
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
                    <img src={item.image} alt={item.title} className="h-24 w-full object-cover" />
                  </motion.div>
                  <div className="mt-2 text-xs font-medium leading-snug text-[#7f5120]">{item.title}</div>
                </motion.div>
              ))}
            </div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.55 }}
              className="mt-6 rounded-2xl bg-gradient-to-r from-[#f3a11c] via-[#ffb534] to-[#f5c45f] p-4 text-white"
            >
              <div className="text-sm font-medium text-white/90">Built for independent sellers and small businesses.</div>
              <div className="mt-2 text-xl font-bold">Products, subscriptions, and refunds in one place.</div>
            </motion.div>
          </motion.div>
        </section>
      </main>
    </div>
  );
};

export default LandingPage;
