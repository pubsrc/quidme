import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Check } from "lucide-react";
import { api, type TransactionItem } from "../lib/api";
import { useAccountStatus } from "../lib/useAccountStatus";
import { useLocaleNavigate } from "../lib/useLocaleNavigate";

const currencySymbol = (code?: string) => {
  const value = (code || "gbp").toLowerCase();
  if (value === "gbp") return "£";
  if (value === "usd") return "$";
  if (value === "eur") return "€";
  return "";
};

const formatMoney = (amountMinor: number, currency?: string) => `${currencySymbol(currency)}${(amountMinor / 100).toFixed(2)}`;

const formatTimeAgo = (isoDate: string, t: (key: string, options?: Record<string, unknown>) => string) => {
  const d = new Date(isoDate);
  if (Number.isNaN(d.getTime())) return isoDate;
  const diffMs = Date.now() - d.getTime();
  const min = Math.floor(diffMs / 60000);
  if (min < 1) return t("pages.dashboard.just_now");
  if (min < 60) return min === 1 ? t("pages.dashboard.minutes_ago", { count: min }) : t("pages.dashboard.minutes_ago_plural", { count: min });
  const hrs = Math.floor(min / 60);
  if (hrs < 24) return hrs === 1 ? t("pages.dashboard.hours_ago", { count: hrs }) : t("pages.dashboard.hours_ago_plural", { count: hrs });
  const days = Math.floor(hrs / 24);
  if (days < 30) return days === 1 ? t("pages.dashboard.days_ago", { count: days }) : t("pages.dashboard.days_ago_plural", { count: days });
  const years = Math.floor(days / 365);
  if (years >= 1) return years === 1 ? t("pages.dashboard.years_ago", { count: years }) : t("pages.dashboard.years_ago_plural", { count: years });
  return d.toLocaleDateString();
};

