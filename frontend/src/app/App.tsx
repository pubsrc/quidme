import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Routes, Route, Navigate, Outlet, useLocation, useParams } from "react-router-dom";
import LandingPage from "../pages/LandingPage";
import LoginPage from "../pages/LoginPage";
import SignupPage from "../pages/SignupPage";
import VerifyEmailPage from "../pages/VerifyEmailPage";
import ForgotPasswordPage from "../pages/ForgotPasswordPage";
import CallbackPage from "../pages/CallbackPage";
import DashboardLayout from "../layouts/DashboardLayout";
import DashboardPage from "../pages/DashboardPage";
import StartPage from "../pages/StartPage";
import PaymentLinksPage from "../pages/PaymentLinksPage";
import PaymentLinkDetailsPage from "../pages/PaymentLinkDetailsPage";
import CustomerSubscriptionsPage from "../pages/CustomerSubscriptionsPage";
import TransactionsPage from "../pages/TransactionsPage";
import ProfilePage from "../pages/ProfilePage";
import SettingsPage from "../pages/SettingsPage";
import QuickPaymentsPage from "../pages/QuickPaymentsPage";
import { RequireAuth } from "../components/RequireAuth";
import { RequireGuest } from "../components/RequireGuest";
import { RequireNoStripeAccount } from "../components/RequireNoStripeAccount";
import { RequireStripeAccount } from "../components/RequireStripeAccount";
import { LOCALE_STORAGE_KEY } from "./i18n";
import { replaceLocaleInPathname, resolveLocale } from "../lib/localeRouting";

const LocaleShell = () => {
  const { i18n } = useTranslation();
  const { locale } = useParams<{ locale: string }>();
  const location = useLocation();
  const normalized = resolveLocale(locale);

  useEffect(() => {
    if (!normalized) return;
    if (i18n.resolvedLanguage !== normalized) {
      void i18n.changeLanguage(normalized);
    }
    localStorage.setItem(LOCALE_STORAGE_KEY, normalized);
  }, [i18n, normalized]);

  if (!normalized) {
    const [, , ...remaining] = location.pathname.split("/");
    const normalizedPath = remaining.length > 0 ? `/${remaining.join("/")}` : "";
    return <Navigate to={`/en${normalizedPath}${location.search}`} replace />;
  }

  return <Outlet />;
};

const RedirectToPreferredLocale = () => {
  const { i18n } = useTranslation();
  const location = useLocation();
  const current = resolveLocale(i18n.resolvedLanguage) ?? "en";
  const targetPath = replaceLocaleInPathname(location.pathname, current);
  const target = `${targetPath}${location.search}`;
  return <Navigate to={target} replace />;
};

const App = () => {
  return (
    <Routes>
      <Route path="/:locale" element={<LocaleShell />}>
        <Route
          index
          element={
            <RequireGuest>
              <LandingPage />
            </RequireGuest>
          }
        />
        <Route
          path="login"
          element={
            <RequireGuest>
              <LoginPage />
            </RequireGuest>
          }
        />
        <Route
          path="signup"
          element={
            <RequireGuest>
              <SignupPage />
            </RequireGuest>
          }
        />
        <Route
          path="verify-email"
          element={
            <RequireGuest>
              <VerifyEmailPage />
            </RequireGuest>
          }
        />
        <Route
          path="forgot-password"
          element={
            <RequireGuest>
              <ForgotPasswordPage />
            </RequireGuest>
          }
        />
        <Route path="callback" element={<CallbackPage />} />
        <Route path="dashboard" element={<Navigate to="../app/dashboard" replace />} />
        <Route path="offerings" element={<Navigate to="../app/offerings" replace />} />
        <Route path="transactions" element={<Navigate to="../app/transactions" replace />} />
        <Route path="subscribers" element={<Navigate to="../app/subscribers" replace />} />
        <Route path="profile" element={<Navigate to="../app/profile" replace />} />
        <Route path="settings" element={<Navigate to="../app/settings" replace />} />
        <Route
          path="start"
          element={
            <RequireAuth>
              <RequireNoStripeAccount>
                <StartPage />
              </RequireNoStripeAccount>
            </RequireAuth>
          }
        />
        <Route
          path="app"
          element={
            <RequireAuth>
              <RequireStripeAccount>
                <DashboardLayout />
              </RequireStripeAccount>
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="quick-payments" element={<QuickPaymentsPage />} />
          <Route path="offerings" element={<PaymentLinksPage />} />
          <Route path="offerings/:id" element={<PaymentLinkDetailsPage />} />
          <Route path="subscriptions" element={<Navigate to="../offerings" replace />} />
          <Route path="subscribers" element={<CustomerSubscriptionsPage />} />
          <Route path="customer-subscriptions" element={<CustomerSubscriptionsPage />} />
          <Route path="transactions" element={<TransactionsPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to=".." replace />} />
      </Route>
      <Route path="*" element={<RedirectToPreferredLocale />} />
    </Routes>
  );
};

export default App;
