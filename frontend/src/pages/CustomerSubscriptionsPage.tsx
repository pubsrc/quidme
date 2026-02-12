import { useEffect, useState } from "react";
import { api } from "../lib/api";

const CustomerSubscriptionsPage = () => {
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
        setStripeError(err?.message || "Unable to load customer subscriptions.");
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
      setStripeError(err?.message || "Unable to load more subscriptions.");
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
      setStripeError(err?.message || "Unable to cancel subscription.");
    } finally {
      setStripeLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-brand-navy">Customer subscription</h2>
          <p className="text-sm text-slate-500">Subscriptions created from your product checkout links.</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <span>Limit</span>
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
          Loading customer subscriptions...
        </div>
      )}
      {stripeError && <div className="text-sm text-red-500">{stripeError}</div>}

      <div className="space-y-3">
        {stripeSubscriptions.map((subscription) => (
          <div key={subscription.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold">{subscription.customer?.name ?? "Customer"}</div>
                <div className="text-xs text-slate-500">{subscription.customer?.email ?? "—"}</div>
              </div>
              <div className="text-xs text-slate-500">Status: {subscription.status}</div>
            </div>
            <div className="mt-3 grid gap-2 text-xs text-slate-500 md:grid-cols-2">
              <div>Phone: {subscription.customer?.phone ?? "—"}</div>
              <div>
                Plan:{" "}
                {subscription.plan?.amount
                  ? `${(subscription.plan.amount / 100).toFixed(2)} ${subscription.plan.currency?.toUpperCase()}`
                  : "—"}{" "}
                / {subscription.plan?.interval ?? "—"}
              </div>
              <div>
                Period:{" "}
                {subscription.current_period_start
                  ? new Date(subscription.current_period_start).toLocaleDateString()
                  : "—"}{" "}
                -{" "}
                {subscription.current_period_end
                  ? new Date(subscription.current_period_end).toLocaleDateString()
                  : "—"}
              </div>
              <div>
                Address:{" "}
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
                  : "—"}
              </div>
            </div>
            <div className="mt-3 flex justify-end">
              <button
                onClick={() => handleCancelSubscription(subscription.id)}
                disabled={stripeLoading || subscription.status === "canceled"}
                className="rounded-full border border-slate-200 px-3 py-1 text-xs"
              >
                {subscription.status === "canceled" ? "Canceled" : "Cancel subscription"}
              </button>
            </div>
          </div>
        ))}
        {stripeSubscriptions.length === 0 && !stripeLoading && (
          <div className="rounded-2xl bg-white p-6 text-sm text-slate-500 shadow">
            No customer subscriptions yet.
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
            {stripeLoading ? "Loading..." : "Load more"}
          </button>
        </div>
      )}
    </div>
  );
};

export default CustomerSubscriptionsPage;
