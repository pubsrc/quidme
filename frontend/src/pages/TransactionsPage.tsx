import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, type TransactionItem } from "../lib/api";

const currencySymbol = (code?: string) => {
  const value = (code || "gbp").toLowerCase();
  if (value === "gbp") return "£";
  if (value === "usd") return "$";
  if (value === "eur") return "€";
  return "";
};

const formatMoney = (amountMinor: number, currency?: string) => `${currencySymbol(currency)}${(amountMinor / 100).toFixed(2)}`;

const formatTimeAgo = (isoDate: string, t: (key: string, options?: Record<string, unknown>) => string) => {
  const date = new Date(isoDate);
  if (Number.isNaN(date.getTime())) return isoDate;
  const diffMs = Date.now() - date.getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return t("pages.transactions.just_now");
  if (minutes < 60) return t("pages.transactions.minutes_ago", { count: minutes });
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return t("pages.transactions.hours_ago", { count: hours });
  const days = Math.floor(hours / 24);
  if (days < 365) return t("pages.transactions.days_ago", { count: days });
  const years = Math.floor(days / 365);
  return t("pages.transactions.years_ago", { count: years });
};

const TransactionsPage = () => {
  const { t } = useTranslation();
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [refundLoading, setRefundLoading] = useState<string | null>(null);
  const [refundConfirmId, setRefundConfirmId] = useState<string | null>(null);

  const fetchTransactions = async (withDateFilter: boolean) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.listTransactions(
        withDateFilter && startDate && endDate
          ? { date_start: startDate, date_end: endDate, limit: 100 }
          : { limit: 100 }
      );
      setTransactions(response.items || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t("pages.transactions.fetch_failed"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions(false);
  }, []);

  const visibleRows = useMemo(() => transactions, [transactions]);

  const handleRefund = async (id: string) => {
    setRefundLoading(id);
    setError(null);
    try {
      await api.refund(id);
      setTransactions((prev) =>
        prev.map((tx) => (tx.id === id ? { ...tx, refunded: true, refund_status: "refunded" } : tx))
      );
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t("pages.transactions.refund_failed"));
    } finally {
      setRefundLoading(null);
      setRefundConfirmId(null);
    }
  };

  return (
    <div className="space-y-6 md:space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">{t("pages.transactions.title")}</h2>
        <p className="mt-2 text-base text-slate-500 md:text-lg">{t("pages.transactions.subtitle")}</p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4 md:rounded-3xl md:p-5">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-500">{t("pages.transactions.from")}</label>
            <input
              type="date"
              className="mt-1 rounded-xl border border-slate-200 px-3 py-2 text-sm md:px-4 md:text-base"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-500">{t("pages.transactions.to")}</label>
            <input
              type="date"
              className="mt-1 rounded-xl border border-slate-200 px-3 py-2 text-sm md:px-4 md:text-base"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
          <button
            type="button"
            onClick={() => fetchTransactions(true)}
            className="rounded-xl bg-amber-500 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-600 md:px-5 md:py-2.5 md:text-base"
            disabled={loading}
          >
            {t("pages.transactions.apply")}
          </button>
          <button
            type="button"
            onClick={() => {
              setStartDate("");
              setEndDate("");
              fetchTransactions(false);
            }}
            className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 md:px-5 md:py-2.5 md:text-base"
            disabled={loading}
          >
            {t("pages.transactions.reset")}
          </button>
        </div>
      </div>

      {error && <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-base text-red-700">{error}</div>}

      <div className="rounded-2xl border border-slate-200 bg-white p-4 md:rounded-3xl md:p-6">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="text-left text-sm text-slate-500 md:text-lg">
                <th className="border-b border-slate-200 pb-4 pr-4 font-medium">{t("pages.transactions.customer")}</th>
                <th className="border-b border-slate-200 pb-4 pr-4 font-medium">{t("pages.transactions.status")}</th>
                <th className="border-b border-slate-200 pb-4 pr-4 font-medium">{t("pages.transactions.date")}</th>
                <th className="border-b border-slate-200 pb-4 text-right font-medium">{t("pages.transactions.amount")}</th>
              </tr>
            </thead>
            <tbody>
              {!loading &&
                visibleRows.map((tx) => {
                  const statusCode = tx.refunded ? "refunded" : (tx.status?.toLowerCase() || "pending");
                  const statusLabel =
                    statusCode === "succeeded"
                      ? t("pages.transactions.status_succeeded")
                      : statusCode === "refunded"
                      ? t("pages.transactions.status_refunded")
                      : statusCode === "failed"
                      ? t("pages.transactions.status_failed")
                      : statusCode === "pending"
                      ? t("pages.transactions.status_pending")
                      : tx.status || t("pages.transactions.status_unknown");
                  const statusClass =
                    statusCode === "succeeded"
                      ? "bg-emerald-100 text-emerald-700"
                      : statusCode === "refunded"
                      ? "bg-slate-200 text-slate-700"
                      : statusCode === "failed"
                      ? "bg-red-100 text-red-700"
                      : "bg-sky-100 text-sky-700";
                  return (
                    <tr key={tx.id}>
                      <td className="border-b border-slate-100 py-5 pr-4 align-top">
                        <div className="text-base font-medium text-slate-900 md:text-xl">{tx.customer_name || t("pages.transactions.default_customer")}</div>
                        <div className="text-sm text-slate-500 md:text-base">{tx.customer_email || "—"}</div>
                      </td>
                      <td className="border-b border-slate-100 py-5 pr-4 align-top">
                        <div className="flex items-center gap-2">
                          <span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize md:px-3 md:text-lg ${statusClass}`}>{statusLabel}</span>
                          {!tx.refunded && (
                            <button
                              type="button"
                              onClick={() => setRefundConfirmId(tx.id)}
                              className="rounded-full border border-amber-300 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700 hover:bg-amber-100 md:px-3 md:text-sm"
                              disabled={refundLoading === tx.id}
                            >
                              {refundLoading === tx.id ? t("pages.transactions.refunding") : t("pages.transactions.refund")}
                            </button>
                          )}
                        </div>
                      </td>
                      <td className="border-b border-slate-100 py-5 pr-4 align-top text-sm text-slate-700 md:text-lg">
                        {formatTimeAgo(tx.created_at, t)}
                      </td>
                      <td className="border-b border-slate-100 py-5 text-right align-top text-base font-semibold text-slate-900 md:text-xl">
                        {formatMoney(tx.amount, tx.currency)}
                      </td>
                    </tr>
                  );
                })}
              {!loading && visibleRows.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-10 text-center text-lg text-slate-500">
                    {t("pages.transactions.no_transactions")}
                  </td>
                </tr>
              )}
              {loading && (
                <tr>
                  <td colSpan={4} className="py-10 text-center text-lg text-slate-500">
                    {t("pages.transactions.loading_transactions")}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {refundConfirmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40" onClick={() => setRefundConfirmId(null)} />
          <div className="relative w-full max-w-sm rounded-2xl bg-white p-5 shadow-xl">
            <h3 className="text-lg font-semibold text-slate-900">{t("pages.transactions.confirm_refund_title")}</h3>
            <p className="mt-2 text-sm text-slate-600">
              {t("pages.transactions.confirm_refund_text")}
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setRefundConfirmId(null)}
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                disabled={refundLoading === refundConfirmId}
              >
                {t("pages.transactions.cancel")}
              </button>
              <button
                type="button"
                onClick={() => handleRefund(refundConfirmId)}
                className="rounded-lg bg-amber-500 px-3 py-2 text-sm font-semibold text-white hover:bg-amber-600"
                disabled={refundLoading === refundConfirmId}
              >
                {refundLoading === refundConfirmId ? t("pages.transactions.refunding") : t("pages.transactions.confirm_refund")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TransactionsPage;
