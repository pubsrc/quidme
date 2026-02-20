import { useAuth } from "../lib/useAuth";
import SessionLoader from "./SessionLoader";
import LocaleNavigate from "./LocaleNavigate";
export const RequireGuest = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <SessionLoader />;
  }

  if (isAuthenticated) {
    return <LocaleNavigate to="/app/dashboard" replace />;
  }

  return <>{children}</>;
};
