export const SUPPORTED_LOCALES = ["en", "tr"] as const;

export type AppLocale = (typeof SUPPORTED_LOCALES)[number];

export const resolveLocale = (value: string | null | undefined): AppLocale | null => {
  if (!value) return null;
  return SUPPORTED_LOCALES.includes(value as AppLocale) ? (value as AppLocale) : null;
};

export const getLocaleFromPathname = (pathname: string): AppLocale | null => {
  const firstSegment = pathname.split("/").filter(Boolean)[0] ?? "";
  return resolveLocale(firstSegment);
};

export const stripLocalePrefix = (pathname: string): string => {
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) return "/";
  const maybeLocale = resolveLocale(segments[0]);
  const remaining = maybeLocale ? segments.slice(1) : segments;
  return remaining.length > 0 ? `/${remaining.join("/")}` : "/";
};

export const replaceLocaleInPathname = (pathname: string, locale: AppLocale): string => {
  const stripped = stripLocalePrefix(pathname);
  return stripped === "/" ? `/${locale}` : `/${locale}${stripped}`;
};

export const localizePath = (targetPath: string, currentPathname: string, fallbackLocale: AppLocale = "en"): string => {
  const locale = getLocaleFromPathname(currentPathname) ?? fallbackLocale;
  const normalizedTarget = targetPath.startsWith("/") ? targetPath : `/${targetPath}`;
  return replaceLocaleInPathname(normalizedTarget, locale);
};
