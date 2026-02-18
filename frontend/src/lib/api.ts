import { config } from "./config";
import { getIdToken } from "./auth";

export type Account = {
  stripe_account_id: string;
  country: string;
  status: string; // NEW | RESTRICTED | VERIFIED
  created_at: string;
  pending_earnings?: Record<string, number>; // currency -> amount in minor units
  earnings?: Record<string, number>; // currency -> amount in minor units
};

export type TransactionItem = {
  id: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
  refunded?: boolean;
  refund_status?: string | null;
  customer_name?: string | null;
  customer_email?: string | null;
  customer_phone?: string | null;
  customer_address?: string | null;
};

const withAuth = async (init: RequestInit = {}): Promise<RequestInit> => {
  const idToken = await getIdToken();
  const headers: Record<string, string> = { ...(init.headers as Record<string, string> | undefined) };

  if (init.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  if (idToken) {
    headers.Authorization = `Bearer ${idToken}`;
  }

  return {
    ...init,
    headers,
  };
};

/** API base URL including version prefix (e.g. http://localhost:8000/api/v1). */
const base = `${config.apiBaseUrl.replace(/\/$/, "")}/api/v1`;

const STRIPE_ACCOUNT_REQUIRED_ERROR_CODE = "STRIPE_ACCOUNT_REQUIRED";

async function authFetch(input: string, init?: RequestInit): Promise<Response> {
  return fetch(input, init);
}

const detailToMessage = (detail: unknown): string => {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((entry: any) => {
        if (typeof entry?.msg === "string") return entry.msg;
        if (typeof entry === "string") return entry;
        return JSON.stringify(entry);
      })
      .join(", ");
  }
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  return "Request failed";
};

const errorMessageFromResponse = async (res: Response, fallback: string): Promise<string> => {
  try {
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const body = await res.json();
      if (body && typeof body === "object" && "detail" in body) {
        return detailToMessage((body as any).detail);
      }
    }
    const text = (await res.text()).trim();
    if (text) return text;
  } catch {
    // Ignore parse errors.
  }
  return fallback;
};

/** Build require_fields array for API (backend expects "email" | "name" | "address" | "phone"). */
function toRequireFields(p: {
  require_name?: boolean;
  require_email?: boolean;
  require_address?: boolean;
  require_phone?: boolean;
}): string[] {
  const fields: string[] = [];
  if (p.require_email) fields.push("email");
  if (p.require_name) fields.push("name");
  if (p.require_address) fields.push("address");
  if (p.require_phone) fields.push("phone");
  return fields;
}

export type PaymentLinkPayload = {
  title?: string | null;
  description?: string | null;
  amount: number;
  currency: string;
  expires_at?: string | null;
  require_name?: boolean;
  require_email?: boolean;
  require_address?: boolean;
  require_phone?: boolean;
};

export type SubscriptionPayload = {
  title?: string | null;
  description?: string | null;
  amount: number;
  currency: string;
  interval: string;
  expires_at?: string | null;
  require_name?: boolean;
  require_email?: boolean;
  require_address?: boolean;
  require_phone?: boolean;
};

/** Response shape for both payment and subscription links (list + create). */
export type LinkResponse = {
  id: string;
  stripe_payment_link_id: string;
  url: string;
  title?: string | null;
  description?: string | null;
  amount: number;
  service_fee: number;
  currency: string;
  status: string;
  expires_at?: string | null;
  created_at?: string | null;
  total_amount_paid: number;
  earnings_amount: number;
  require_fields: string[];
  interval?: string | null;
};

export type TransferResponse = {
  stripe_account_id: string;
  transferred: Record<string, number>;
  failed: Record<string, string>;
  payout_ids?: Record<string, string>;
  message?: string;
};

