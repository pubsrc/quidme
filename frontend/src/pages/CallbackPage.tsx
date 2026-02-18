import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { fetchAuthSession } from "aws-amplify/auth";
import { useTranslation } from "react-i18next";

const CallbackPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  useEffect(() => {
    const finalize = async () => {
      try {
        const session = await fetchAuthSession();
        if (session.tokens?.idToken) {
          navigate("/app/offerings", { replace: true });
        } else {
          navigate("/login", { replace: true });
        }
      } catch {
        navigate("/login", { replace: true });
      }
    };

    finalize();
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-slate-600">{t("pages.callback.signing_in")}</div>
    </div>
  );
};

export default CallbackPage;
