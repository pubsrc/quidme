import { useCallback, useEffect, useState } from "react";
import { api, type Account } from "./api";

export type { Account };

export const useAccountStatus = () => {
  const [account, setAccount] = useState<Account | null | undefined>(undefined); // undefined = loading, null = no account
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.getAccount();
      setAccount(response);
    } catch (err: any) {
      setError(err?.message || "Unable to load account");
      // Keep the last-known account value. If we have no prior value, `account`
      // remains `undefined` and callers should treat that as an unknown state.
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const accountKnown = account !== undefined;
  const has_connected_account = accountKnown && account !== null;
  const requires_onboarding = has_connected_account && account.status !== "VERIFIED";
  const payouts_enabled = has_connected_account && account.status === "VERIFIED";

  return {
    account: accountKnown ? account : null,
    accountKnown,
    status: {
      has_connected_account,
      requires_onboarding: has_connected_account ? requires_onboarding : false,
      payouts_enabled,
    },
    isLoading,
    error,
    refresh,
  };
};
