import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { requestPasswordReset, confirmPasswordReset } from "../lib/auth";

const ForgotPasswordPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [step, setStep] = useState<"request" | "confirm">("request");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRequest = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setLoading(true);

    try {
      await requestPasswordReset(email);
      setMessage(t("pages.forgot_password.messages.sent"));
      setStep("confirm");
    } catch (err: any) {
      setError(err?.message || t("pages.forgot_password.errors.send_failed"));
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setLoading(true);

    try {
      await confirmPasswordReset(email, code, newPassword);
      setMessage(t("pages.forgot_password.messages.updated"));
      setTimeout(() => navigate("/login", { replace: true }), 1500);
    } catch (err: any) {
      setError(err?.message || t("pages.forgot_password.errors.reset_failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow">
        <h1 className="text-2xl font-semibold text-brand-navy">{t("pages.forgot_password.title")}</h1>
        <p className="mt-2 text-sm text-slate-600">
          {step === "request"
            ? t("pages.forgot_password.subtitle_request")
            : t("pages.forgot_password.subtitle_confirm")}
        </p>

        {step === "request" ? (
          <form className="mt-6 space-y-4" onSubmit={handleRequest}>
            <div>
              <label className="text-sm font-medium text-slate-700">{t("pages.forgot_password.email")}</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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
              {loading ? t("pages.forgot_password.sending") : t("pages.forgot_password.send_code")}
            </button>
          </form>
        ) : (
          <form className="mt-6 space-y-4" onSubmit={handleConfirm}>
            <div>
              <label className="text-sm font-medium text-slate-700">{t("pages.forgot_password.email")}</label>
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
              <label className="text-sm font-medium text-slate-700">{t("pages.forgot_password.reset_code")}</label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-sky"
                required
                disabled={loading}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">{t("pages.forgot_password.new_password")}</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-brand-sky"
                  required
                  minLength={6}
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-500 hover:text-slate-700"
                  aria-label={showPassword ? t("pages.forgot_password.hide_password") : t("pages.forgot_password.show_password")}
                  disabled={loading}
                >
                  <span className="text-xs font-semibold">{showPassword ? t("pages.forgot_password.hide") : t("pages.forgot_password.show")}</span>
                </button>
              </div>
            </div>

            {error && <div className="text-sm text-red-500">{error}</div>}
            {message && <div className="text-sm text-emerald-600">{message}</div>}

            <button
              type="submit"
              className="w-full rounded-full bg-brand-sky px-4 py-3 text-sm font-semibold text-white"
              disabled={loading}
            >
              {loading ? t("pages.forgot_password.updating") : t("pages.forgot_password.update_password")}
            </button>
          </form>
        )}

        <button
          type="button"
          onClick={() => navigate("/login")}
          className="mt-6 w-full rounded-full border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700"
        >
          {t("pages.forgot_password.back_login")}
        </button>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
