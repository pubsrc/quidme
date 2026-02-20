import LocaleNavigate from "./LocaleNavigate";
import { useAuth } from "../lib/useAuth";
import SessionLoader from "./SessionLoader";

export const RequireAuth = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <SessionLoader />;
  }

  if (!isAuthenticated) {
    return <LocaleNavigate to="/login" replace />;
  }

  return <>{children}</>;
};
