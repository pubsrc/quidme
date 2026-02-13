import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../lib/api";

const CustomerSubscriptionsPage = () => {
  const { t } = useTranslation();
  const [stripeSubscriptions, setStripeSubscriptions] = useState<any[]>([]);
  const [stripeLoading, setStripeLoading] = useState(false);
  const [stripeError, setStripeError] = useState<string | null>(null);
  const [stripeLimit, setStripeLimit] = useState(25);
  const [stripeCursor, setStripeCursor] = useState<string | null>(null);
  const [stripeHasMore, setStripeHasMore] = useState(false);

  useEffect(() => {
    const fetchStripeSubscriptions = async () => {
      setStripeLoading(true);
      setStripeError(null);
      try {
        const response = await api.listStripeSubscriptions({ limit: stripeLimit });
        setStripeSubscriptions(response.items || []);
        setStripeHasMore(Boolean(response.has_more));
        setStripeCursor(response.next_cursor || null);
      } catch (err: any) {
        setStripeError(err?.message || t("pages.customer_subscriptions.load_failed"));
      } finally {
        setStripeLoading(false);
      }
    };

    fetchStripeSubscriptions();
  }, [stripeLimit]);

  const handleLoadMoreStripe = async () => {
    if (!stripeCursor) return;
    setStripeLoading(true);
    setStripeError(null);
    try {
      const response = await api.listStripeSubscriptions({
        limit: stripeLimit,
        page: stripeCursor,
      });
      setStripeSubscriptions((prev) => [...prev, ...(response.items || [])]);
      setStripeHasMore(Boolean(response.has_more));
      setStripeCursor(response.next_cursor || null);
    } catch (err: any) {
      setStripeError(err?.message || t("pages.customer_subscriptions.load_more_failed"));
    } finally {
      setStripeLoading(false);
    }
  };

  const handleCancelSubscription = async (subscriptionId: string) => {
    setStripeLoading(true);
    setStripeError(null);
    try {
      await api.cancelStripeSubscription(subscriptionId);
      setStripeSubscriptions((prev) =>
        prev.map((item) => (item.id === subscriptionId ? { ...item, status: "canceled" } : item))
      );
    } catch (err: any) {
      setStripeError(err?.message || t("pages.customer_subscriptions.cancel_failed"));
    } finally {
      setStripeLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-brand-navy">{t("pages.customer_subscriptions.title")}</h2>
          <p className="text-sm text-slate-500">{t("pages.customer_subscriptions.subtitle")}</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <span>{t("pages.customer_subscriptions.limit")}</span>
          <select
            className="rounded-lg border border-slate-200 px-2 py-1"
            value={stripeLimit}
            onChange={(e) => setStripeLimit(Number(e.target.value))}
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
        </div>
      </div>

      {stripeLoading && (
        <div className="rounded-2xl bg-white p-6 text-sm text-slate-500 shadow">
          {t("pages.customer_subscriptions.loading")}
        </div>
      )}
      {stripeError && <div className="text-sm text-red-500">{stripeError}</div>}

      <div className="space-y-3">
        {stripeSubscriptions.map((subscription) => (
          <div key={subscription.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold">{subscription.customer?.name ?? t("pages.customer_subscriptions.customer")}</div>
                <div className="text-xs text-slate-500">{subscription.customer?.email ?? t("pages.customer_subscriptions.dash")}</div>
              </div>
              <div className="text-xs text-slate-500">{t("pages.customer_subscriptions.status")}: {subscription.status}</div>
            </div>
            <div className="mt-3 grid gap-2 text-xs text-slate-500 md:grid-cols-2">
              <div>{t("pages.customer_subscriptions.phone")}: {subscription.customer?.phone ?? t("pages.customer_subscriptions.dash")}</div>
              <div>
                {t("pages.customer_subscriptions.plan")}:{" "}
                {subscription.plan?.amount
                  ? `${(subscription.plan.amount / 100).toFixed(2)} ${subscription.plan.currency?.toUpperCase()}`
                  : t("pages.customer_subscriptions.dash")}{" "}
                / {subscription.plan?.interval ?? t("pages.customer_subscriptions.dash")}
              </div>
              <div>
                {t("pages.customer_subscriptions.period")}:{" "}
                {subscription.current_period_start
                  ? new Date(subscription.current_period_start).toLocaleDateString()
                  : t("pages.customer_subscriptions.dash")}{" "}
                -{" "}
                {subscription.current_period_end
                  ? new Date(subscription.current_period_end).toLocaleDateString()
                  : t("pages.customer_subscriptions.dash")}
              </div>
              <div>
                {t("pages.customer_subscriptions.address")}:{" "}
                {subscription.customer?.address
                  ? [
                      subscription.customer.address.line1,
                      subscription.customer.address.line2,
                      subscription.customer.address.city,
                      subscription.customer.address.state,
                      subscription.customer.address.postal_code,
                      subscription.customer.address.country,
                    ]
                      .filter(Boolean)
                      .join(", ")
                  : t("pages.customer_subscriptions.dash")}
              </div>
            </div>
            <div className="mt-3 flex justify-end">
              <button
                onClick={() => handleCancelSubscription(subscription.id)}
                disabled={stripeLoading || subscription.status === "canceled"}
                className="rounded-full border border-slate-200 px-3 py-1 text-xs"
              >
                {subscription.status === "canceled" ? t("pages.customer_subscriptions.canceled") : t("pages.customer_subscriptions.cancel_subscription")}
              </button>
            </div>
          </div>
        ))}
        {stripeSubscriptions.length === 0 && !stripeLoading && (
          <div className="rounded-2xl bg-white p-6 text-sm text-slate-500 shadow">
            {t("pages.customer_subscriptions.empty")}
          </div>
        )}
      </div>

      {stripeHasMore && (
        <div className="flex justify-center">
          <button
            onClick={handleLoadMoreStripe}
            disabled={stripeLoading}
            className="rounded-full border border-slate-200 px-4 py-2 text-sm"
          >
            {stripeLoading ? t("pages.customer_subscriptions.loading_more") : t("pages.customer_subscriptions.load_more")}
          </button>
        </div>
      )}
    </div>
  );
};

export default CustomerSubscriptionsPage;
