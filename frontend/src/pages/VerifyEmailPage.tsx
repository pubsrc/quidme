import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { confirmSignUpWithCognito, resendConfirmationCode } from "../lib/auth";

const VerifyEmailPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialEmail = searchParams.get("email") ?? "";

  const [email, setEmail] = useState(initialEmail);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleVerify = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setLoading(true);

    try {
      await confirmSignUpWithCognito(email, code);
      setMessage("Email verified. You can now sign in.");
      setTimeout(() => navigate("/login", { replace: true }), 1500);
    } catch (err: any) {
      setError(err?.message || "Verification failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError(null);
    setMessage(null);
    setLoading(true);

    try {
      await resendConfirmationCode(email);
      setMessage("We sent a new verification code.");
    } catch (err: any) {
      setError(err?.message || "Unable to resend code.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow">
        <h1 className="text-2xl font-semibold text-brand-navy">Verify your email</h1>
        <p className="mt-2 text-sm text-slate-600">
          Enter the verification code sent to your inbox.
        </p>

        <form className="mt-6 space-y-4" onSubmit={handleVerify}>
          <div>
            <label className="text-sm font-medium text-slate-700">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-sky"
              required
              disabled={loading}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Verification code</label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-sky"
              required
              disabled={loading}
            />
          </div>

          {error && <div className="text-sm text-red-500">{error}</div>}
          {message && <div className="text-sm text-emerald-600">{message}</div>}

          <button
            type="submit"
            className="w-full rounded-full bg-brand-sky px-4 py-3 text-sm font-semibold text-white"
            disabled={loading}
          >
            {loading ? "Verifying..." : "Verify email"}
          </button>
        </form>

        <button
          type="button"
          onClick={handleResend}
          className="mt-4 w-full rounded-full border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700"
          disabled={loading}
        >
          Resend code
        </button>
      </div>
    </div>
  );
};

export default VerifyEmailPage;
