import { useState } from "react";
import { useTranslation } from "react-i18next";
import { signUpWithCognito, signInWithGoogle } from "../lib/auth";
import { config } from "../lib/config";
import { useLocaleNavigate } from "../lib/useLocaleNavigate";

const SignupPage = () => {
  const { t } = useTranslation();
  const { localeNavigate } = useLocaleNavigate();
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
        localeNavigate("/login", { replace: true });
      } else {
        localeNavigate(`/verify-email?email=${encodeURIComponent(email)}`, { replace: true });
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
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-brand-sky"
                required
                minLength={6}
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-500 hover:text-slate-700"
                aria-label={showPassword ? t("pages.signup.hide_password") : t("pages.signup.show_password")}
                disabled={loading}
              >
                {showPassword ? (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    className="h-5 w-5"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 3l18 18" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M10.58 10.58A2 2 0 0012 14a2 2 0 001.42-.58" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.88 5.09A10.94 10.94 0 0112 5c5.05 0 9.27 3.11 10.5 7-1.03 3.24-4.19 5.92-8.2 6.74" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6.61 6.61C4.96 7.75 3.68 9.29 3 12c.51 1.62 1.54 3.09 2.92 4.27" />
                  </svg>
                ) : (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    className="h-5 w-5"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
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
            onClick={() => localeNavigate("/login")}
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
