import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { signOutWithCognito } from "../lib/auth";

/**
 * Start page: create Stripe Connect account.
 * No API calls until user clicks the button (authorization gate is backend 403).
 */
const StartPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogout = async () => {
    try {
      await signOutWithCognito();
      navigate("/", { replace: true });
    } catch {
      navigate("/", { replace: true });
    }
  };

  const handleStart = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.connectAccount();
      navigate("/app/payment-links", { replace: true });
    } catch (err) {
      setError("Unable to create your account. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-lg rounded-2xl bg-white p-8 shadow">
        <h1 className="text-2xl font-semibold text-brand-navy">Start selling with Quidme</h1>
        <p className="mt-3 text-sm text-slate-600">
          Create your Stripe Express account with minimal details. Country selection is currently
          limited to the United Kingdom.
        </p>

        <div className="mt-6 flex items-center gap-3 rounded-xl border border-slate-200 p-4">
          <div className="text-2xl">🇬🇧</div>
          <div>
            <div className="text-sm font-semibold">United Kingdom</div>
            <div className="text-xs text-slate-500">Express account</div>
          </div>
        </div>

        {error && <div className="mt-4 text-sm text-red-500">{error}</div>}

        <div className="mt-6 flex justify-between">
          <button
            onClick={handleLogout}
            className="rounded-full border border-slate-300 px-5 py-2 text-sm text-slate-600"
            disabled={loading}
          >
            Log out
          </button>
          <div className="flex gap-3">
            <button
              onClick={() => navigate("/")}
              className="rounded-full border border-slate-300 px-5 py-2 text-sm"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              onClick={handleStart}
              className="rounded-full bg-brand-sky px-5 py-2 text-sm font-semibold text-white"
              disabled={loading}
            >
              {loading ? "Starting..." : "OK"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StartPage;