export const api = {
  connectAccount: async (country: string = "GB") => {
    const res = await authFetch(`${base}/platform/connected-accounts`, await withAuth({
      method: "POST",
      body: JSON.stringify({ country }),
      headers: { "Content-Type": "application/json" },
    }));
    if (!res.ok) throw new Error(await errorMessageFromResponse(res, "Failed to create connected account"));
    return res.json();
  },
  getAccount: async (): Promise<Account | null> => {
    const res = await authFetch(`${base}/accounts/account`, await withAuth());
    if (res.status === 404) return null;
    if (res.status === 403) {
      const body = await res.clone().json().catch(() => ({}));
      if (body && (body as { error_code?: string }).error_code === STRIPE_ACCOUNT_REQUIRED_ERROR_CODE) {
        return null;
      }
    }
    if (!res.ok) throw new Error(await errorMessageFromResponse(res, "Failed to fetch account"));
    return res.json();
  },
  createOnboardingLink: async () => {
    const res = await authFetch(`${base}/accounts/onboarding`, await withAuth({ method: "POST" }));
    if (!res.ok) throw new Error(await errorMessageFromResponse(res, "Failed to create onboarding link"));
    return res.json();
  },
  deleteAccount: async () => {
    const res = await authFetch(`${base}/accounts/account`, await withAuth({ method: "DELETE" }));
    if (!res.ok) throw new Error(await errorMessageFromResponse(res, "Failed to delete account"));
  },
  createPaymentLink: async (payload: PaymentLinkPayload) => {
    const body = {
      title: payload.title ?? undefined,
      description: payload.description ?? undefined,
      amount: payload.amount,
      currency: payload.currency,
      expires_at: payload.expires_at ?? undefined,
      require_fields: toRequireFields(payload),
    };
    const res = await authFetch(
      `${base}/payment-links`,
      await withAuth({
        method: "POST",
        body: JSON.stringify(body),
      })
    );
    if (!res.ok) throw new Error(await errorMessageFromResponse(res, "Failed to create payment link"));
    return res.json();
  },
  listPaymentLinks: async (): Promise<LinkResponse[]> => {
    const res = await authFetch(`${base}/payment-links`, await withAuth());
    if (!res.ok) throw new Error(await errorMessageFromResponse(res, "Failed to fetch payment links"));
    return res.json();
  },
  disablePaymentLink: async (linkId: string) => {
    const res = await authFetch(`${base}/payment-links/${linkId}/disable`, await withAuth({ method: "POST" }));
    if (!res.ok) throw new Error(await errorMessageFromResponse(res, "Failed to disable payment link"));
    return res.json();
  },
  createSubscription: async (payload: SubscriptionPayload) => {
    const body = {
      title: payload.title ?? undefined,
      description: payload.description ?? undefined,
      amount: payload.amount,
      currency: payload.currency,
      interval: payload.interval,
      expires_at: payload.expires_at ?? undefined,
      require_fields: toRequireFields(payload),
    };
    const res = await authFetch(
      `${base}/subscriptions`,
      await withAuth({
        method: "POST",
        body: JSON.stringify(body),
      })
    );
    if (!res.ok) throw new Error(await errorMessageFromResponse(res, "Failed to create subscription link"));
    return res.json();
  },
  listSubscriptions: async (): Promise<LinkResponse[]> => {
    const res = await authFetch(`${base}/subscriptions`, await withAuth());
    if (!res.ok) throw new Error(await errorMessageFromResponse(res, "Failed to fetch subscriptions"));
    return res.json();
  },
  listStripeSubscriptions: async (params: Record<string, string | number | undefined>) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) query.set(key, String(value));
    });
    const res = await authFetch(`${base}/stripe-subscriptions?${query.toString()}`, await withAuth());
    if (!res.ok) throw new Error(await errorMessageFromResponse(res, "Failed to fetch subscriptions"));
    return res.json();
  },
  cancelStripeSubscription: async (subscriptionId: string) => {
    const res = await authFetch(
      `${base}/stripe-subscriptions/${subscriptionId}/cancel`,
      await withAuth({ method: "POST" })
    );
    if (!res.ok) throw new Error(await errorMessageFromResponse(res, "Failed to cancel subscription"));
    return res.json();
  },
  disableSubscription: async (subscriptionId: string) => {
    const res = await authFetch(
      `${base}/subscriptions/${subscriptionId}/disable`,
      await withAuth({ method: "POST" })
    );
    if (!res.ok) throw new Error(await errorMessageFromResponse(res, "Failed to disable subscription link"));
    return res.json();
  },
  createPayouts: async (): Promise<TransferResponse> => {
    const res = await authFetch(
      `${base}/transfers/payouts`,
      await withAuth({ method: "POST" })
    );
    if (!res.ok) throw new Error(await errorMessageFromResponse(res, "Failed to payout funds"));
    return res.json();
  },
  listTransactions: async (params: { date_start?: string; date_end?: string; limit?: number }) => {
    const query = new URLSearchParams();
    if (params.date_start) query.set("date_start", params.date_start);
    if (params.date_end) query.set("date_end", params.date_end);
    if (params.limit != null) query.set("limit", String(params.limit));
    const res = await authFetch(`${base}/transactions?${query.toString()}`, await withAuth());
    if (!res.ok) throw new Error(await errorMessageFromResponse(res, "Failed to fetch transactions"));
    return res.json() as Promise<{ items: TransactionItem[]; has_more: boolean; next_cursor?: string | null }>;
  },
  getTransaction: async (paymentIntentId: string) => {
    const res = await authFetch(
      `${base}/transactions/by-id/${encodeURIComponent(paymentIntentId)}`,
      await withAuth()
    );
    if (!res.ok) throw new Error(await errorMessageFromResponse(res, "Failed to fetch transaction"));
    return res.json() as Promise<TransactionItem & { link_id?: string; date_transaction_id?: string }>;
  },
  refund: async (paymentIntentId: string) => {
    const res = await authFetch(
      `${base}/refunds`,
      await withAuth({
        method: "POST",
        body: JSON.stringify({ payment_intent_id: paymentIntentId }),
      })
    );
    if (!res.ok) throw new Error(await errorMessageFromResponse(res, "Failed to refund"));
    return res.json();
  },
};
