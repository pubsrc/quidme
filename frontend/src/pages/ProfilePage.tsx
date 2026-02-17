import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../lib/api";
import { useAccountStatus } from "../lib/useAccountStatus";

const formatEarnings = (pending_earnings: Record<string, number> | undefined): string => {
  if (!pending_earnings || Object.keys(pending_earnings).length === 0) return "£0.00";
  const parts = Object.entries(pending_earnings).map(([currency, amount]) => {
    const value = (amount / 100).toFixed(2);
    const symbol = currency.toUpperCase() === "GBP" ? "£" : currency.toUpperCase() === "USD" ? "$" : currency.toUpperCase() + " ";
    return `${symbol}${value}`;
  });
  return parts.join(" / ");
};

const ProfilePage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { account, status, isLoading } = useAccountStatus();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasAccount = Boolean(status?.has_connected_account);
  const isVerified = Boolean(status?.payouts_enabled);
  const needsOnboarding = hasAccount && !isVerified;

  const handleStartOnboarding = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.createOnboardingLink();
      window.location.href = response.onboarding_url;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t("pages.account.onboarding_failed"));
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-semibold text-brand-navy md:text-4xl">{t("pages.account.title")}</h2>
        <p className="text-sm text-slate-500 md:text-base">{t("pages.account.subtitle")}</p>
      </div>

      <div className="rounded-2xl bg-white p-4 shadow md:p-6">
        {isLoading ? (
          <div className="text-sm text-slate-500">{t("pages.account.loading_status")}</div>
        ) : !hasAccount ? (
          <div>
            <div className="text-sm text-slate-500">{t("pages.account.status")}</div>
            <div className="text-lg font-semibold">{t("pages.account.connected_required")}</div>
            <button
              onClick={() => navigate("/start")}
              className="mt-4 rounded-full bg-brand-sky px-5 py-2 text-sm font-semibold text-white"
            >
              {t("pages.account.start_onboarding")}
            </button>
          </div>
        ) : isVerified ? (
          <div className="flex flex-col items-center justify-center py-8 text-center md:py-10">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50 ring-1 ring-emerald-200 md:h-20 md:w-20">
              <svg viewBox="0 0 24 24" className="h-8 w-8 text-emerald-600 md:h-10 md:w-10" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 6 9 17l-5-5" />
              </svg>
            </div>
            <div className="mt-4 text-xl font-semibold text-brand-navy md:mt-5 md:text-2xl">{t("pages.account.verified")}</div>
            <div className="mt-1 text-sm text-slate-500">{t("pages.account.verified_body")}</div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="text-3xl font-bold tracking-tight text-brand-navy md:text-4xl">
              {formatEarnings(account?.pending_earnings)}
            </div>
            <div className="mt-1 text-sm font-medium text-slate-500">{t("pages.account.earnings")}</div>
            <p className="mt-6 max-w-sm text-slate-600">
              {t("pages.account.onboarding_body")}
            </p>
            <button
              onClick={handleStartOnboarding}
              className="mt-8 rounded-full bg-green-600 px-6 py-3 text-base font-semibold text-white shadow hover:bg-green-700 md:px-8 md:py-4 md:text-lg"
              disabled={loading}
            >
              {loading ? t("pages.account.opening") : t("pages.account.start_onboarding")}
            </button>
            {error && <div className="mt-4 text-sm text-red-500">{error}</div>}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfilePage;
