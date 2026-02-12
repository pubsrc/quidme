import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type LinkResponse } from "../lib/api";
import CreateLinkDialog from "../components/CreateLinkDialog";
import LinkCard from "../components/LinkCard";

type LinkKind = "one_time" | "subscription";

const PaymentLinksPage = () => {
  const navigate = useNavigate();
  const [createKind, setCreateKind] = useState<LinkKind>("one_time");
  const [paymentLinks, setPaymentLinks] = useState<LinkResponse[]>([]);
  const [subscriptionLinks, setSubscriptionLinks] = useState<LinkResponse[]>([]);
  const [isLoadingLinks, setIsLoadingLinks] = useState(false);
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDialog, setShowDialog] = useState(false);

  useEffect(() => {
    const fetchLinks = async () => {
      setIsLoadingLinks(true);
      setError(null);
      try {
        const [payments, subscriptions] = await Promise.all([
          api.listPaymentLinks(),
          api.listSubscriptions(),
        ]);
        setPaymentLinks(payments || []);
        setSubscriptionLinks(subscriptions || []);
      } catch (err: any) {
        setError(err?.message || "Unable to load links.");
      } finally {
        setIsLoadingLinks(false);
      }
    };

    fetchLinks();
  }, []);

  const allLinks = useMemo(() => {
    const merged = [
      ...paymentLinks.map((item) => ({ ...item, __kind: "one_time" as const })),
      ...subscriptionLinks.map((item) => ({ ...item, __kind: "subscription" as const })),
    ];
    return merged.sort((a, b) => {
      const ta = a.created_at ? Date.parse(a.created_at) : 0;
      const tb = b.created_at ? Date.parse(b.created_at) : 0;
      return tb - ta;
    });
  }, [paymentLinks, subscriptionLinks]);

  const disablePaymentLink = async (linkId: string) => {
    setIsBusy(true);
    setError(null);
    try {
      await api.disablePaymentLink(linkId);
      setPaymentLinks((prev) => prev.map((l) => (l.id === linkId ? { ...l, status: "DISABLED" } : l)));
    } catch (err: any) {
      setError(err?.message || "Unable to disable link.");
    } finally {
      setIsBusy(false);
    }
  };

  const disableSubscriptionLink = async (subscriptionId: string) => {
    setIsBusy(true);
    setError(null);
    try {
      await api.disableSubscription(subscriptionId);
      setSubscriptionLinks((prev) =>
        prev.map((l) => (l.id === subscriptionId ? { ...l, status: "DISABLED" } : l))
      );
    } catch (err: any) {
      setError(err?.message || "Unable to disable link.");
    } finally {
      setIsBusy(false);
    }
  };

  return (
    <div className="space-y-6 md:space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">Products</h2>
          <p className="mt-2 text-base text-slate-500 md:text-lg">Create and manage one-time and recurring product checkout links.</p>
        </div>
        <button
          type="button"
          onClick={() => setShowDialog(true)}
          className="inline-flex items-center gap-2 rounded-xl bg-amber-500 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-600 md:gap-3 md:rounded-2xl md:px-6 md:py-3 md:text-lg"
        >
          <span className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-white/60 text-sm">+</span>
          Add Product
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-base text-red-700">{error}</div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {isLoadingLinks && <div className="col-span-full text-base text-slate-500 md:text-lg">Loading...</div>}

        {!isLoadingLinks && allLinks.length === 0 && (
          <div className="col-span-full rounded-2xl border border-slate-200 bg-white px-4 py-8 text-base text-slate-600 md:rounded-3xl md:px-6 md:py-10 md:text-lg">
            No products yet. Add your first product checkout.
          </div>
        )}

        {allLinks.map((link) => (
          <LinkCard
            key={link.id}
            link={link}
            onDisable={link.__kind === "subscription" ? disableSubscriptionLink : disablePaymentLink}
            onOpen={link.__kind === "one_time" ? (id) => navigate(`/app/payment-links/${id}`) : undefined}
            loading={isBusy}
            showInterval={link.__kind === "subscription"}
            showEarnings={false}
            defaultTitle={link.__kind === "subscription" ? "Subscription Product" : "Product"}
            mockStyle
          />
        ))}
      </div>

      <CreateLinkDialog
        open={showDialog}
        onClose={() => setShowDialog(false)}
        initialKind={createKind}
        onCreated={(link, kind) => {
          if (kind === "one_time") setPaymentLinks((prev) => [link, ...prev]);
          else setSubscriptionLinks((prev) => [link, ...prev]);
          setCreateKind(kind);
        }}
      />
    </div>
  );
};

export default PaymentLinksPage;
