import { Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAccountStatus } from "../lib/useAccountStatus";

export const RequireNoStripeAccount = ({ children }: { children: React.ReactNode }) => {
  const { t } = useTranslation();
  const { status, isLoading } = useAccountStatus();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-slate-500">{t("components.require.checking_session")}</div>
      </div>
    );
  }

  if (status.has_connected_account) {
    return <Navigate to="/app/payment-links" replace />;
  }

  return <>{children}</>;
};

