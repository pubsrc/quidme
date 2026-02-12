import type { LinkResponse } from "../lib/api";
import PaymentLinkShare from "./PaymentLinkShare";

type SubscriptionLinkCardProps = {
  link: LinkResponse;
  onDisable?: (id: string) => void;
  loading?: boolean;
};

const formatMinorUnits = (value: number) => (value / 100).toFixed(2);

const formatDate = (value?: string | null) => {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return parsed.toLocaleDateString();
};

const SubscriptionLinkCard = ({ link, onDisable, loading }: SubscriptionLinkCardProps) => {
  const isDisabled = link.status === "DISABLED";

  return (
    <div className="rounded-2xl bg-white p-5 shadow transition hover:shadow-lg">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <div>{formatDate(link.created_at)}</div>
        {link.url && <PaymentLinkShare url={link.url} />}
      </div>
      <div className="mt-3 rounded-xl p-2">
        <div>
          <div className="text-sm text-slate-500">{link.currency?.toUpperCase()}</div>
          <div className="text-lg font-semibold">{link.title ?? "Subscription"}</div>
          {link.description && <div className="mt-1 text-sm text-slate-500">{link.description}</div>}
        </div>
        <div className="mt-3 grid gap-2 text-sm text-slate-600 md:grid-cols-4">
          <div>
            <div className="text-xs text-slate-400">Amount</div>
            <div className="font-semibold">{formatMinorUnits(link.amount)}</div>
          </div>
          <div>
            <div className="text-xs text-slate-400">Interval</div>
            <div className="font-semibold">{link.interval ?? "—"}</div>
          </div>
          <div>
            <div className="text-xs text-slate-400">Status</div>
            <div className="font-semibold">{link.status ?? "—"}</div>
          </div>
          <div>
            <div className="text-xs text-slate-400">Expires</div>
            <div className="font-semibold">
              {link.expires_at ? new Date(link.expires_at).toLocaleDateString() : "No expiry"}
            </div>
          </div>
        </div>
      </div>
      {onDisable && (
        <div className="mt-3 flex justify-end">
          <button
            onClick={() => onDisable(link.id)}
            className="rounded-full border border-slate-200 px-3 py-1 text-xs"
            disabled={loading || isDisabled}
          >
            {isDisabled ? "Disabled" : "Disable"}
          </button>
        </div>
      )}
    </div>
  );
};

export default SubscriptionLinkCard;
