import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { signUpWithCognito, signInWithGoogle } from "../lib/auth";
import { config } from "../lib/config";

const SignupPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [googleLoading, setGoogleLoading] = useState(false);
  const showGoogle = Boolean(config.cognitoOauthDomain);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await signUpWithCognito(email, password);
      if (response.confirmed) {
        navigate("/login", { replace: true });
      } else {
        navigate(`/verify-email?email=${encodeURIComponent(email)}`, { replace: true });
      }
    } catch (err: any) {
      setError(err?.message || t("pages.signup.errors.signup_failed"));
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async () => {
    setGoogleLoading(true);
    setError(null);
    try {
      await signInWithGoogle();
    } catch (err: any) {
      setError(err?.message || t("pages.signup.errors.google_failed"));
      setGoogleLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow">
        <h1 className="text-2xl font-semibold text-brand-navy">{t("pages.signup.title")}</h1>
        <p className="mt-2 text-sm text-slate-600">{t("pages.signup.subtitle")}</p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="text-sm font-medium text-slate-700">{t("pages.signup.email")}</label>
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
            <label className="text-sm font-medium text-slate-700">{t("pages.signup.password")}</label>
            <input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-sky"
              required
              minLength={6}
              disabled={loading}
            />
            <label className="mt-2 inline-flex items-center gap-2 text-xs font-medium text-slate-600">
              <input
                type="checkbox"
                checked={showPassword}
                onChange={(e) => setShowPassword(e.target.checked)}
                disabled={loading}
                className="h-4 w-4 rounded border-slate-300 text-brand-sky focus:ring-brand-sky"
              />
              {t("pages.signup.show_password")}
            </label>
          </div>

          {error && <div className="text-sm text-red-500">{error}</div>}

          <button
            type="submit"
            className="w-full rounded-full bg-brand-sky px-4 py-3 text-sm font-semibold text-white"
            disabled={loading}
          >
            {loading ? t("pages.signup.creating") : t("pages.signup.create_account")}
          </button>
        </form>

        {showGoogle && (
          <button
            type="button"
            onClick={handleGoogle}
            className="mt-4 w-full rounded-full border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700"
            disabled={loading || googleLoading}
          >
            {googleLoading ? t("pages.signup.redirecting") : t("pages.signup.continue_google")}
          </button>
        )}

        <div className="mt-6 text-center text-sm text-slate-600">
          {t("pages.signup.already_have")}{" "}
          <button
            type="button"
            onClick={() => navigate("/login")}
            className="text-brand-sky hover:underline"
          >
            {t("pages.signup.sign_in")}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;
