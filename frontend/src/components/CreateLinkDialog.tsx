import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { ChevronDown } from "lucide-react";
import { api, type LinkResponse } from "../lib/api";

type LinkKind = "one_time" | "subscription";

const currencies = [
  { code: "gbp", labelKey: "components.create_link_dialog.currency_options.gbp", flag: "🇬🇧" },
  { code: "eur", labelKey: "components.create_link_dialog.currency_options.eur", flag: "🇪🇺" },
  { code: "usd", labelKey: "components.create_link_dialog.currency_options.usd", flag: "🇺🇸" },
  { code: "bgn", labelKey: "components.create_link_dialog.currency_options.bgn", flag: "🇧🇬" },
  { code: "ron", labelKey: "components.create_link_dialog.currency_options.ron", flag: "🇷🇴" },
  { code: "all", labelKey: "components.create_link_dialog.currency_options.all", flag: "🇦🇱" },
];

const intervals = [
  { value: "day", labelKey: "components.create_link_dialog.interval_options.day" },
  { value: "week", labelKey: "components.create_link_dialog.interval_options.week" },
  { value: "month", labelKey: "components.create_link_dialog.interval_options.month" },
  { value: "year", labelKey: "components.create_link_dialog.interval_options.year" },
];

const titlePlaceholderPhrases = [
  "components.create_link_dialog.title_placeholders.piano",
  "components.create_link_dialog.title_placeholders.lunch",
  "components.create_link_dialog.title_placeholders.spanish",
  "components.create_link_dialog.title_placeholders.maths",
];

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

const toMinorUnits = (value: string) => {
  const normalized = value.replace(",", ".").trim();
  if (!normalized) return null;
  if (!/^\d+(\.\d{1,2})?$/.test(normalized)) return null;
  const parsed = Number(normalized);
  if (Number.isNaN(parsed)) return null;
  const rounded = Math.round(parsed * 100);
  return rounded > 0 ? rounded : null;
};

export type CreateLinkDialogProps = {
  open: boolean;
  onClose: () => void;
  onCreated: (link: LinkResponse, kind: LinkKind) => void;
  initialKind?: LinkKind;
};

