import { Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAccountStatus } from "../lib/useAccountStatus";
import SessionLoader from "./SessionLoader";

export const RequireNoStripeAccount = ({ children }: { children: React.ReactNode }) => {
  const { t } = useTranslation();
  const { status, isLoading, error, refresh, accountKnown } = useAccountStatus();

  if (isLoading || !accountKnown) {
    return <SessionLoader />;
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
          <div className="text-sm font-semibold text-slate-900">{t("components.require.account_check_failed")}</div>
          <div className="mt-2 text-sm text-slate-600">{error}</div>
          <button
            type="button"
            onClick={refresh}
            className="mt-4 rounded-xl bg-amber-500 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-600"
          >
            {t("components.require.retry")}
          </button>
        </div>
      </div>
    );
  }

  if (status.has_connected_account) {
    return <Navigate to="/app/offerings" replace />;
  }

  return <>{children}</>;
};
