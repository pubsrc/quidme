import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { BarChart3, DollarSign, Home, LogOut, Menu, Settings, User, Users, X } from "lucide-react";
import { signOutWithCognito } from "../lib/auth";
import { LOCALE_STORAGE_KEY } from "../app/i18n";
import { replaceLocaleInPathname } from "../lib/localeRouting";
import { useLocaleNavigate } from "../lib/useLocaleNavigate";
import QuidmeLogo from "../components/QuidmeLogo";

const navItems = [
  {
    to: "dashboard",
    labelKey: "layouts.dashboard.nav.dashboard",
    icon: <Home className="h-8 w-8" />,
  },
  {
    to: "offerings",
    labelKey: "layouts.dashboard.nav.products",
    icon: <DollarSign className="h-8 w-8" />,
  },
  {
    to: "subscribers",
    labelKey: "layouts.dashboard.nav.subscribers",
    icon: <Users className="h-8 w-8" />,
  },
  {
    to: "transactions",
    labelKey: "layouts.dashboard.nav.transactions",
    icon: <BarChart3 className="h-8 w-8" />,
  },
  {
    to: "profile",
    labelKey: "layouts.dashboard.nav.account",
    icon: <User className="h-8 w-8" />,
  },
];

const DashboardLayout = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { localeNavigate } = useLocaleNavigate();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const currentLanguage = (i18n.resolvedLanguage || "en").startsWith("tr") ? "tr" : "en";

  const setLanguage = async (lang: "en" | "tr") => {
    await i18n.changeLanguage(lang);
    localStorage.setItem(LOCALE_STORAGE_KEY, lang);
    navigate(replaceLocaleInPathname(location.pathname, lang), { replace: true });
  };

  useEffect(() => {
    setMobileSidebarOpen(false);
  }, [location.pathname]);

  const handleLogout = async () => {
    try {
      await signOutWithCognito();
    } finally {
      localeNavigate("/login", { replace: true });
    }
  };

  return (
    <div className="h-svh overflow-hidden bg-slate-50">
      <div className="h-full md:flex">
        <aside className="hidden h-full w-[92px] shrink-0 flex-col items-center border-r border-slate-200 bg-white py-5 md:flex">
          <QuidmeLogo
            alt={t("layouts.dashboard.logo_alt")}
            containerClassName="mb-7 h-12 w-12"
            logoClassName="h-9 w-9"
          />

          <nav className="flex min-h-0 flex-1 flex-col items-center gap-3 overflow-y-auto">
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
              <Settings className="h-8 w-8" />
            </NavLink>
            <button
              type="button"
              onClick={handleLogout}
              title={t("layouts.dashboard.menu.logout")}
              className="flex h-12 w-12 items-center justify-center rounded-full text-slate-500 hover:bg-slate-100"
            >
              <LogOut className="h-8 w-8" />
            </button>
          </div>
        </aside>
        {mobileSidebarOpen && (
          <div className="fixed inset-0 z-40 md:hidden" role="dialog" aria-modal="true">
            <div className="absolute inset-0 bg-black/40" onClick={() => setMobileSidebarOpen(false)} />
            <aside className="absolute left-0 top-0 h-full w-72 border-r border-slate-200 bg-white p-5">
              <div className="mb-6 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <QuidmeLogo
                    alt={t("layouts.dashboard.logo_alt")}
                    containerClassName="h-9 w-9"
                    logoClassName="h-7 w-7"
                  />
                  <div className="text-lg font-semibold text-slate-800">{t("pages.landing.brand")}</div>
                </div>
                <button
                  type="button"
                  onClick={() => setMobileSidebarOpen(false)}
                  className="rounded-full p-2 text-slate-500 hover:bg-slate-100"
                  aria-label={t("layouts.dashboard.menu.close")}
                >
                  <X className="h-8 w-8" />
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
                  <Settings className="h-8 w-8" />
                  <span>{t("layouts.dashboard.nav.settings")}</span>
                </NavLink>
              </nav>
              <button
                type="button"
                onClick={handleLogout}
                className="mt-8 inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-600 hover:bg-slate-100"
              >
                <LogOut className="h-4 w-4" />
                {t("layouts.dashboard.menu.logout")}
              </button>
            </aside>
          </div>
        )}

        <main className="min-h-0 flex-1 overflow-y-auto p-4 md:p-8 lg:p-10">
          <div className="mb-4 md:hidden">
            <button
              type="button"
              onClick={() => setMobileSidebarOpen(true)}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700"
            >
              <Menu className="h-4 w-4" />
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
