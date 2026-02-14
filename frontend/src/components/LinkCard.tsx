import type { LinkResponse } from "../lib/api";
import { useTranslation } from "react-i18next";
import PaymentLinkShare from "./PaymentLinkShare";

type LinkCardProps = {
  link: LinkResponse;
  onDisable?: (id: string) => void;
  onOpen?: (id: string) => void;
  loading?: boolean;
  showShare?: boolean;
  defaultTitle?: string;
  showInterval?: boolean;
  showEarnings?: boolean;
  mockStyle?: boolean;
};

const formatMinorUnits = (value: number) => (value / 100).toFixed(2);

const formatDate = (value?: string | null) => {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  const day = String(parsed.getDate()).padStart(2, "0");
  const month = String(parsed.getMonth() + 1).padStart(2, "0");
  const year = parsed.getFullYear();
  return `${day}-${month}-${year}`;
};

const LinkCard = ({
  link,
  onDisable,
  onOpen,
  loading,
  showShare = true,
  defaultTitle,
  showInterval = false,
  showEarnings = true,
  mockStyle = false,
}: LinkCardProps) => {
  const { t } = useTranslation();
  const resolvedDefaultTitle = defaultTitle ?? t("components.link_card.default_title");
  const isDisabled = link.status === "DISABLED";
  const handleOpen = () => {
    if (onOpen) onOpen(link.id);
  };
  const currency = (link.currency || "gbp").toUpperCase();
  const amount = `£${formatMinorUnits(link.amount)}`;
  const earnings = `£${formatMinorUnits(link.earnings_amount ?? 0)}`;
  const expiry = link.expires_at ? formatDate(link.expires_at) : "—";

  if (mockStyle) {
    return (
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm transition hover:shadow-md">
        <div className="flex items-center justify-between text-xs text-slate-500 md:text-sm">
          <div>{formatDate(link.created_at)}</div>
          {showShare && link.url && <PaymentLinkShare url={link.url} iconOnly />}
        </div>

        <div
          className={`mt-4 rounded-xl transition ${onOpen ? "cursor-pointer hover:bg-slate-50" : ""}`}
          role={onOpen ? "button" : undefined}
          tabIndex={onOpen ? 0 : undefined}
          onClick={onOpen ? handleOpen : undefined}
          onKeyDown={
            onOpen
              ? (event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    handleOpen();
                  }
                }
              : undefined
          }
        >
          <div className="text-lg font-semibold leading-tight text-slate-900 md:text-xl">{link.title ?? resolvedDefaultTitle}</div>

          <div className="mt-4 grid grid-cols-4 gap-2 text-center text-xs text-slate-700 md:text-sm">
            <div className="truncate">{currency}</div>
            <div className="truncate">{amount}</div>
            <div className="truncate">{earnings}</div>
            <div className="truncate">{expiry}</div>
          </div>
        </div>

        <div className="mt-5 flex items-center justify-between">
          <div className="w-8" />
          <div className="flex-1 flex justify-center">
            {showInterval ? (
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-emerald-100 text-emerald-600" title={t("components.link_card.recurring")}>
                <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 12a9 9 0 0 1 15.3-6.3" />
                  <path d="M21 12a9 9 0 0 1-15.3 6.3" />
                  <path d="M18 2v4h-4" />
                  <path d="M6 22v-4h4" />
                </svg>
              </span>
            ) : null}
          </div>
          {onDisable ? (
            <button
              onClick={() => onDisable(link.id)}
              className="rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600 hover:bg-slate-50 md:text-sm"
              disabled={loading || isDisabled}
            >
              {isDisabled ? t("components.link_card.disabled") : t("components.link_card.disable")}
            </button>
          ) : (
            <div className="w-16" />
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-white p-5 shadow transition hover:shadow-lg">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-sm text-slate-500">{link.currency?.toUpperCase()}</div>
          <div className="text-lg font-semibold">{link.title ?? resolvedDefaultTitle}</div>
        </div>
        {showShare && link.url && <PaymentLinkShare url={link.url} compact />}
      </div>
      <div
        className={`mt-3 rounded-xl p-2 transition ${onOpen ? "cursor-pointer hover:bg-slate-50" : ""}`}
        role={onOpen ? "button" : undefined}
        tabIndex={onOpen ? 0 : undefined}
        onClick={onOpen ? handleOpen : undefined}
        onKeyDown={
          onOpen
            ? (event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  handleOpen();
                }
              }
            : undefined
        }
      >
        <div className="mt-3 grid gap-2 text-sm text-slate-600 md:grid-cols-3">
          <div>
            <div className="text-xs text-slate-400">{t("components.link_card.amount")}</div>
            <div className="font-semibold">{formatMinorUnits(link.amount)}</div>
          </div>
          {showEarnings && (
            <div>
              <div className="text-xs text-slate-400">{t("components.link_card.earnings")}</div>
              <div className="font-semibold">{formatMinorUnits(link.earnings_amount ?? 0)}</div>
            </div>
          )}
          <div>
            <div className="text-xs text-slate-400">{showInterval ? t("components.link_card.interval") : t("components.link_card.expires")}</div>
            <div className="font-semibold">
              {showInterval
                ? link.interval ?? "—"
                : link.expires_at
                ? formatDate(link.expires_at)
                : t("components.link_card.no_expiry")}
            </div>
          </div>
        </div>
      </div>
      {(link.require_fields?.length || onDisable) && (
        <div className="mt-3 flex min-h-0 flex-wrap items-center justify-between gap-2">
          {link.require_fields && link.require_fields.length > 0 ? (
            <div className="flex flex-wrap gap-1.5 text-sm text-slate-500">
              {link.require_fields.map((field) => (
                <span
                  key={field}
                  className="rounded-md bg-slate-100 px-2 py-0.5 font-medium lowercase"
                >
                  {field}
                </span>
              ))}
            </div>
          ) : (
            <div />
          )}
          {onDisable && (
            <button
              onClick={() => onDisable(link.id)}
              className="rounded-full border border-slate-200 px-3 py-1 text-sm"
              disabled={loading || isDisabled}
            >
              {isDisabled ? t("components.link_card.disabled") : t("components.link_card.disable")}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default LinkCard;
