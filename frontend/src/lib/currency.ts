export const getDefaultCurrencyForCountry = (country: string | null | undefined): string => {
  const normalized = (country || "").toUpperCase();

  if (normalized === "GB") return "gbp";
  if (normalized === "DE" || normalized === "AT" || normalized === "IT" || normalized === "GR" || normalized === "XK") {
    return "eur";
  }
  if (normalized === "BG") return "bgn";
  if (normalized === "RO") return "ron";
  if (normalized === "AL") return "all";

  return "gbp";
};