const DashboardPage = () => {
  const { t } = useTranslation();
  const { localeNavigate } = useLocaleNavigate();
  const { account, status, refresh } = useAccountStatus();
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [transferLoading, setTransferLoading] = useState(false);
  const [transferError, setTransferError] = useState<string | null>(null);
  const [showOnboardingDialog, setShowOnboardingDialog] = useState(false);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const response = await api.listTransactions({ limit: 10 });
        setTransactions(response.items || []);
      } catch {
        setTransactions([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const totals = useMemo(() => {
    const totalEarningsMinor =
      account?.earnings
        ? Object.values(account.earnings).reduce((acc, amount) => acc + amount, 0)
        : 0;
    const pendingEarningsMinor =
      account?.pending_earnings
        ? Object.values(account.pending_earnings).reduce((acc, amount) => acc + amount, 0)
        : 0;
    const mainCurrency = account?.pending_earnings
      ? Object.keys(account.pending_earnings)[0]
      : account?.earnings
      ? Object.keys(account.earnings)[0]
      : "gbp";
    return { totalEarningsMinor, pendingEarningsMinor, mainCurrency };
  }, [account]);

  const recentRows = useMemo(() => transactions.slice(0, 4), [transactions]);

  const handleTransfer = async () => {
    if (!status.payouts_enabled) {
      setShowOnboardingDialog(true);
      return;
    }
    setTransferError(null);
    setTransferLoading(true);
    try {
      await api.createPayouts();
      await refresh();
    } catch (err) {
      setTransferError(err instanceof Error ? err.message : t("pages.dashboard.transfer_failed"));
    } finally {
      setTransferLoading(false);
    }
  };

  return (
    <div className="space-y-6 md:space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">{t("pages.dashboard.title")}</h1>
        <p className="mt-2 text-base text-slate-500 md:text-lg">{t("pages.dashboard.subtitle")}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4 md:rounded-3xl md:px-6 md:py-5">
          <div className="text-base text-slate-600 md:text-xl">{t("pages.dashboard.total_earnings")}</div>
          <div className="mt-2 text-3xl font-bold text-slate-900 md:text-4xl">{formatMoney(totals.totalEarningsMinor, totals.mainCurrency)}</div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4 md:rounded-3xl md:px-6 md:py-5">
          <div className="text-base text-slate-600 md:text-xl">{t("pages.dashboard.pending_earnings")}</div>
          <div className="mt-2 text-3xl font-bold text-slate-900 md:text-4xl">
            {formatMoney(totals.pendingEarningsMinor, totals.mainCurrency)}
          </div>
          <button
            type="button"
            onClick={handleTransfer}
            disabled={transferLoading || totals.pendingEarningsMinor <= 0}
            className="mt-4 rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50 md:rounded-2xl md:px-5 md:py-2.5 md:text-base"
          >
            {transferLoading ? t("pages.dashboard.transferring") : t("pages.dashboard.transfer_to_account")}
          </button>
          {transferError && <div className="mt-2 text-sm font-medium text-red-600">{transferError}</div>}
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4 md:rounded-3xl md:px-6 md:py-5 md:col-span-2 xl:col-span-1">
          <div className="text-base text-slate-600 md:text-xl">{t("pages.dashboard.account_status")}</div>
          <div className={`mt-2 text-3xl font-bold md:text-4xl ${status.payouts_enabled ? "text-emerald-600" : "text-amber-600"}`}>
            {status.payouts_enabled ? t("pages.dashboard.verified") : t("pages.dashboard.pending")}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4 md:rounded-3xl md:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 md:text-3xl">{t("pages.dashboard.recent_transactions")}</h2>
            <p className="mt-2 text-base text-slate-500 md:text-lg">{t("pages.dashboard.recent_subtitle")}</p>
          </div>
          <button
            type="button"
            onClick={() => localeNavigate("/app/transactions")}
            className="rounded-xl bg-amber-500 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-600 md:rounded-2xl md:px-6 md:py-3 md:text-lg"
          >
            {t("pages.dashboard.view_all")}
          </button>
        </div>

        <div className="mt-7 overflow-x-auto">
          <table className="min-w-full border-separate border-spacing-y-0">
            <thead>
              <tr className="text-left text-sm text-slate-500 md:text-xl">
                <th className="border-b border-slate-200 pb-3 pr-4">{t("pages.dashboard.customer")}</th>
                <th className="border-b border-slate-200 pb-3 pr-4">{t("pages.dashboard.status")}</th>
                <th className="border-b border-slate-200 pb-3 pr-4">{t("pages.dashboard.date")}</th>
                <th className="border-b border-slate-200 pb-3 text-right">{t("pages.dashboard.amount")}</th>
              </tr>
            </thead>
            <tbody>
              {!loading &&
                recentRows.map((tx) => {
                  const customer = tx.customer_name || t("pages.dashboard.default_customer");
                  const email = tx.customer_email || "—";
                  const statusCode = tx.refunded ? "refunded" : (tx.status?.toLowerCase() || "pending");
                  const statusLabel =
                    statusCode === "succeeded"
                      ? t("pages.dashboard.status_succeeded")
                      : statusCode === "refunded"
                      ? t("pages.dashboard.status_refunded")
                      : statusCode === "failed"
                      ? t("pages.dashboard.status_failed")
                      : statusCode === "pending"
                      ? t("pages.dashboard.status_pending")
                      : tx.status || t("pages.dashboard.status_unknown");
                  const statusClass =
                    statusCode === "succeeded"
                      ? "bg-emerald-100 text-emerald-700"
                      : statusCode === "refunded"
                      ? "bg-slate-200 text-slate-700"
                      : statusCode === "failed"
                      ? "bg-red-100 text-red-700"
                      : "bg-sky-100 text-sky-700";

                  return (
                    <tr key={tx.id} className="text-sm text-slate-800 md:text-lg">
                      <td className="border-b border-slate-100 py-4 pr-4">
                        <div className="text-base font-semibold md:text-xl">{customer}</div>
                        <div className="text-sm text-slate-500 md:text-lg">{email}</div>
                      </td>
                      <td className="border-b border-slate-100 py-4 pr-4">
                        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize md:px-3 md:text-base ${statusClass}`}>
                          {statusLabel}
                        </span>
                      </td>
                      <td className="border-b border-slate-100 py-4 pr-4 text-sm md:text-lg">{formatTimeAgo(tx.created_at, t)}</td>
                      <td className="border-b border-slate-100 py-4 text-right text-base font-semibold md:text-xl">
                        {formatMoney(tx.amount, tx.currency)}
                      </td>
                    </tr>
                  );
                })}

              {!loading && recentRows.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-xl text-slate-500">
                    {t("pages.dashboard.no_transactions")}
                  </td>
                </tr>
              )}
              {loading && (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-xl text-slate-500">
                    {t("pages.dashboard.loading_transactions")}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showOnboardingDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-slate-900/55"
            onClick={() => setShowOnboardingDialog(false)}
          />
          <div className="relative w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl md:rounded-3xl">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100">
              <Check className="h-9 w-9 text-emerald-600" aria-hidden="true" />
            </div>
            <p className="text-center text-base font-medium text-slate-800 md:text-lg">
              {t("pages.dashboard.transfer_onboarding_required")}
            </p>
            <button
              type="button"
              className="mt-5 w-full rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 md:text-base"
              onClick={() => {
                setShowOnboardingDialog(false);
                localeNavigate("/app/profile");
              }}
            >
              {t("pages.dashboard.okay")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
