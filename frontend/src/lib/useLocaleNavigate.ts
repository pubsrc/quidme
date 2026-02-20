import { useCallback } from "react";
import { NavigateOptions, To, useLocation, useNavigate } from "react-router-dom";
import { localizePath } from "./localeRouting";

const isExternalUrl = (value: string) => /^([a-z][a-z\d+\-.]*:)?\/\//i.test(value);

const localizeTo = (to: To, pathname: string): To => {
  if (typeof to !== "string") return to;
  if (isExternalUrl(to) || to.startsWith("#")) return to;
  if (!to.startsWith("/")) return to;
  return localizePath(to, pathname);
};

export const useLocaleNavigate = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const localeNavigate = useCallback(
    (to: To, options?: NavigateOptions) => {
      navigate(localizeTo(to, location.pathname), options);
    },
    [navigate, location.pathname]
  );

  const localeTo = useCallback((to: To) => localizeTo(to, location.pathname), [location.pathname]);

  return { localeNavigate, localeTo };
};

