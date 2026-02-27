import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { BarChart3, DollarSign, Home, LogOut, Menu, QrCode, Settings, User, Users, X } from "lucide-react";
import { signOutWithCognito } from "../lib/auth";
import { LOCALE_STORAGE_KEY } from "../app/i18n";
import { LOCALE_OPTIONS, replaceLocaleInPathname, resolveLocale, type AppLocale } from "../lib/localeRouting";
import { useLocaleNavigate } from "../lib/useLocaleNavigate";
import QuidmeLogo from "../components/QuidmeLogo";

const navItems = [
  {
    to: "quick-payments",
    labelKey: "layouts.dashboard.nav.quick_payments",
    icon: <QrCode className="h-8 w-8" />,
  },
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
  const [desktopSidebarHovered, setDesktopSidebarHovered] = useState(false);
  const [languageMenuOpen, setLanguageMenuOpen] = useState(false);
  const currentLanguage = resolveLocale(i18n.resolvedLanguage) ?? "en";
  const currentLanguageOption =
    LOCALE_OPTIONS.find((option) => option.code === currentLanguage) ?? LOCALE_OPTIONS[0];

  const setLanguage = async (lang: AppLocale) => {
    await i18n.changeLanguage(lang);
    localStorage.setItem(LOCALE_STORAGE_KEY, lang);
    navigate(replaceLocaleInPathname(location.pathname, lang), { replace: true });
    setLanguageMenuOpen(false);
  };

  useEffect(() => {
    setMobileSidebarOpen(false);
    setLanguageMenuOpen(false);
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
      <div className="relative h-full">
        <aside
          className={`sidebar-shell hidden absolute inset-y-0 left-0 z-20 flex-col border-r border-slate-200 bg-white py-5 transition-all duration-200 md:flex ${
            desktopSidebarHovered ? "w-[240px]" : "w-[92px]"
          }`}
          onMouseEnter={() => setDesktopSidebarHovered(true)}
          onMouseLeave={() => {
            setDesktopSidebarHovered(false);
            setLanguageMenuOpen(false);
          }}
        >
          <div className="relative mb-7 h-12 w-full">
            <QuidmeLogo
              alt={t("layouts.dashboard.logo_alt")}
              containerClassName="absolute left-[22px] h-12 w-12"
              logoClassName="h-9 w-9"
            />
          </div>

          <nav className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                title={t(item.labelKey)}
                className="relative block h-12 w-full"
              >
                {({ isActive }) => (
                  <>
                    <span
                      className={`absolute left-[22px] top-1/2 inline-flex h-12 w-12 -translate-y-1/2 items-center justify-center rounded-full transition ${
                        isActive ? "bg-emerald-500 text-white" : "text-slate-500 hover:bg-slate-100"
                      }`}
                    >
                      {item.icon}
                    </span>
                    <span
                      className={`absolute left-[76px] top-1/2 -translate-y-1/2 whitespace-nowrap text-sm font-medium text-slate-700 transition-all duration-150 ${
                        desktopSidebarHovered
                          ? "translate-x-0 opacity-100"
                          : "pointer-events-none -translate-x-1 opacity-0"
                      } ${isActive ? "text-emerald-700" : ""}`}
                    >
                      {t(item.labelKey)}
                    </span>
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          <div className="mt-4 flex flex-col gap-3">
            <div className="relative h-12 w-full">
              <button
                type="button"
                onClick={() => setLanguageMenuOpen((prev) => !prev)}
                title={t("layouts.dashboard.language.label")}
                className="relative block h-12 w-full text-left"
                aria-haspopup="menu"
                aria-expanded={languageMenuOpen}
              >
                <span className="absolute left-[22px] top-1/2 inline-flex h-12 w-12 -translate-y-1/2 items-center justify-center rounded-full text-2xl leading-none text-slate-500 transition hover:bg-slate-100">
                  {currentLanguageOption.flag}
                </span>
                <span
                  className={`absolute left-[76px] top-1/2 -translate-y-1/2 whitespace-nowrap text-sm font-medium text-slate-700 transition-all duration-150 ${
                    desktopSidebarHovered
                      ? "translate-x-0 opacity-100"
                      : "pointer-events-none -translate-x-1 opacity-0"
                  }`}
                >
                  {t("layouts.dashboard.language.label")}
                </span>
              </button>
              {languageMenuOpen && (
                <div
                  role="menu"
                  className="absolute bottom-[52px] left-[22px] z-30 max-h-64 w-[196px] overflow-y-auto rounded-xl border border-slate-200 bg-white p-1 shadow-lg"
                >
                  {LOCALE_OPTIONS.map((option) => {
                    const isCurrent = option.code === currentLanguage;
                    return (
                      <button
                        key={option.code}
                        type="button"
                        onClick={() => setLanguage(option.code)}
                        className={`flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-sm ${
                          isCurrent
                            ? "bg-emerald-50 font-semibold text-emerald-700"
                            : "text-slate-700 hover:bg-slate-100"
                        }`}
                      >
                        <span className="text-lg leading-none">{option.flag}</span>
                        <span>{t(option.labelKey)}</span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
            <NavLink
              to="settings"
              title={t("layouts.dashboard.nav.settings")}
              className="relative block h-12 w-full"
            >
              {({ isActive }) => (
                <>
                  <span
                    className={`absolute left-[22px] top-1/2 inline-flex h-12 w-12 -translate-y-1/2 items-center justify-center rounded-full transition ${
                      isActive ? "bg-emerald-500 text-white" : "text-slate-500 hover:bg-slate-100"
                    }`}
                  >
                    <Settings className="h-8 w-8" />
                  </span>
                  <span
                    className={`absolute left-[76px] top-1/2 -translate-y-1/2 whitespace-nowrap text-sm font-medium text-slate-700 transition-all duration-150 ${
                      desktopSidebarHovered
                        ? "translate-x-0 opacity-100"
                        : "pointer-events-none -translate-x-1 opacity-0"
                    } ${isActive ? "text-emerald-700" : ""}`}
                  >
                    {t("layouts.dashboard.nav.settings")}
                  </span>
                </>
              )}
            </NavLink>
            <button
              type="button"
              onClick={handleLogout}
              title={t("layouts.dashboard.menu.logout")}
              className="relative h-12 w-full"
            >
              <span className="absolute left-[22px] top-1/2 inline-flex h-12 w-12 -translate-y-1/2 items-center justify-center rounded-full text-slate-500 transition hover:bg-slate-100">
                <LogOut className="h-8 w-8" />
              </span>
              <span
                className={`absolute left-[76px] top-1/2 -translate-y-1/2 whitespace-nowrap text-sm font-medium text-slate-700 transition-all duration-150 ${
                  desktopSidebarHovered
                    ? "translate-x-0 opacity-100"
                    : "pointer-events-none -translate-x-1 opacity-0"
                }`}
              >
                {t("layouts.dashboard.menu.logout")}
              </span>
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
                    onChange={(e) => setLanguage(e.target.value as AppLocale)}
                    aria-label={t("layouts.dashboard.language.label")}
                    className="mt-2 h-11 w-full rounded-lg border border-slate-200 bg-white px-3 text-base text-slate-700 outline-none"
                  >
                    {LOCALE_OPTIONS.map((option) => (
                      <option key={option.code} value={option.code}>
                        {option.flag} {t(option.labelKey)}
                      </option>
                    ))}
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

        <main className="h-full min-h-0 overflow-y-auto p-4 md:pl-[112px] md:pr-8 md:pt-8 md:pb-8 lg:pr-10 lg:pt-10 lg:pb-10">
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