const CreateLinkDialog = ({ open, onClose, onCreated, initialKind = "one_time" }: CreateLinkDialogProps) => {
  const { t } = useTranslation();
  const [kind, setKind] = useState<LinkKind>(initialKind);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("gbp");
  const [interval, setInterval] = useState("month");
  const [expiresAt, setExpiresAt] = useState("");
  const [requireName, setRequireName] = useState(true);
  const [requireEmail, setRequireEmail] = useState(true);
  const [requireAddress, setRequireAddress] = useState(false);
  const [requirePhone, setRequirePhone] = useState(false);
  const [descriptionFocused, setDescriptionFocused] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [placeholderText, setPlaceholderText] = useState(t(titlePlaceholderPhrases[0]));
  const [placeholderPhraseIndex, setPlaceholderPhraseIndex] = useState(0);
  const [placeholderCharIndex, setPlaceholderCharIndex] = useState(0);
  const [isDeletingPlaceholder, setIsDeletingPlaceholder] = useState(false);
  const [placeholderPaused, setPlaceholderPaused] = useState(false);

  const ctaLabel = useMemo(
    () =>
      kind === "one_time"
        ? t("components.create_link_dialog.cta_one_time")
        : t("components.create_link_dialog.cta_subscription"),
    [kind, t]
  );
  const symbol = useMemo(() => currencySymbol(currency), [currency]);

  const resetAndClose = () => {
    setKind(initialKind);
    setTitle("");
    setDescription("");
    setAmount("");
    setCurrency("gbp");
    setInterval("month");
    setExpiresAt("");
    setRequireName(true);
    setRequireEmail(true);
    setRequireAddress(false);
    setRequirePhone(false);
    setDescriptionFocused(false);
    setLoading(false);
    setError(null);
    setExpanded(false);
    onClose();
  };

  useEffect(() => {
    if (!open) return;
    // Re-open should start collapsed unless we're creating a recurring link.
    setExpanded(initialKind === "subscription");
    setPlaceholderText(t(titlePlaceholderPhrases[0]));
    setPlaceholderPhraseIndex(0);
    setPlaceholderCharIndex(0);
    setIsDeletingPlaceholder(false);
    setPlaceholderPaused(false);
  }, [open, initialKind]);

  useEffect(() => {
    if (!open) return;
    if (kind === "subscription") setExpanded(true);
  }, [kind, open]);

  useEffect(() => {
    if (!open || title.trim() || placeholderPaused) return;

    const currentPhrase = t(titlePlaceholderPhrases[placeholderPhraseIndex]);
    const nextDelay = isDeletingPlaceholder ? 35 : 75;
    const timer = window.setTimeout(() => {
      if (!isDeletingPlaceholder) {
        const nextIndex = Math.min(placeholderCharIndex + 1, currentPhrase.length);
        setPlaceholderCharIndex(nextIndex);
        setPlaceholderText(currentPhrase.slice(0, nextIndex));
        if (nextIndex === currentPhrase.length) {
          setPlaceholderPaused(true);
        }
        return;
      }

      const nextIndex = Math.max(placeholderCharIndex - 1, 0);
      setPlaceholderCharIndex(nextIndex);
      setPlaceholderText(currentPhrase.slice(0, nextIndex));
      if (nextIndex === 0) {
        const nextPhraseIndex = (placeholderPhraseIndex + 1) % titlePlaceholderPhrases.length;
        setPlaceholderPhraseIndex(nextPhraseIndex);
        setIsDeletingPlaceholder(false);
      }
    }, nextDelay);

    return () => window.clearTimeout(timer);
  }, [open, title, placeholderPaused, placeholderPhraseIndex, placeholderCharIndex, isDeletingPlaceholder]);

  useEffect(() => {
    if (!open || title.trim() || !placeholderPaused) return;
    const pauseTimer = window.setTimeout(() => {
      setPlaceholderPaused(false);
      setIsDeletingPlaceholder(true);
    }, 1200);
    return () => window.clearTimeout(pauseTimer);
  }, [open, title, placeholderPaused]);

  const handleCreate = async () => {
    setLoading(true);
    setError(null);
    try {
      if (!title.trim()) {
        throw new Error(t("components.create_link_dialog.errors.title_required"));
      }
      const amountMinor = toMinorUnits(amount);
      if (!amountMinor) {
        throw new Error(t("components.create_link_dialog.errors.invalid_amount"));
      }

      const commonPayload = {
        title: title.trim(),
        description: description.trim() || undefined,
        amount: amountMinor,
        currency,
        expires_at: expiresAt || undefined,
        require_name: requireName,
        require_email: requireEmail,
        require_address: requireAddress,
        require_phone: requirePhone,
      };

      const response =
        kind === "one_time"
          ? await api.createPaymentLink(commonPayload)
          : await api.createSubscription({ ...commonPayload, interval });

      onCreated(response, kind);
      resetAndClose();
    } catch (err: any) {
      setError(err?.message || t("components.create_link_dialog.errors.create_failed"));
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={resetAndClose}
    >
      <div
        className="w-full max-w-md max-h-[90vh] overflow-y-auto rounded-[2.25rem] bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mt-7 flex items-center justify-center gap-4">
          <div className="text-5xl font-semibold text-slate-200">{symbol}</div>
          <input
            inputMode="decimal"
            type="text"
            className="w-[12rem] bg-transparent text-center text-5xl font-semibold tracking-tight text-slate-700 placeholder:text-slate-300 outline-none"
            placeholder={t("components.create_link_dialog.amount_placeholder")}
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </div>

        <div className="mt-7 flex items-center justify-between gap-3 pt-5">
          <div className="flex items-center gap-2 flex-1 justify-center">
            <button
              type="button"
              onClick={() => setKind("one_time")}
              className={`rounded-full px-6 py-2 text-sm font-semibold transition ${
                kind === "one_time" ? "bg-orange-100 text-orange-700 ring-1 ring-orange-200" : "bg-slate-100 text-slate-600"
              }`}
            >
              {t("components.create_link_dialog.one_time")}
            </button>
            <button
              type="button"
              onClick={() => {
                setKind("subscription");
                setExpanded(true);
              }}
              className={`rounded-full px-6 py-2 text-sm font-semibold transition ${
                kind === "subscription" ? "bg-sky-100 text-sky-700 ring-1 ring-sky-200" : "bg-slate-100 text-slate-600"
              }`}
            >
              {t("components.create_link_dialog.repeat")}
            </button>
          </div>
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="rounded-full p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
            aria-label={expanded ? t("components.create_link_dialog.collapse") : t("components.create_link_dialog.expand")}
          >
            <ChevronDown className={`h-5 w-5 transition-transform ${expanded ? "rotate-180" : ""}`} />
          </button>
        </div>

        <input
          className="mt-5 w-full rounded-xl border border-slate-200 px-4 py-3 text-base outline-none focus:border-brand-sky"
          placeholder={placeholderText || t("components.create_link_dialog.title_placeholder")}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />

        {expanded && (
          <div className="mt-7 space-y-3">
            <textarea
              className={`w-full rounded-xl border border-slate-200 px-4 py-3 text-base outline-none transition-all duration-200 focus:border-brand-sky ${
                descriptionFocused ? "min-h-[140px]" : "min-h-[88px]"
              }`}
              placeholder={t("components.create_link_dialog.description_placeholder")}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onFocus={() => setDescriptionFocused(true)}
              onBlur={() => setDescriptionFocused(false)}
            />

            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="text-xs font-semibold tracking-wide text-slate-400">{t("components.create_link_dialog.currency")}</div>
                <select
                  className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 text-base outline-none focus:border-brand-sky"
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

              {kind === "subscription" ? (
                <div>
                  <div className="text-xs font-semibold tracking-wide text-slate-400">{t("components.create_link_dialog.interval")}</div>
                  <select
                    className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 text-base outline-none focus:border-brand-sky"
                    value={interval}
                    onChange={(e) => setInterval(e.target.value)}
                  >
                    {intervals.map((it) => (
                      <option key={it.value} value={it.value}>
                        {t(it.labelKey)}
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div />
              )}
            </div>

            <div className="rounded-2xl border border-slate-200 p-4">
              <div className="text-sm font-semibold text-slate-700">{t("components.create_link_dialog.customer_fields")}</div>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setRequireEmail((v) => !v)}
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                    requireEmail ? "bg-sky-100 text-sky-700 ring-1 ring-sky-200" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {t("components.create_link_dialog.field_email")}
                </button>
                <button
                  type="button"
                  onClick={() => setRequireName((v) => !v)}
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                    requireName ? "bg-sky-100 text-sky-700 ring-1 ring-sky-200" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {t("components.create_link_dialog.field_name")}
                </button>
                <button
                  type="button"
                  onClick={() => setRequirePhone((v) => !v)}
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                    requirePhone ? "bg-sky-100 text-sky-700 ring-1 ring-sky-200" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {t("components.create_link_dialog.field_phone")}
                </button>
                <button
                  type="button"
                  onClick={() => setRequireAddress((v) => !v)}
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                    requireAddress ? "bg-sky-100 text-sky-700 ring-1 ring-sky-200" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {t("components.create_link_dialog.field_address")}
                </button>
              </div>
            </div>

            <div>
              <div className="text-xs font-semibold tracking-wide text-slate-400">{t("components.create_link_dialog.expiry_optional")}</div>
              <input
                type="date"
                className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 text-base outline-none focus:border-brand-sky"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
              />
            </div>
          </div>
        )}

        {error && <div className="mt-4 text-sm text-red-500">{error}</div>}

        <button
          type="button"
          onClick={handleCreate}
          disabled={loading}
          className={`mt-7 w-full rounded-2xl px-4 py-4 text-sm font-semibold text-white shadow-sm transition ${
            kind === "one_time"
              ? "bg-orange-300 hover:bg-orange-400"
              : "bg-sky-300 hover:bg-sky-400"
          }`}
        >
          {loading ? t("components.create_link_dialog.creating") : ctaLabel}
        </button>
      </div>
    </div>
  );
};

export default CreateLinkDialog;
