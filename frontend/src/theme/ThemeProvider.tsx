import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type AppTheme = "classic" | "gold-cute" | "dark";

const THEME_STORAGE_KEY = "quidme-theme";

type ThemeContextValue = {
  theme: AppTheme;
  setTheme: (value: AppTheme) => void;
  toggleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

const getInitialTheme = (): AppTheme => {
  if (typeof window === "undefined") return "gold-cute";
  const saved = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (saved === "gold-cute") return "gold-cute";
  if (saved === "dark") return "dark";
  return "gold-cute";
};

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const [theme, setTheme] = useState<AppTheme>(getInitialTheme);

  useEffect(() => {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    if (theme === "classic") {
      document.documentElement.removeAttribute("data-theme");
    } else {
      document.documentElement.setAttribute("data-theme", theme);
    }
  }, [theme]);

  const value = useMemo(
    () => ({
      theme,
      setTheme,
      toggleTheme: () => setTheme((current) => (current === "classic" ? "gold-cute" : "classic")),
    }),
    [theme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used inside ThemeProvider");
  }
  return context;
};
