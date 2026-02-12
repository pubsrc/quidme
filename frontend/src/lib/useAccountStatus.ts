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
      setAccount(undefined);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const has_connected_account = account != null;
  const requires_onboarding = has_connected_account && account!.status !== "VERIFIED";
  const payouts_enabled = account?.status === "VERIFIED";

  return {
    account: account ?? null,
    status: {
      has_connected_account,
      requires_onboarding: has_connected_account ? requires_onboarding : false,
      payouts_enabled: payouts_enabled ?? false,
    },
    isLoading,
    error,
    refresh,
  };
};
