"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

const AUTH_TOKEN_KEY = "meeting-notes-assistant-token";

type CaptureState =
  | "checking"
  | "missing-order"
  | "missing-auth"
  | "capturing"
  | "captured"
  | "failed";

type CaptureResponse = {
  status: string;
  provider: string;
  provider_order_id: string | null;
  provider_capture_id: string | null;
  billing?: {
    plan_code?: string;
    billing_status?: string;
    provider?: string | null;
    source?: string;
  };
};

const pageStyle = {
  background: "linear-gradient(180deg, #f7fbf8 0%, #ffffff 100%)",
  minHeight: "100vh",
  padding: "56px 20px 88px",
};

const cardStyle = {
  background: "#ffffff",
  border: "1px solid #d7eadf",
  borderRadius: 24,
  boxShadow: "0 18px 45px rgba(18, 51, 38, 0.08)",
  padding: 28,
};

const primaryButtonStyle = {
  background: "#2f6f4e",
  borderRadius: 999,
  color: "#ffffff",
  display: "inline-block",
  fontWeight: 800,
  padding: "12px 18px",
  textDecoration: "none",
};

const secondaryButtonStyle = {
  border: "1px solid #b8d8c5",
  borderRadius: 999,
  color: "#123326",
  display: "inline-block",
  fontWeight: 800,
  padding: "12px 18px",
  textDecoration: "none",
};

function getErrorMessage(payload: unknown): string {
  if (
    payload &&
    typeof payload === "object" &&
    "detail" in payload &&
    typeof payload.detail === "string"
  ) {
    return payload.detail;
  }

  return "Payment approval was received, but MeetIQ could not confirm activation yet.";
}

function formatProvider(provider?: string | null): string {
  if (!provider) {
    return "PayPal";
  }

  return provider.charAt(0).toUpperCase() + provider.slice(1);
}

export default function PayPalCaptureClient() {
  const searchParams = useSearchParams();
  const providerOrderId = useMemo(() => searchParams.get("token"), [searchParams]);

  const [state, setState] = useState<CaptureState>("checking");
  const [message, setMessage] = useState<string>(
    "Confirming your PayPal payment with MeetIQ...",
  );
  const [capture, setCapture] = useState<CaptureResponse | null>(null);

  useEffect(() => {
    let canceled = false;

    async function capturePayment() {
      if (!providerOrderId) {
        setState("missing-order");
        setMessage("PayPal returned you to MeetIQ, but the order token was missing.");
        return;
      }

      const authToken = window.localStorage.getItem(AUTH_TOKEN_KEY);
      if (!authToken) {
        setState("missing-auth");
        setMessage(
          "PayPal approval was received. Please sign in to MeetIQ to finish activation.",
        );
        return;
      }

      setState("capturing");

      try {
        const response = await fetch(`${API_BASE_URL}/v1/billing/paypal/capture`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${authToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            provider_order_id: providerOrderId,
          }),
        });

        const payload = (await response.json().catch(() => null)) as
          | CaptureResponse
          | { detail?: string }
          | null;

        if (!response.ok) {
          throw new Error(getErrorMessage(payload));
        }

        if (canceled) {
          return;
        }

        setCapture(payload as CaptureResponse);
        setState("captured");
        setMessage("Payment confirmed. Your MeetIQ paid access is active.");
      } catch (error) {
        if (canceled) {
          return;
        }

        setState("failed");
        setMessage(
          error instanceof Error
            ? error.message
            : "Payment approval was received, but activation could not be confirmed.",
        );
      }
    }

    void capturePayment();

    return () => {
      canceled = true;
    };
  }, [providerOrderId]);

  const isSuccess = state === "captured";
  const isPending = state === "checking" || state === "capturing";

  return (
    <main style={pageStyle}>
      <div style={{ margin: "0 auto", maxWidth: 760 }}>
        <section style={cardStyle}>
          <p
            style={{
              color: "#2f6f4e",
              fontSize: 13,
              fontWeight: 800,
              letterSpacing: "0.08em",
              margin: 0,
              textTransform: "uppercase",
            }}
          >
            PayPal
          </p>

          <h1
            style={{
              color: "#123326",
              fontSize: "clamp(34px, 5vw, 48px)",
              letterSpacing: "-0.05em",
              lineHeight: 1.08,
              margin: "12px 0 14px",
            }}
          >
            {isSuccess
              ? "Payment confirmed"
              : isPending
                ? "Confirming payment"
                : "PayPal approval received"}
          </h1>

          <p style={{ color: "#416153", fontSize: 18, lineHeight: 1.6, margin: 0 }}>
            {message}
          </p>

          {capture?.billing ? (
            <div
              style={{
                display: "grid",
                gap: 14,
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                marginTop: 24,
              }}
            >
              <div style={{ background: "#f7fbf8", borderRadius: 18, padding: 18 }}>
                <p style={{ color: "#5d6f66", fontSize: 13, margin: "0 0 6px" }}>
                  Plan
                </p>
                <p style={{ color: "#123326", fontSize: 24, fontWeight: 800, margin: 0 }}>
                  {capture.billing.plan_code ?? "paid_pro"}
                </p>
              </div>

              <div style={{ background: "#f7fbf8", borderRadius: 18, padding: 18 }}>
                <p style={{ color: "#5d6f66", fontSize: 13, margin: "0 0 6px" }}>
                  Status
                </p>
                <p style={{ color: "#123326", fontSize: 24, fontWeight: 800, margin: 0 }}>
                  {capture.billing.billing_status ?? "active"}
                </p>
              </div>

              <div style={{ background: "#f7fbf8", borderRadius: 18, padding: 18 }}>
                <p style={{ color: "#5d6f66", fontSize: 13, margin: "0 0 6px" }}>
                  Provider
                </p>
                <p style={{ color: "#123326", fontSize: 24, fontWeight: 800, margin: 0 }}>
                  {formatProvider(capture.billing.provider)}
                </p>
              </div>
            </div>
          ) : null}

          {state === "failed" ? (
            <div
              style={{
                background: "#fff8ec",
                border: "1px solid #f7d8a8",
                borderRadius: 18,
                color: "#6f4200",
                lineHeight: 1.6,
                marginTop: 22,
                padding: 16,
              }}
            >
              Your PayPal approval may still be valid. Please check your usage page or
              contact support if activation does not update.
            </div>
          ) : null}

          <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 28 }}>
            <Link href="/usage" style={primaryButtonStyle}>
              Check usage
            </Link>
            <Link href="/meetings" style={secondaryButtonStyle}>
              Go to meetings
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
