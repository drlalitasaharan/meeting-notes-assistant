"use client";

import { useState } from "react";

type SquarePlanCode = "starter" | "paid_pro" | "pro_pilot";

type CheckoutResponse = {
  status: string;
  provider_order_id: string | null;
  checkout_url?: string | null;
  approval_url?: string | null;
  attempt_reference: string;
  plan_code: string;
  amount_cents: number;
  currency_code: string;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "https://meeting-notes-assistant.onrender.com";

export function SquareCheckoutButton({
  planCode = "starter",
}: {
  planCode?: SquarePlanCode;
}) {
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function startCheckout() {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const token = window.localStorage.getItem("meeting-notes-assistant-token");

      if (!token) {
        window.location.href = "/login";
        return;
      }

      const response = await fetch(
        `${API_BASE_URL}/v1/billing/square/create-checkout`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ plan_code: planCode }),
        },
      );

      const payload = (await response.json().catch(() => ({}))) as
        | Partial<CheckoutResponse>
        | { detail?: string };

      if (!response.ok) {
        const detail =
          "detail" in payload && payload.detail
            ? payload.detail
            : "Could not start Square checkout. Please try again.";
        throw new Error(detail);
      }

      const checkoutUrl =
        ("checkout_url" in payload && payload.checkout_url) ||
        ("approval_url" in payload && payload.approval_url);

      if (!checkoutUrl) {
        throw new Error("Square checkout link was not returned. Please try again.");
      }

      window.location.href = checkoutUrl;
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Could not start Square checkout. Please try again.",
      );
      setIsLoading(false);
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={startCheckout}
        disabled={isLoading}
        style={{
          background: "#ffffff",
          border: "1px solid #b8d8c5",
          borderRadius: 999,
          color: "#123326",
          cursor: isLoading ? "not-allowed" : "pointer",
          display: "inline-flex",
          fontWeight: 800,
          justifyContent: "center",
          opacity: isLoading ? 0.72 : 1,
          padding: "12px 18px",
          textDecoration: "none",
          width: "100%",
        }}
      >
        {isLoading ? "Opening Square..." : "Pay with Square"}
      </button>

      {errorMessage ? (
        <p style={{ color: "#b42318", fontSize: 14, margin: "10px 0 0" }}>
          {errorMessage}
        </p>
      ) : null}
    </div>
  );
}
