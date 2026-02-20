import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import QRCode from "qrcode";
import { Copy, QrCode, Share2 } from "lucide-react";

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
            <Copy className="h-4 w-4" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowQr(true);
            }}
            className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 text-slate-500 hover:bg-slate-50"
            title={t("components.payment_link_share.show_qr")}
          >
            <QrCode className="h-4 w-4" />
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
            <Share2 className="h-5 w-5" />
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
              <Copy className="h-4 w-4" />
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
              <QrCode className="h-4 w-4" />
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
                  <Copy className="h-4 w-4" />
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
