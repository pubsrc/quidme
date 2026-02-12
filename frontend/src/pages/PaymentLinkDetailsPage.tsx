import { useEffect, useState } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import type { LinkResponse } from "../lib/api";
import PaymentLinkShare from "../components/PaymentLinkShare";

const formatAmount = (value: number) => (value / 100).toFixed(2);

const PaymentLinkDetailsPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [link, setLink] = useState<LinkResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const linkFromState = (location.state as { link?: LinkResponse } | null)?.link;
    if (!id) {
      setLoading(false);
      return;
    }
    if (linkFromState && linkFromState.id === id) {
      setLink(linkFromState);
      setLoading(false);
      return;
    }
    setError("Open this page from the products list.");
    setLoading(false);
  }, [id, location.state]);

  useEffect(() => {
    if (!loading && !link && id) {
      navigate("/app/payment-links", { replace: true });
    }
  }, [loading, link, id, navigate]);

  if (loading) {
    return (
      <div className="rounded-2xl bg-white p-6 text-sm text-slate-500 shadow">
        Loading product checkout...
      </div>
    );
  }

  if (!link) {
    return (
      <div className="space-y-4">
        <button onClick={() => navigate("/app/payment-links")} className="text-sm text-slate-500 hover:text-slate-700">
          Back to products
        </button>
        <div className="rounded-2xl bg-white p-6 text-sm text-red-500 shadow">
          {error || "Product checkout not found."}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <button onClick={() => navigate("/app/payment-links")} className="text-sm text-slate-500 hover:text-slate-700">
        Back to products
      </button>

      <div className="rounded-2xl bg-white p-6 shadow">
        <div className="text-xs text-slate-400">
          {link.created_at ? new Date(link.created_at).toLocaleDateString() : "—"}
        </div>
        <div className="mt-1 flex items-center justify-between">
          <div>
            <div className="text-lg font-semibold text-brand-navy">{link.title ?? "Product"}</div>
            <div className="text-sm text-slate-500">{link.description}</div>
          </div>
          <div className="text-sm text-slate-500">{link.status}</div>
        </div>
        <div className="mt-4 grid gap-3 text-sm text-slate-600 md:grid-cols-3">
          <div>
            <div className="text-xs text-slate-400">Amount</div>
            <div className="font-semibold">{formatAmount(link.amount)}</div>
          </div>
          <div>
            <div className="text-xs text-slate-400">Earnings</div>
            <div className="font-semibold">{formatAmount(link.earnings_amount ?? 0)}</div>
          </div>
          <div>
            <div className="text-xs text-slate-400">Expires</div>
            <div className="font-semibold">
              {link.expires_at ? new Date(link.expires_at).toLocaleDateString() : "No expiry"}
            </div>
          </div>
        </div>
        <div className="mt-4">
          <PaymentLinkShare url={link.url} />
        </div>
      </div>

      <div className="rounded-2xl bg-white p-6 shadow">
        <h3 className="text-lg font-semibold text-brand-navy">Transactions</h3>
        <p className="mt-2 text-sm text-slate-500">
          Transactions are recorded automatically when payments succeed. View all transactions in the Transactions
          page.
        </p>
      </div>

      {error && <div className="text-sm text-red-500">{error}</div>}
    </div>
  );
};

export default PaymentLinkDetailsPage;
