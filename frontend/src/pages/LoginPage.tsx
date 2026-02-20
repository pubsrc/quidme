import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Eye, EyeOff } from "lucide-react";
import { signInWithCognito, signInWithGoogle } from "../lib/auth";
import { config } from "../lib/config";
import { useLocaleNavigate } from "../lib/useLocaleNavigate";

const LoginPage = () => {
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
      await signInWithCognito(email, password);
      localeNavigate("/app/dashboard", { replace: true });
    } catch (err: any) {
      if (err?.code === "USER_NOT_CONFIRMED") {
        localeNavigate(`/verify-email?email=${encodeURIComponent(email)}`, { replace: true });
        return;
      }
      setError(err?.message || t("pages.login.errors.sign_in_failed"));
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
      setError(err?.message || t("pages.login.errors.google_failed"));
      setGoogleLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow">
        <h1 className="text-2xl font-semibold text-brand-navy">{t("pages.login.title")}</h1>
        <p className="mt-2 text-sm text-slate-600">{t("pages.login.subtitle")}</p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="text-sm font-medium text-slate-700">{t("pages.login.email")}</label>
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
            <label className="text-sm font-medium text-slate-700">{t("pages.login.password")}</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-brand-sky"
                required
                disabled={loading}
                minLength={6}
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-500 hover:text-slate-700"
                aria-label={showPassword ? t("pages.login.hide_password") : t("pages.login.show_password")}
                disabled={loading}
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5" />
                ) : (
                  <Eye className="h-5 w-5" />
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
            {loading ? t("pages.login.signing_in") : t("pages.login.sign_in")}
          </button>
        </form>

        {showGoogle && (
          <button
            type="button"
            onClick={handleGoogle}
            className="mt-4 w-full rounded-full border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700"
            disabled={loading || googleLoading}
          >
            {googleLoading ? t("pages.login.redirecting") : t("pages.login.continue_google")}
          </button>
        )}

        <div className="mt-6 flex items-center justify-between text-sm text-slate-600">
          <button
            type="button"
            onClick={() => localeNavigate("/forgot-password")}
            className="text-brand-sky hover:underline"
          >
            {t("pages.login.forgot_password")}
          </button>
          <button
            type="button"
            onClick={() => localeNavigate("/signup")}
            className="text-brand-sky hover:underline"
          >
            {t("pages.login.create_account")}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
