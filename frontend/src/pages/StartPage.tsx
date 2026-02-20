import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../lib/api";
import { signOutWithCognito } from "../lib/auth";
import { useLocaleNavigate } from "../lib/useLocaleNavigate";

/**
 * Start page: create Stripe Connect account.
 * No API calls until user clicks the button (authorization gate is backend 403).
 */
const StartPage = () => {
  const { t } = useTranslation();
  const { localeNavigate } = useLocaleNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogout = async () => {
    try {
      await signOutWithCognito();
      localeNavigate("/", { replace: true });
    } catch {
      localeNavigate("/", { replace: true });
    }
  };

  const handleStart = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.connectAccount();
      localeNavigate("/app/dashboard", { replace: true });
    } catch (err) {
      setError(t("pages.start.errors.create_account_failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-lg rounded-2xl bg-white p-8 shadow">
        <h1 className="text-2xl font-semibold text-brand-navy">{t("pages.start.title")}</h1>
        <p className="mt-3 text-sm text-slate-600">{t("pages.start.subtitle")}</p>

        <div className="mt-6 flex items-center gap-3 rounded-xl border border-slate-200 p-4">
          <div className="text-2xl">🇬🇧</div>
          <div>
            <div className="text-sm font-semibold">{t("pages.start.country")}</div>
            <div className="text-xs text-slate-500">{t("pages.start.account_type")}</div>
          </div>
        </div>

        {error && <div className="mt-4 text-sm text-red-500">{error}</div>}

        <div className="mt-6 flex justify-between">
          <button
            onClick={handleLogout}
            className="rounded-full border border-slate-300 px-5 py-2 text-sm text-slate-600"
            disabled={loading}
          >
            {t("pages.start.logout")}
          </button>
          <div className="flex gap-3">
            <button
              onClick={() => localeNavigate("/")}
              className="rounded-full border border-slate-300 px-5 py-2 text-sm"
              disabled={loading}
            >
              {t("pages.start.cancel")}
            </button>
            <button
              onClick={handleStart}
              className="rounded-full bg-brand-sky px-5 py-2 text-sm font-semibold text-white"
              disabled={loading}
            >
              {loading ? t("pages.start.starting") : t("pages.start.ok")}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StartPage;
