import { useEffect, useState } from "react";
import { fetchAuthSession } from "aws-amplify/auth";

export const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const checkAuth = async () => {
      try {
        const session = await fetchAuthSession();
        const authed = !!session.tokens?.idToken;
        if (isMounted) {
          setIsAuthenticated(authed);
          setIsLoading(false);
        }
      } catch {
        if (isMounted) {
          setIsAuthenticated(false);
          setIsLoading(false);
        }
      }
    };

    checkAuth();
    const interval = setInterval(checkAuth, 5000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return { isAuthenticated, isLoading };
};
