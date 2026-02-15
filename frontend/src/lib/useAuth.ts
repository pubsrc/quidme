import { useEffect, useState } from "react";
import { fetchAuthSession } from "aws-amplify/auth";
import { Hub } from "aws-amplify/utils";

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
    const stop = Hub.listen("auth", () => {
      checkAuth();
    }, "useAuth");

    const onVisibility = () => {
      if (document.visibilityState === "visible") {
        checkAuth();
      }
    };
    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("focus", checkAuth);

    return () => {
      isMounted = false;
      stop();
      document.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("focus", checkAuth);
    };
  }, []);

  return { isAuthenticated, isLoading };
};
