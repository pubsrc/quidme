import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { signOutWithCognito } from "../lib/auth";
import { LOCALE_STORAGE_KEY } from "../app/i18n";

const navItems = [
  {
    to: "dashboard",
    labelKey: "layouts.dashboard.nav.dashboard",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M3 12 12 4l9 8" />
        <path d="M5 10v10h14V10" />
      </svg>
    ),
  },
  {
    to: "payment-links",
    labelKey: "layouts.dashboard.nav.products",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 2v20" />
        <path d="M17 6.5a4.5 4.5 0 0 0-5-2.5 4 4 0 0 0 0 8 4 4 0 0 1 0 8 4.5 4.5 0 0 1-5-2.5" />
      </svg>
    ),
  },
  {
    to: "transactions",
    labelKey: "layouts.dashboard.nav.transactions",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M3 3v18h18" />
        <path d="m7 15 4-4 3 3 5-6" />
      </svg>
    ),
  },
  {
    to: "profile",
    labelKey: "layouts.dashboard.nav.account",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M20 21a8 8 0 0 0-16 0" />
        <circle cx="12" cy="8" r="4" />
      </svg>
    ),
  },
];

const DashboardLayout = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const currentLanguage = (i18n.resolvedLanguage || "en").startsWith("tr") ? "tr" : "en";

  const setLanguage = async (lang: "en" | "tr") => {
    await i18n.changeLanguage(lang);
    localStorage.setItem(LOCALE_STORAGE_KEY, lang);
  };

  useEffect(() => {
    setMobileSidebarOpen(false);
  }, [location.pathname]);

  const handleLogout = async () => {
    try {
      await signOutWithCognito();
    } finally {
      navigate("/login", { replace: true });
    }
  };

  return (
    <div className="h-screen overflow-hidden bg-[#f5f7fb]">
      <div className="flex h-full">
        <aside className="hidden h-full w-[92px] flex-col items-center border-r border-slate-200 bg-[#f8fafc] py-5 md:flex">
          <div className="mb-7 flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 ring-1 ring-amber-300">
            <img src="/quidme-logo.svg" alt={t("layouts.dashboard.logo_alt")} className="h-9 w-9" />
          </div>

          <nav className="flex flex-1 flex-col items-center gap-3">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                title={t(item.labelKey)}
                className={({ isActive }) =>
                  `flex h-12 w-12 items-center justify-center rounded-full transition ${
                    isActive ? "bg-emerald-500 text-white" : "text-slate-500 hover:bg-slate-100"
                  }`
                }
              >
                {item.icon}
              </NavLink>
            ))}
          </nav>

          <div className="mt-4 flex flex-col items-center gap-3">
            <div className="flex flex-col items-center gap-1">
              <select
                value={currentLanguage}
                onChange={(e) => setLanguage(e.target.value as "en" | "tr")}
                aria-label={t("layouts.dashboard.language.label")}
                className="h-8 w-14 rounded-md border border-slate-200 bg-white px-1 text-center text-xs text-slate-700 outline-none"
              >
                <option value="en">🇬🇧</option>
                <option value="tr">🇹🇷</option>
              </select>
            </div>
            <NavLink
              to="settings"
              title={t("layouts.dashboard.nav.settings")}
              className={({ isActive }) =>
                `flex h-12 w-12 items-center justify-center rounded-full transition ${
                  isActive ? "bg-emerald-500 text-white" : "text-slate-500 hover:bg-slate-100"
                }`
              }
            >
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z" />
                <path d="M19.4 15a7.9 7.9 0 0 0 .1-1 7.9 7.9 0 0 0-.1-1l2-1.5-2-3.5-2.4 1a8.5 8.5 0 0 0-1.7-1l-.4-2.6h-4l-.4 2.6a8.5 8.5 0 0 0-1.7 1l-2.4-1-2 3.5 2 1.5a7.9 7.9 0 0 0-.1 1 7.9 7.9 0 0 0 .1 1l-2 1.5 2 3.5 2.4-1a8.5 8.5 0 0 0 1.7 1l.4 2.6h4l.4-2.6a8.5 8.5 0 0 0 1.7-1l2.4 1 2-3.5-2-1.5Z" />
              </svg>
            </NavLink>
            <button
              type="button"
              onClick={handleLogout}
              title={t("layouts.dashboard.menu.logout")}
              className="flex h-12 w-12 items-center justify-center rounded-full text-slate-500 hover:bg-slate-100"
            >
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <path d="M16 17l5-5-5-5" />
                <path d="M21 12H9" />
              </svg>
            </button>
          </div>
        </aside>
        {mobileSidebarOpen && (
          <div className="fixed inset-0 z-40 md:hidden" role="dialog" aria-modal="true">
            <div className="absolute inset-0 bg-black/40" onClick={() => setMobileSidebarOpen(false)} />
            <aside className="absolute left-0 top-0 h-full w-72 border-r border-slate-200 bg-white p-5">
              <div className="mb-6 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <img src="/quidme-logo.svg" alt={t("layouts.dashboard.logo_alt")} className="h-7 w-7" />
                  <div className="text-lg font-semibold text-slate-800">{t("pages.landing.brand")}</div>
                </div>
                <button
                  type="button"
                  onClick={() => setMobileSidebarOpen(false)}
                  className="rounded-full p-2 text-slate-500 hover:bg-slate-100"
                  aria-label={t("layouts.dashboard.menu.close")}
                >
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 6 6 18M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <nav className="space-y-2">
                <div className="mb-2 rounded-xl bg-slate-50 p-2">
                  <div className="px-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                    {t("layouts.dashboard.language.label")}
                  </div>
                  <select
                    value={currentLanguage}
                    onChange={(e) => setLanguage(e.target.value as "en" | "tr")}
                    aria-label={t("layouts.dashboard.language.label")}
                    className="mt-2 h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none"
                  >
                    <option value="en">🇬🇧 {t("layouts.dashboard.language.english")}</option>
                    <option value="tr">🇹🇷 {t("layouts.dashboard.language.turkish")}</option>
                  </select>
                </div>
                {navItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium ${
                        isActive ? "bg-emerald-500 text-white" : "text-slate-600 hover:bg-slate-100"
                      }`
                    }
                  >
                    {item.icon}
                    <span>{t(item.labelKey)}</span>
                  </NavLink>
                ))}
                <NavLink
                  to="settings"
                  className={({ isActive }) =>
                    `mt-2 flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium ${
                      isActive ? "bg-emerald-500 text-white" : "text-slate-600 hover:bg-slate-100"
                    }`
                  }
                >
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z" />
                    <path d="M19.4 15a7.9 7.9 0 0 0 .1-1 7.9 7.9 0 0 0-.1-1l2-1.5-2-3.5-2.4 1a8.5 8.5 0 0 0-1.7-1l-.4-2.6h-4l-.4 2.6a8.5 8.5 0 0 0-1.7 1l-2.4-1-2 3.5 2 1.5a7.9 7.9 0 0 0-.1 1 7.9 7.9 0 0 0 .1 1l-2 1.5 2 3.5 2.4-1a8.5 8.5 0 0 0 1.7 1l.4 2.6h4l.4-2.6a8.5 8.5 0 0 0 1.7-1l2.4 1 2-3.5-2-1.5Z" />
                  </svg>
                  <span>{t("layouts.dashboard.nav.settings")}</span>
                </NavLink>
              </nav>
              <button
                type="button"
                onClick={handleLogout}
                className="mt-8 inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-600 hover:bg-slate-100"
              >
                <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <path d="M16 17l5-5-5-5" />
                  <path d="M21 12H9" />
                </svg>
                {t("layouts.dashboard.menu.logout")}
              </button>
            </aside>
          </div>
        )}

        <main className="h-full flex-1 overflow-y-auto p-4 md:p-8 lg:p-10">
          <div className="mb-4 md:hidden">
            <button
              type="button"
              onClick={() => setMobileSidebarOpen(true)}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700"
            >
              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 6h16M4 12h16M4 18h16" />
              </svg>
              {t("layouts.dashboard.menu.open")}
            </button>
          </div>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
