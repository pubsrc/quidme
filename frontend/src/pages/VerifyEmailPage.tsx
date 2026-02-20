import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { confirmSignUpWithCognito, resendConfirmationCode } from "../lib/auth";
import { useLocaleNavigate } from "../lib/useLocaleNavigate";

const VerifyEmailPage = () => {
  const { t } = useTranslation();
  const { localeNavigate } = useLocaleNavigate();
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
      setMessage(t("pages.verify_email.messages.verified"));
      setTimeout(() => localeNavigate("/login", { replace: true }), 1500);
    } catch (err: any) {
      setError(err?.message || t("pages.verify_email.errors.verify_failed"));
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
      setMessage(t("pages.verify_email.messages.resent"));
    } catch (err: any) {
      setError(err?.message || t("pages.verify_email.errors.resend_failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow">
        <h1 className="text-2xl font-semibold text-brand-navy">{t("pages.verify_email.title")}</h1>
        <p className="mt-2 text-sm text-slate-600">{t("pages.verify_email.subtitle")}</p>

        <form className="mt-6 space-y-4" onSubmit={handleVerify}>
          <div>
            <label className="text-sm font-medium text-slate-700">{t("pages.verify_email.email")}</label>
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
            <label className="text-sm font-medium text-slate-700">{t("pages.verify_email.code")}</label>
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
            {loading ? t("pages.verify_email.verifying") : t("pages.verify_email.verify")}
          </button>
        </form>

        <button
          type="button"
          onClick={handleResend}
          className="mt-4 w-full rounded-full border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700"
          disabled={loading}
        >
          {t("pages.verify_email.resend")}
        </button>
      </div>
    </div>
  );
};

export default VerifyEmailPage;
