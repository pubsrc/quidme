import { useEffect, useState } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { LinkResponse } from "../lib/api";
import PaymentLinkShare from "../components/PaymentLinkShare";

const formatAmount = (value: number) => (value / 100).toFixed(2);

const PaymentLinkDetailsPage = () => {
  const { t } = useTranslation();
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
    setError(t("pages.product_details.open_from_list"));
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
        {t("pages.product_details.loading")}
      </div>
    );
  }

  if (!link) {
    return (
      <div className="space-y-4">
        <button onClick={() => navigate("/app/payment-links")} className="text-sm text-slate-500 hover:text-slate-700">
          {t("pages.product_details.back")}
        </button>
        <div className="rounded-2xl bg-white p-6 text-sm text-red-500 shadow">
          {error || t("pages.product_details.not_found")}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <button onClick={() => navigate("/app/payment-links")} className="text-sm text-slate-500 hover:text-slate-700">
        {t("pages.product_details.back")}
      </button>

      <div className="rounded-2xl bg-white p-6 shadow">
        <div className="text-xs text-slate-400">
          {link.created_at ? new Date(link.created_at).toLocaleDateString() : "—"}
        </div>
        <div className="mt-1 flex items-center justify-between">
          <div>
            <div className="text-lg font-semibold text-brand-navy">{link.title ?? t("pages.product_details.default_title")}</div>
            <div className="text-sm text-slate-500">{link.description}</div>
          </div>
          <div className="text-sm text-slate-500">{link.status}</div>
        </div>
        <div className="mt-4 grid gap-3 text-sm text-slate-600 md:grid-cols-3">
          <div>
            <div className="text-xs text-slate-400">{t("pages.product_details.amount")}</div>
            <div className="font-semibold">{formatAmount(link.amount)}</div>
          </div>
          <div>
            <div className="text-xs text-slate-400">{t("pages.product_details.earnings")}</div>
            <div className="font-semibold">{formatAmount(link.earnings_amount ?? 0)}</div>
          </div>
          <div>
            <div className="text-xs text-slate-400">{t("pages.product_details.expires")}</div>
            <div className="font-semibold">
              {link.expires_at ? new Date(link.expires_at).toLocaleDateString() : t("pages.product_details.no_expiry")}
            </div>
          </div>
        </div>
        <div className="mt-4">
          <PaymentLinkShare url={link.url} />
        </div>
      </div>

      <div className="rounded-2xl bg-white p-6 shadow">
        <h3 className="text-lg font-semibold text-brand-navy">{t("pages.product_details.transactions")}</h3>
        <p className="mt-2 text-sm text-slate-500">
          {t("pages.product_details.transactions_info")}
        </p>
      </div>

      {error && <div className="text-sm text-red-500">{error}</div>}
    </div>
  );
};

export default PaymentLinkDetailsPage;
