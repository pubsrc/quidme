import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type TransactionItem } from "../lib/api";
import { useAccountStatus } from "../lib/useAccountStatus";

const currencySymbol = (code?: string) => {
  const value = (code || "gbp").toLowerCase();
  if (value === "gbp") return "£";
  if (value === "usd") return "$";
  if (value === "eur") return "€";
  return "";
};

const formatMoney = (amountMinor: number, currency?: string) => `${currencySymbol(currency)}${(amountMinor / 100).toFixed(2)}`;

const formatTimeAgo = (isoDate: string) => {
  const d = new Date(isoDate);
  if (Number.isNaN(d.getTime())) return isoDate;
  const diffMs = Date.now() - d.getTime();
  const min = Math.floor(diffMs / 60000);
  if (min < 1) return "just now";
  if (min < 60) return `${min} minute${min === 1 ? "" : "s"} ago`;
  const hrs = Math.floor(min / 60);
  if (hrs < 24) return `${hrs} hour${hrs === 1 ? "" : "s"} ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days} day${days === 1 ? "" : "s"} ago`;
  const years = Math.floor(days / 365);
  if (years >= 1) return `over ${years} year${years === 1 ? "" : "s"} ago`;
  return d.toLocaleDateString();
};

const DashboardPage = () => {
  const navigate = useNavigate();
  const { account, status } = useAccountStatus();
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [loading, setLoading] = useState(true);

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
    const succeeded = transactions.filter((tx) => tx.status?.toLowerCase() === "succeeded");
    const totalEarnings = succeeded.reduce((acc, tx) => acc + tx.amount, 0);
    const pendingEarningsMinor =
      account?.pending_earnings
        ? Object.values(account.pending_earnings).reduce((acc, amount) => acc + amount, 0)
        : 0;
    const mainCurrency = account?.pending_earnings ? Object.keys(account.pending_earnings)[0] : "gbp";
    return { totalEarnings, pendingEarningsMinor, mainCurrency };
  }, [transactions, account]);

  const recentRows = useMemo(() => transactions.slice(0, 4), [transactions]);

  return (
    <div className="space-y-6 md:space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">Dashboard</h1>
        <p className="mt-2 text-base text-slate-500 md:text-lg">A quick overview of your product sales activity.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4 md:rounded-3xl md:px-6 md:py-5">
          <div className="text-base text-slate-600 md:text-xl">Total Earnings</div>
          <div className="mt-2 text-3xl font-bold text-slate-900 md:text-4xl">{formatMoney(totals.totalEarnings, totals.mainCurrency)}</div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4 md:rounded-3xl md:px-6 md:py-5">
          <div className="text-base text-slate-600 md:text-xl">Pending Earnings</div>
          <div className="mt-2 text-3xl font-bold text-slate-900 md:text-4xl">
            {formatMoney(totals.pendingEarningsMinor, totals.mainCurrency)}
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4 md:rounded-3xl md:px-6 md:py-5 md:col-span-2 xl:col-span-1">
          <div className="text-base text-slate-600 md:text-xl">Account Status</div>
          <div className={`mt-2 text-3xl font-bold md:text-4xl ${status.payouts_enabled ? "text-emerald-600" : "text-amber-600"}`}>
            {status.payouts_enabled ? "Verified" : "Pending"}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4 md:rounded-3xl md:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 md:text-3xl">Recent Transactions</h2>
            <p className="mt-2 text-base text-slate-500 md:text-lg">A log of your most recent sales.</p>
          </div>
          <button
            type="button"
            onClick={() => navigate("/app/transactions")}
            className="rounded-xl bg-amber-500 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-600 md:rounded-2xl md:px-6 md:py-3 md:text-lg"
          >
            View All
          </button>
        </div>

        <div className="mt-7 overflow-x-auto">
          <table className="min-w-full border-separate border-spacing-y-0">
            <thead>
              <tr className="text-left text-sm text-slate-500 md:text-xl">
                <th className="border-b border-slate-200 pb-3 pr-4">Customer</th>
                <th className="border-b border-slate-200 pb-3 pr-4">Status</th>
                <th className="border-b border-slate-200 pb-3 pr-4">Date</th>
                <th className="border-b border-slate-200 pb-3 text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {!loading &&
                recentRows.map((tx) => {
                  const customer = tx.customer_name || "Customer";
                  const email = tx.customer_email || "—";
                  const statusKey = tx.refunded ? "refunded" : tx.status?.toLowerCase() || "pending";
                  const statusClass =
                    statusKey === "succeeded"
                      ? "bg-emerald-100 text-emerald-700"
                      : statusKey === "refunded"
                      ? "bg-slate-200 text-slate-700"
                      : "bg-sky-100 text-sky-700";

                  return (
                    <tr key={tx.id} className="text-sm text-slate-800 md:text-lg">
                      <td className="border-b border-slate-100 py-4 pr-4">
                        <div className="text-base font-semibold md:text-xl">{customer}</div>
                        <div className="text-sm text-slate-500 md:text-lg">{email}</div>
                      </td>
                      <td className="border-b border-slate-100 py-4 pr-4">
                        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize md:px-3 md:text-base ${statusClass}`}>
                          {statusKey}
                        </span>
                      </td>
                      <td className="border-b border-slate-100 py-4 pr-4 text-sm md:text-lg">{formatTimeAgo(tx.created_at)}</td>
                      <td className="border-b border-slate-100 py-4 text-right text-base font-semibold md:text-xl">
                        {formatMoney(tx.amount, tx.currency)}
                      </td>
                    </tr>
                  );
                })}

              {!loading && recentRows.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-xl text-slate-500">
                    No transactions yet.
                  </td>
                </tr>
              )}
              {loading && (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-xl text-slate-500">
                    Loading transactions...
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
