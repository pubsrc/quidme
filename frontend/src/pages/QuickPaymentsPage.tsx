import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import QRCode from "qrcode";
import { Copy } from "lucide-react";
import { useTranslation } from "react-i18next";
import { api } from "../lib/api";
import { getDefaultCurrencyForCountry } from "../lib/currency";
import { useAccountStatus } from "../lib/useAccountStatus";

const currencies = [
  { code: "gbp", labelKey: "components.create_link_dialog.currency_options.gbp", flag: "🇬🇧" },
  { code: "eur", labelKey: "components.create_link_dialog.currency_options.eur", flag: "🇪🇺" },
  { code: "usd", labelKey: "components.create_link_dialog.currency_options.usd", flag: "🇺🇸" },
  { code: "bgn", labelKey: "components.create_link_dialog.currency_options.bgn", flag: "🇧🇬" },
  { code: "ron", labelKey: "components.create_link_dialog.currency_options.ron", flag: "🇷🇴" },
  { code: "all", labelKey: "components.create_link_dialog.currency_options.all", flag: "🇦🇱" },
];

const toMinorUnits = (value: string) => {
  const normalized = value.replace(",", ".").trim();
  if (!normalized) return null;
  if (!/^\d+(\.\d{1,2})?$/.test(normalized)) return null;
  const parsed = Number(normalized);
  if (Number.isNaN(parsed)) return null;
  const rounded = Math.round(parsed * 100);
  return rounded > 0 ? rounded : null;
};

const currencySymbol = (code: string) => {
  const v = (code || "").toLowerCase();
  if (v === "gbp") return "£";
  if (v === "usd") return "$";
  if (v === "eur") return "€";
  if (v === "bgn") return "лв";
  if (v === "ron") return "lei";
  if (v === "all") return "L";
  return v.toUpperCase() + " ";
};

const formatQuickPaymentTitle = (baseTitle: string) => {
  const now = new Date();
  const dd = String(now.getDate()).padStart(2, "0");
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const yy = String(now.getFullYear()).slice(-2);
  const hh = String(now.getHours()).padStart(2, "0");
  const min = String(now.getMinutes()).padStart(2, "0");
  return `${baseTitle} - ${dd}-${mm}-${yy} ${hh}:${min}`;
};

