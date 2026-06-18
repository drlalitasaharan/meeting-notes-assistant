const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "";

const AUTH_TOKEN_KEY = "meeting-notes-assistant-token";

export class AdminApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "AdminApiError";
    this.status = status;
  }
}

export type AdminOverview = {
  generated_at: string;
  total_users: number;
  total_meetings: number;
  meetings_today: number;
  meetings_last_7_days: number;
  meetings_last_30_days: number;
  completed: number;
  failed: number;
  processing: number;
  queued: number;
  stuck: number;
  success_rate_percent: number | null;
  status_counts: Record<string, number>;
  stuck_after_minutes: number;
};

export type AdminMeeting = {
  id: number;
  title: string;
  status: string;
  user_id: number | null;
  user_email: string | null;
  created_at: string | null;
  updated_at: string | null;
  last_error: string | null;
  is_stuck: boolean;
};

export type AdminMeetingsResponse = {
  items: AdminMeeting[];
  total: number;
  limit: number;
  offset: number;
};

export type AdminBillingSubscription = {
  id: number;
  user_id: number;
  user_email: string | null;
  provider: string;
  plan_code: string;
  status: string;
  provider_subscription_id: string | null;
  provider_payment_id: string | null;
  current_period_end: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type AdminBillingPaymentAttempt = {
  id: number;
  user_id: number;
  user_email: string | null;
  provider: string;
  plan_code: string;
  status: string;
  amount_cents: number;
  currency_code: string;
  provider_order_id: string | null;
  provider_capture_id: string | null;
  provider_payment_id: string | null;
  completed_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  error_message: string | null;
};

export type AdminBillingOverview = {
  generated_at: string;
  active_paid_users: number;
  active_subscriptions: number;
  total_subscriptions: number;
  total_payment_attempts: number;
  successful_payment_attempts: number;
  failed_payment_attempts: number;
  recent_subscriptions: AdminBillingSubscription[];
  recent_payment_attempts: AdminBillingPaymentAttempt[];
};

export type AdminSystemHealth = {
  generated_at: string;
  status: string;
  checks: Record<
    string,
    {
      status: string;
      detail?: string;
    }
  >;
};

function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(AUTH_TOKEN_KEY);
}

async function requestAdmin<T>(path: string): Promise<T> {
  if (!API_BASE_URL) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not set.");
  }

  const token = getToken();

  if (!token) {
    throw new AdminApiError(
      401,
      "Authentication credentials were not provided.",
    );
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `Admin request failed with status ${response.status}.`;

    try {
      const payload = await response.json();

      if (typeof payload?.detail === "string") {
        message = payload.detail;
      }
    } catch {
      // Preserve the fallback error message.
    }

    throw new AdminApiError(response.status, message);
  }

  return response.json() as Promise<T>;
}

export function getAdminOverview(): Promise<AdminOverview> {
  return requestAdmin<AdminOverview>("/v1/admin/overview");
}

export function getAdminSystemHealth(): Promise<AdminSystemHealth> {
  return requestAdmin<AdminSystemHealth>("/v1/admin/system-health");
}

export function getAdminBillingOverview(): Promise<AdminBillingOverview> {
  return requestAdmin<AdminBillingOverview>("/v1/admin/billing/overview");
}

export async function getAdminMeetings(options?: {
  search?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<AdminMeetingsResponse> {
  const query = new URLSearchParams();

  query.set("limit", String(options?.limit ?? 20));
  query.set("offset", String(options?.offset ?? 0));

  if (options?.search?.trim()) {
    query.set("search", options.search.trim());
  }

  if (options?.status?.trim()) {
    query.set("status", options.status.trim());
  }

  const payload = await requestAdmin<unknown>(
    `/v1/admin/meetings?${query.toString()}`,
  );

  if (
    typeof payload !== "object" ||
    payload === null ||
    !Array.isArray((payload as AdminMeetingsResponse).items) ||
    typeof (payload as AdminMeetingsResponse).total !== "number"
  ) {
    throw new Error(
      "The admin meetings endpoint returned an unexpected response. Restart or redeploy the backend and try again.",
    );
  }

  return payload as AdminMeetingsResponse;
}
