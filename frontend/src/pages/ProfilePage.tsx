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
  const [scheduleLoading, setScheduleLoading] = useState(false);
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const [scheduleSuccess, setScheduleSuccess] = useState<string | null>(null);
  const [interval, setInterval] = useState<"daily" | "weekly" | "monthly" | "manual">("daily");
  const [weeklyAnchor, setWeeklyAnchor] = useState<"monday" | "tuesday" | "wednesday" | "thursday" | "friday" | "saturday" | "sunday">("monday");
  const [monthlyAnchor, setMonthlyAnchor] = useState(1);

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

  const handleSaveSchedule = async () => {
    setScheduleLoading(true);
    setScheduleError(null);
    setScheduleSuccess(null);
    try {
      await api.createPayoutSchedule({
        interval,
        weekly_anchor: interval === "weekly" ? weeklyAnchor : undefined,
        monthly_anchor: interval === "monthly" ? monthlyAnchor : undefined,
      });
      setScheduleSuccess(t("pages.account.payout_schedule_saved"));
    } catch (err: unknown) {
      setScheduleError(err instanceof Error ? err.message : t("pages.account.payout_schedule_failed"));
    } finally {
      setScheduleLoading(false);
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
          <div className="space-y-6">
            <div className="flex flex-col items-center justify-center py-4 text-center md:py-6">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50 ring-1 ring-emerald-200 md:h-20 md:w-20">
                <svg viewBox="0 0 24 24" className="h-8 w-8 text-emerald-600 md:h-10 md:w-10" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 6 9 17l-5-5" />
                </svg>
              </div>
              <div className="mt-4 text-xl font-semibold text-brand-navy md:mt-5 md:text-2xl">{t("pages.account.verified")}</div>
              <div className="mt-1 text-sm text-slate-500">{t("pages.account.verified_body")}</div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 md:p-5">
              <h3 className="text-lg font-semibold text-brand-navy">{t("pages.account.payout_schedule_title")}</h3>
              <p className="mt-1 text-sm text-slate-600">{t("pages.account.payout_schedule_body")}</p>

              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <div className="md:col-span-2">
                  <select
                    value={interval}
                    onChange={(e) => setInterval(e.target.value as "daily" | "weekly" | "monthly" | "manual")}
                    className="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-700"
                  >
                    <option value="daily">{t("pages.account.schedule_daily")}</option>
                    <option value="weekly">{t("pages.account.schedule_weekly")}</option>
                    <option value="monthly">{t("pages.account.schedule_monthly")}</option>
                    <option value="manual">{t("pages.account.schedule_manual")}</option>
                  </select>
                </div>

                {interval === "weekly" && (
                  <div className="md:col-span-2">
                    <label className="text-sm font-medium text-slate-700">{t("pages.account.weekly_anchor")}</label>
                    <select
                      value={weeklyAnchor}
                      onChange={(e) =>
                        setWeeklyAnchor(
                          e.target.value as
                            | "monday"
                            | "tuesday"
                            | "wednesday"
                            | "thursday"
                            | "friday"
                            | "saturday"
                            | "sunday"
                        )
                      }
                      className="mt-1 h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-700"
                    >
                      <option value="monday">{t("pages.account.day_monday")}</option>
                      <option value="tuesday">{t("pages.account.day_tuesday")}</option>
                      <option value="wednesday">{t("pages.account.day_wednesday")}</option>
                      <option value="thursday">{t("pages.account.day_thursday")}</option>
                      <option value="friday">{t("pages.account.day_friday")}</option>
                      <option value="saturday">{t("pages.account.day_saturday")}</option>
                      <option value="sunday">{t("pages.account.day_sunday")}</option>
                    </select>
                  </div>
                )}

                {interval === "monthly" && (
                  <div className="md:col-span-2">
                    <label className="text-sm font-medium text-slate-700">{t("pages.account.monthly_anchor")}</label>
                    <input
                      type="number"
                      min={1}
                      max={31}
                      value={monthlyAnchor}
                      onChange={(e) => setMonthlyAnchor(Number(e.target.value || 1))}
                      className="mt-1 h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-700"
                    />
                  </div>
                )}
              </div>

              <button
                onClick={handleSaveSchedule}
                className="mt-4 rounded-full bg-brand-sky px-5 py-2 text-sm font-semibold text-white"
                disabled={scheduleLoading}
              >
                {scheduleLoading ? t("pages.account.saving_schedule") : t("pages.account.save_schedule")}
              </button>
              {scheduleError && <div className="mt-3 text-sm text-red-500">{scheduleError}</div>}
              {scheduleSuccess && <div className="mt-3 text-sm text-emerald-600">{scheduleSuccess}</div>}
            </div>
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