const QuickPaymentsPage = () => {
  const { t } = useTranslation();
  const { account } = useAccountStatus();

  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("gbp");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentUrl, setPaymentUrl] = useState<string | null>(null);
  const [qrDataUrl, setQrDataUrl] = useState<string | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);
  const [copiedQr, setCopiedQr] = useState(false);

  const defaultCurrency = useMemo(
    () => getDefaultCurrencyForCountry(account?.country),
    [account?.country]
  );
  const symbol = useMemo(() => currencySymbol(currency), [currency]);

  useEffect(() => {
    if (!paymentUrl) {
      setCurrency(defaultCurrency);
    }
  }, [defaultCurrency, paymentUrl]);

  useEffect(() => {
    if (!paymentUrl) {
      setQrDataUrl(null);
      return;
    }
    let mounted = true;
    QRCode.toDataURL(paymentUrl, { width: 300, margin: 2 })
      .then((dataUrl: string) => {
        if (mounted) setQrDataUrl(dataUrl);
      })
      .catch(() => setQrDataUrl(null));
    return () => {
      mounted = false;
    };
  }, [paymentUrl]);

  const handleCreate = async () => {
    setError(null);
    const amountMinor = toMinorUnits(amount);
    if (!amountMinor) {
      setError(t("components.create_link_dialog.errors.invalid_amount"));
      return;
    }

    setCreating(true);
    try {
      const title = formatQuickPaymentTitle(t("quickPayments.title"));
      const response = await api.createQuickPayment({
        title,
        amount: amountMinor,
        currency,
      });
      setPaymentUrl(response.url);
    } catch (err: any) {
      setError(err?.message || t("components.create_link_dialog.errors.create_failed"));
    } finally {
      setCreating(false);
    }
  };

  const handleCopyLink = async () => {
    if (!paymentUrl) return;
    await navigator.clipboard.writeText(paymentUrl);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 1200);
  };

  const handleCopyQr = async () => {
    if (!qrDataUrl) return;
    try {
      const response = await fetch(qrDataUrl);
      const blob = await response.blob();
      await navigator.clipboard.write([new ClipboardItem({ [blob.type]: blob })]);
      setCopiedQr(true);
      setTimeout(() => setCopiedQr(false), 1200);
    } catch {
      setCopiedQr(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-8rem)] items-center justify-center">
      <div className="w-full max-w-sm [perspective:1200px]">
        <motion.div
          animate={{ rotateY: paymentUrl ? 180 : 0 }}
          transition={{ duration: 0.65, ease: "easeInOut" }}
          style={{ transformStyle: "preserve-3d" }}
          className="relative h-[430px]"
        >
          <div
            style={{ backfaceVisibility: "hidden" }}
            className="absolute inset-0 overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 shadow-xl"
          >
            <img
              src="/quidme-uk-qr.png"
              alt=""
              aria-hidden
              className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-[0.2]"
            />
            <div className="relative h-full">
              <div className="flex h-full flex-col gap-4 p-3 md:p-4">
                <div>
                  <select
                    className="h-12 w-full rounded-xl border border-slate-200 bg-white px-4 text-base text-slate-700 outline-none"
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                  >
                    {currencies.map((item) => (
                      <option key={item.code} value={item.code}>
                        {item.flag} {t(item.labelKey)}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white/95 px-4 py-4 shadow-sm">
                  <div className="flex items-center justify-center gap-4">
                    <div className="text-3xl font-semibold text-slate-300 md:text-4xl">{symbol}</div>
                    <input
                      inputMode="decimal"
                      type="text"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      className="w-[9rem] bg-transparent text-center text-3xl font-semibold tracking-tight text-slate-700 placeholder:text-slate-300 outline-none md:w-[10rem] md:text-4xl"
                      placeholder={t("components.create_link_dialog.amount_placeholder")}
                    />
                  </div>
                </div>

                {error && <div className="text-sm text-red-600">{error}</div>}

                <button
                  type="button"
                  onClick={handleCreate}
                  disabled={creating}
                  className="mt-auto h-12 w-full rounded-2xl bg-amber-500 text-sm font-semibold text-white transition hover:bg-amber-600 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {creating ? t("components.payment_link_share.generating") : t("quickPayments.generate_code")}
                </button>
              </div>
            </div>
          </div>

          <div
            style={{ backfaceVisibility: "hidden", transform: "rotateY(180deg)" }}
            className="absolute inset-0 overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 shadow-xl"
          >
            <div className="flex h-full flex-col">
              <div className="flex flex-1 flex-col items-center justify-center gap-4">
                <div className="rounded-2xl border border-slate-200 p-3">
                  {qrDataUrl ? (
                    <img src={qrDataUrl} alt={t("components.payment_link_share.qr_alt")} className="h-56 w-56" />
                  ) : (
                    <div className="flex h-56 w-56 items-center justify-center text-sm text-slate-500">
                      {t("components.payment_link_share.generating")}
                    </div>
                  )}
                </div>

                <div className="mt-1 flex flex-wrap items-center justify-center gap-2">
                  <button
                    type="button"
                    onClick={handleCopyLink}
                    className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${
                      copiedLink
                        ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                        : "border-slate-200 text-slate-600"
                    }`}
                  >
                    <Copy className="h-4 w-4" />
                    {copiedLink ? t("components.payment_link_share.copied") : t("components.payment_link_share.copy_link")}
                  </button>
                  <button
                    type="button"
                    onClick={handleCopyQr}
                    disabled={!qrDataUrl}
                    className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${
                      copiedQr
                        ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                        : "border-slate-200 text-slate-600"
                    }`}
                  >
                    <Copy className="h-4 w-4" />
                    {copiedQr ? t("components.payment_link_share.copied") : t("components.payment_link_share.copy_qr")}
                  </button>
                </div>
              </div>

              <div className="mt-4 text-xs text-slate-500 break-all">{paymentUrl}</div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default QuickPaymentsPage;
