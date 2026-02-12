import { Navigate } from "react-router-dom";
import { useAuth } from "../lib/useAuth";
export const RequireGuest = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-slate-500">Checking session...</div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/app/start" replace />;
  }

  return <>{children}</>;
};
