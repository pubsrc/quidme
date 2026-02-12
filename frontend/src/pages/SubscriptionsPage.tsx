import { useEffect, useState } from "react";
import { api, type LinkResponse } from "../lib/api";
import SubscriptionLinkCard from "../components/SubscriptionLinkCard";

const SubscriptionsPage = () => {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("10.00");
  const [currency, setCurrency] = useState("gbp");
  const [interval, setInterval] = useState("month");
  const [links, setLinks] = useState<LinkResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingLinks, setIsLoadingLinks] = useState(false);
  const [showDialog, setShowDialog] = useState(false);
  const [expiresAt, setExpiresAt] = useState("");
  const [requireName, setRequireName] = useState(true);
  const [requireEmail, setRequireEmail] = useState(true);
  const [requireAddress, setRequireAddress] = useState(false);
  const [requirePhone, setRequirePhone] = useState(false);
  const [descriptionFocused, setDescriptionFocused] = useState(false);

  const currencies = [
    { code: "gbp", label: "GBP — British Pound", flag: "🇬🇧" },
    { code: "eur", label: "EUR — Euro", flag: "🇪🇺" },
    { code: "usd", label: "USD — US Dollar", flag: "🇺🇸" },
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

  useEffect(() => {
    const fetchLinks = async () => {
      setIsLoadingLinks(true);
      setError(null);
      try {
        const response = await api.listSubscriptions();
        setLinks(response || []);
      } catch (err: any) {
        setError(err?.message || "Unable to load subscriptions.");
      } finally {
        setIsLoadingLinks(false);
      }
    };

    fetchLinks();
  }, []);


  const handleCreate = async () => {
    setLoading(true);
    setError(null);
    try {
      if (!title.trim()) {
        throw new Error("Please add a title.");
      }
      const amountMinor = toMinorUnits(amount);
      if (!amountMinor) {
        throw new Error("Enter a valid amount (up to 2 decimals).");
      }
      const normalizedTitle = title.trim();
      const normalizedDescription = description.trim() || undefined;
      const payload = {
        title: normalizedTitle,
        description: normalizedDescription,
        amount: amountMinor,
        currency,
        interval,
        expires_at: expiresAt || undefined,
        require_name: requireName,
        require_email: requireEmail,
        require_address: requireAddress,
        require_phone: requirePhone,
      };
      const response = await api.createSubscription(payload);
      setLinks((prev) => [response, ...prev]);
      setTitle("");
      setDescription("");
      setAmount("10.00");
      setCurrency("gbp");
      setInterval("month");
      setExpiresAt("");
      setRequireName(true);
      setRequireEmail(true);
      setRequireAddress(false);
      setRequirePhone(false);
      setShowDialog(false);
    } catch (err: any) {
      setError(err?.message || "Unable to create subscription checkout.");
    } finally {
      setLoading(false);
    }
  };

  const handleDisable = async (subscriptionId: string) => {
    setLoading(true);
    setError(null);
    try {
      await api.disableSubscription(subscriptionId);
      setLinks((prev) =>
        prev.map((link) => (link.id === subscriptionId ? { ...link, status: "DISABLED" } : link))
      );
    } catch (err: any) {
      setError(err?.message || "Unable to disable link.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-brand-navy">Subscription Products</h2>
          <p className="text-sm text-slate-500">Create recurring subscription checkouts for your products.</p>
        </div>
        <button
          onClick={() => setShowDialog(true)}
          className="rounded-full bg-brand-sky px-4 py-2 text-sm font-semibold text-white"
        >
          New subscription product
        </button>
      </div>

      <div className="space-y-4">
        {isLoadingLinks && (
          <div className="rounded-2xl bg-white p-6 text-sm text-slate-500 shadow">
            Loading subscriptions...
          </div>
        )}
        {links.map((link) => (
          <SubscriptionLinkCard key={link.id} link={link} onDisable={handleDisable} loading={loading} />
        ))}
        {links.length === 0 && !isLoadingLinks && (
          <div className="rounded-2xl bg-white p-6 text-sm text-slate-500 shadow">
            No subscription products yet. Create your first one.
          </div>
        )}
      </div>

      {showDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-brand-navy">New subscription product</h3>
              <button
                onClick={() => setShowDialog(false)}
                className="text-sm text-slate-500 hover:text-slate-700"
              >
                Close
              </button>
            </div>
            <div className="mt-4 space-y-3">
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                placeholder="Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
              <textarea
                className={`w-full rounded-lg border border-slate-200 px-3 py-2 transition-all duration-200 ${
                  descriptionFocused ? "min-h-[140px]" : "min-h-[80px]"
                }`}
                placeholder="Description (optional)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                onFocus={() => setDescriptionFocused(true)}
                onBlur={() => setDescriptionFocused(false)}
              />
              <div className="flex gap-3">
                <input
                  type="number"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2"
                  placeholder="Amount"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  step="0.01"
                  min="0"
                />
                <select
                  className="rounded-lg border border-slate-200 px-3 py-2"
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                >
                  {currencies.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.flag} {item.label}
                    </option>
                  ))}
                </select>
              </div>
              <select
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={interval}
                onChange={(e) => setInterval(e.target.value)}
              >
                <option value="day">Daily</option>
                <option value="week">Weekly</option>
                <option value="month">Monthly</option>
                <option value="year">Yearly</option>
              </select>
              <input
                type="date"
                className="w-full rounded-lg border border-slate-200 px-3 py-2"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
              />

              <div className="rounded-xl border border-slate-200 p-4">
                <div className="text-sm font-semibold text-slate-700">Customer details</div>
                <div className="mt-3 grid gap-2 text-sm text-slate-600">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={requireName}
                      onChange={(e) => setRequireName(e.target.checked)}
                    />
                    Name
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={requireEmail}
                      onChange={(e) => setRequireEmail(e.target.checked)}
                    />
                    Email
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={requireAddress}
                      onChange={(e) => setRequireAddress(e.target.checked)}
                    />
                    Address
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={requirePhone}
                      onChange={(e) => setRequirePhone(e.target.checked)}
                    />
                    Phone
                  </label>
                </div>
              </div>

              {error && <div className="text-sm text-red-500">{error}</div>}
              <button
                onClick={handleCreate}
                disabled={loading}
                className="w-full rounded-full bg-brand-sky px-4 py-2 text-sm font-semibold text-white"
              >
                {loading ? "Creating..." : "Create subscription"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SubscriptionsPage;
