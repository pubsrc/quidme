import { Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../lib/useAuth";
export const RequireGuest = ({ children }: { children: React.ReactNode }) => {
  const { t } = useTranslation();
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-slate-500">{t("components.require.checking_session")}</div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/app/offerings" replace />;
  }

  return <>{children}</>;
};
