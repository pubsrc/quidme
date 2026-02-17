import { Routes, Route, Navigate } from "react-router-dom";
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
import { RequireAuth } from "../components/RequireAuth";
import { RequireGuest } from "../components/RequireGuest";
import { RequireNoStripeAccount } from "../components/RequireNoStripeAccount";
import { RequireStripeAccount } from "../components/RequireStripeAccount";

const App = () => {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <RequireGuest>
            <LandingPage />
          </RequireGuest>
        }
      />
      <Route
        path="/login"
        element={
          <RequireGuest>
            <LoginPage />
          </RequireGuest>
        }
      />
      <Route
        path="/signup"
        element={
          <RequireGuest>
            <SignupPage />
          </RequireGuest>
        }
      />
      <Route
        path="/verify-email"
        element={
          <RequireGuest>
            <VerifyEmailPage />
          </RequireGuest>
        }
      />
      <Route
        path="/forgot-password"
        element={
          <RequireGuest>
            <ForgotPasswordPage />
          </RequireGuest>
        }
      />
      <Route path="/callback" element={<CallbackPage />} />
      <Route
        path="/start"
        element={
          <RequireAuth>
            <RequireNoStripeAccount>
              <StartPage />
            </RequireNoStripeAccount>
          </RequireAuth>
        }
      />
      <Route
        path="/app"
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
        <Route path="payment-links" element={<PaymentLinksPage />} />
        <Route path="payment-links/:id" element={<PaymentLinkDetailsPage />} />
        <Route path="subscriptions" element={<Navigate to="/app/payment-links" replace />} />
        <Route path="customer-subscriptions" element={<CustomerSubscriptionsPage />} />
        <Route path="transactions" element={<TransactionsPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
