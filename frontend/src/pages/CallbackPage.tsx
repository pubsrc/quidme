import { useEffect } from "react";
import { fetchAuthSession } from "aws-amplify/auth";
import { useTranslation } from "react-i18next";
import { useLocaleNavigate } from "../lib/useLocaleNavigate";

const CallbackPage = () => {
  const { t } = useTranslation();
  const { localeNavigate } = useLocaleNavigate();

  useEffect(() => {
    const finalize = async () => {
      try {
        const session = await fetchAuthSession();
        if (session.tokens?.idToken) {
          localeNavigate("/app/dashboard", { replace: true });
        } else {
          localeNavigate("/login", { replace: true });
        }
      } catch {
        localeNavigate("/login", { replace: true });
      }
    };

    finalize();
  }, [localeNavigate]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-slate-600">{t("pages.callback.signing_in")}</div>
    </div>
  );
};

export default CallbackPage;
