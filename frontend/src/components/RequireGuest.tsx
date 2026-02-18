import { Navigate } from "react-router-dom";
import { useAuth } from "../lib/useAuth";
import SessionLoader from "./SessionLoader";
export const RequireGuest = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <SessionLoader />;
  }

  if (isAuthenticated) {
    return <Navigate to="/app/offerings" replace />;
  }

  return <>{children}</>;
};
