export const getDefaultCurrencyForCountry = (country: string | null | undefined): string => {
  const normalized = (country || "").toUpperCase();

  if (normalized === "GB") return "gbp";
  if (
    normalized === "DE" ||
    normalized === "AT" ||
    normalized === "IT" ||
    normalized === "GR" ||
    normalized === "XK" ||
    normalized === "BG" ||
    normalized === "AL"
  ) {
    return "eur";
  }
  if (normalized === "RO") return "ron";

  return "gbp";
};
