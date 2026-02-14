import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import QRCode from "qrcode";

type PaymentLinkShareProps = {
  url: string;
  compact?: boolean;
  iconOnly?: boolean;
};

const PaymentLinkShare = ({ url, compact = false, iconOnly = false }: PaymentLinkShareProps) => {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const [qrCopied, setQrCopied] = useState(false);
  const [showQr, setShowQr] = useState(false);
  const [qrDataUrl, setQrDataUrl] = useState<string | null>(null);

  const safeUrl = useMemo(() => url ?? "", [url]);

  const handleCopy = async () => {
    if (!safeUrl) return;
    await navigator.clipboard.writeText(safeUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  useEffect(() => {
    if (!showQr || !safeUrl) return;
    let mounted = true;
    QRCode.toDataURL(safeUrl, { width: 220, margin: 2 })
      .then((dataUrl: string) => {
        if (mounted) {
          setQrDataUrl(dataUrl);
        }
      })
      .catch(() => setQrDataUrl(null));
    return () => {
      mounted = false;
    };
  }, [showQr, safeUrl]);

  const handleCopyQr = async () => {
    if (!qrDataUrl || !navigator.clipboard) return;
    try {
      const response = await fetch(qrDataUrl);
      const blob = await response.blob();
      await navigator.clipboard.write([
        new ClipboardItem({
          [blob.type]: blob,
        }),
      ]);
      setQrCopied(true);
      setTimeout(() => setQrCopied(false), 1200);
    } catch {
      setQrCopied(false);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      {iconOnly ? (
        <>
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleCopy();
            }}
            className={`inline-flex h-8 w-8 items-center justify-center rounded-full border transition ${
              copied ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-slate-200 text-slate-500 hover:bg-slate-50"
            }`}
            title={copied ? t("components.payment_link_share.copied") : t("components.payment_link_share.copy_link")}
          >
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 9h9v9H9z" />
              <path d="M6 15H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v1" />
            </svg>
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowQr(true);
            }}
            className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 text-slate-500 hover:bg-slate-50"
            title={t("components.payment_link_share.show_qr")}
          >
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4z" />
              <path d="M14 14h3v3h-3zM17 17h3v3h-3zM20 14h0" />
            </svg>
          </button>
        </>
      ) : (
        compact ? (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowQr(true);
            }}
            className="inline-flex h-9 w-9 items-center justify-center rounded-full text-slate-500 hover:bg-slate-100"
            title={t("components.payment_link_share.share_link")}
          >
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="18" cy="5" r="2" />
              <circle cx="6" cy="12" r="2" />
              <circle cx="18" cy="19" r="2" />
              <path d="M8 12 16 7M8 12l8 5" />
            </svg>
          </button>
        ) : (
        <>
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleCopy();
            }}
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${
              copied ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-slate-200 text-slate-600"
            }`}
          >
            <span className="inline-flex h-4 w-4 items-center justify-center">
              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 9h9v9H9z" />
                <path d="M6 15H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v1" />
              </svg>
            </span>
            {copied ? t("components.payment_link_share.copied") : t("components.payment_link_share.copy_link")}
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowQr(true);
            }}
            className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600"
          >
            <span className="inline-flex h-4 w-4 items-center justify-center">
              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4z" />
                <path d="M14 14h3v3h-3zM17 17h3v3h-3zM20 14h0" />
              </svg>
            </span>
            {t("components.payment_link_share.qr_code")}
          </button>
        </>
        )
      )}

      {showQr && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold text-slate-700">{t("components.payment_link_share.qr_title")}</div>
              <button
                onClick={() => setShowQr(false)}
                className="text-sm text-slate-500 hover:text-slate-700"
              >
                {t("components.payment_link_share.close")}
              </button>
            </div>
            <div className="mt-4 flex items-center justify-center">
              {qrDataUrl ? (
                <img src={qrDataUrl} alt={t("components.payment_link_share.qr_alt")} className="h-56 w-56" />
              ) : (
                <div className="text-sm text-slate-500">{t("components.payment_link_share.generating")}</div>
              )}
            </div>
            <div className="mt-4 flex justify-center">
              <button
                onClick={handleCopyQr}
                disabled={!qrDataUrl}
                className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${
                  qrCopied
                    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                    : "border-slate-200 text-slate-600"
                }`}
              >
                <span className="inline-flex h-4 w-4 items-center justify-center">
                  <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M9 9h9v9H9z" />
                    <path d="M6 15H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v1" />
                  </svg>
                </span>
                {qrCopied ? t("components.payment_link_share.copied") : t("components.payment_link_share.copy_qr")}
              </button>
            </div>
            <div className="mt-4 text-xs text-slate-500 break-all">{safeUrl}</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PaymentLinkShare;
