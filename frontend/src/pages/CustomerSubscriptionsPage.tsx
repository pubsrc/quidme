import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../lib/api";

type StripeAddress = {
  line1?: string | null;
  line2?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  country?: string | null;
};

type StripeCustomer = {
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: StripeAddress | null;
};

type StripeSubscription = {
  id: string;
  status?: string | null;
  payment_link_title?: string | null;
  customer?: StripeCustomer | null;
};

type PaginatedResponse<T> = {
  items?: T[];
  has_more?: boolean;
  next_cursor?: string | null;
};

const CustomerSubscriptionsPage = () => {
  const { t } = useTranslation();
  const [stripeSubscriptions, setStripeSubscriptions] = useState<StripeSubscription[]>([]);
  const [stripeLoading, setStripeLoading] = useState(false);
  const [stripeError, setStripeError] = useState<string | null>(null);
  const [stripeLimit, setStripeLimit] = useState(25);
  const [stripeCursor, setStripeCursor] = useState<string | null>(null);
  const [stripeHasMore, setStripeHasMore] = useState(false);
  const [confirmCancelId, setConfirmCancelId] = useState<string | null>(null);

  useEffect(() => {
    const fetchStripeSubscriptions = async () => {
      setStripeLoading(true);
      setStripeError(null);
      try {
        const response = (await api.listStripeSubscriptions({ limit: stripeLimit })) as PaginatedResponse<StripeSubscription>;
        setStripeSubscriptions(response.items ?? []);
        setStripeHasMore(Boolean(response.has_more));
        setStripeCursor(response.next_cursor ?? null);
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
      const response = (await api.listStripeSubscriptions({
        limit: stripeLimit,
        page: stripeCursor,
      })) as PaginatedResponse<StripeSubscription>;
      setStripeSubscriptions((prev) => [...prev, ...(response.items ?? [])]);
      setStripeHasMore(Boolean(response.has_more));
      setStripeCursor(response.next_cursor ?? null);
    } catch (err: any) {
      setStripeError(err?.message || t("pages.customer_subscriptions.load_more_failed"));
    } finally {
      setStripeLoading(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!confirmCancelId) return;
    setStripeLoading(true);
    setStripeError(null);
    try {
      await api.cancelStripeSubscription(confirmCancelId);
      setStripeSubscriptions((prev) =>
        prev.map((item) => (item.id === confirmCancelId ? { ...item, status: "canceled" } : item))
      );
      setConfirmCancelId(null);
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
        {stripeSubscriptions.length > 0 && (
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow">
            <table className="hidden w-full table-fixed md:table">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-4 py-3">{t("pages.customer_subscriptions.name")}</th>
                  <th className="px-4 py-3">{t("pages.customer_subscriptions.email")}</th>
                  <th className="px-4 py-3">{t("pages.customer_subscriptions.phone")}</th>
                  <th className="px-4 py-3">{t("pages.customer_subscriptions.payment_link_title")}</th>
                  <th className="px-4 py-3">{t("pages.customer_subscriptions.status")}</th>
                  <th className="px-4 py-3 text-right">{t("pages.customer_subscriptions.action")}</th>
                </tr>
              </thead>
              <tbody>
                {stripeSubscriptions.map((subscription) => (
                  <tr key={subscription.id} className="border-t border-slate-100 text-sm">
                    <td className="px-4 py-3">{subscription.customer?.name ?? t("pages.customer_subscriptions.dash")}</td>
                    <td className="px-4 py-3">{subscription.customer?.email ?? t("pages.customer_subscriptions.dash")}</td>
                    <td className="px-4 py-3">{subscription.customer?.phone ?? t("pages.customer_subscriptions.dash")}</td>
                    <td className="px-4 py-3">{subscription.payment_link_title ?? t("pages.customer_subscriptions.dash")}</td>
                    <td className="px-4 py-3">
                      {subscription.status === "canceled"
                        ? t("pages.customer_subscriptions.canceled")
                        : subscription.status ?? t("pages.customer_subscriptions.dash")}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => setConfirmCancelId(subscription.id)}
                        disabled={stripeLoading || subscription.status === "canceled"}
                        className="rounded-full border border-slate-200 px-3 py-1 text-xs"
                      >
                        {subscription.status === "canceled"
                          ? t("pages.customer_subscriptions.canceled")
                          : t("pages.customer_subscriptions.cancel_subscription")}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="space-y-3 p-4 md:hidden">
              {stripeSubscriptions.map((subscription) => (
                <div key={subscription.id} className="rounded-xl border border-slate-200 p-3">
                  <div className="text-sm font-semibold">{subscription.customer?.name ?? t("pages.customer_subscriptions.dash")}</div>
                  <div className="text-xs text-slate-500">{subscription.customer?.email ?? t("pages.customer_subscriptions.dash")}</div>
                  <div className="mt-2 text-xs text-slate-500">
                    {t("pages.customer_subscriptions.phone")}: {subscription.customer?.phone ?? t("pages.customer_subscriptions.dash")}
                  </div>
                  <div className="text-xs text-slate-500">
                    {t("pages.customer_subscriptions.payment_link_title")}: {subscription.payment_link_title ?? t("pages.customer_subscriptions.dash")}
                  </div>
                  <div className="text-xs text-slate-500">
                    {t("pages.customer_subscriptions.status")}:{" "}
                    {subscription.status === "canceled"
                      ? t("pages.customer_subscriptions.canceled")
                      : subscription.status ?? t("pages.customer_subscriptions.dash")}
                  </div>
                  <div className="mt-3 flex justify-end">
                    <button
                      onClick={() => setConfirmCancelId(subscription.id)}
                      disabled={stripeLoading || subscription.status === "canceled"}
                      className="rounded-full border border-slate-200 px-3 py-1 text-xs"
                    >
                      {subscription.status === "canceled"
                        ? t("pages.customer_subscriptions.canceled")
                        : t("pages.customer_subscriptions.cancel_subscription")}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
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

      {confirmCancelId && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-slate-900">
              {t("pages.customer_subscriptions.confirm_cancel_title")}
            </h3>
            <p className="mt-2 text-sm text-slate-600">{t("pages.customer_subscriptions.confirm_cancel_text")}</p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setConfirmCancelId(null)}
                className="rounded-full border border-slate-200 px-4 py-2 text-sm"
              >
                {t("pages.customer_subscriptions.confirm_cancel_no")}
              </button>
              <button
                type="button"
                onClick={handleCancelSubscription}
                disabled={stripeLoading}
                className="rounded-full bg-rose-600 px-4 py-2 text-sm text-white disabled:opacity-60"
              >
                {stripeLoading
                  ? t("pages.customer_subscriptions.canceling")
                  : t("pages.customer_subscriptions.confirm_cancel_yes")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomerSubscriptionsPage;
