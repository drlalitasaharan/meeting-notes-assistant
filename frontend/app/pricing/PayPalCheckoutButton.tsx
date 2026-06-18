"use client";

import { useState } from "react";

type CheckoutResponse = {
  status: string;
  provider_order_id: string;
  approval_url: string;
  attempt_reference: string;
  plan_code: string;
  amount_cents: number;
  currency_code: string;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "https://meeting-notes-assistant.onrender.com";

export function PayPalCheckoutButton() {
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
        `${API_BASE_URL}/v1/billing/paypal/create-checkout`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      const payload = (await response.json().catch(() => ({}))) as
        | Partial<CheckoutResponse>
        | { detail?: string };

      if (!response.ok) {
        const detail =
          "detail" in payload && payload.detail
            ? payload.detail
            : "Could not start PayPal checkout. Please try again.";
        throw new Error(detail);
      }

      if (!("approval_url" in payload) || !payload.approval_url) {
        throw new Error("PayPal approval link was not returned. Please try again.");
      }

      window.location.href = payload.approval_url;
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Could not start PayPal checkout. Please try again.",
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
          background: "#2f6f4e",
          border: "none",
          borderRadius: 999,
          color: "#ffffff",
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
        {isLoading ? "Opening PayPal..." : "Pay with PayPal"}
      </button>

      {errorMessage ? (
        <p style={{ color: "#b42318", fontSize: 14, margin: "10px 0 0" }}>
          {errorMessage}
        </p>
      ) : null}
    </div>
  );
}
