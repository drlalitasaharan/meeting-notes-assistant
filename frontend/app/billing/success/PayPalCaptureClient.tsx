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

export default function PayPalCaptureClient() {
  const searchParams = useSearchParams();
  const providerOrderId = useMemo(() => searchParams.get("token"), [searchParams]);

  const [state, setState] = useState<CaptureState>("checking");
  const [message, setMessage] = useState<string>(
    "Confirming your PayPal payment with MeetIQ..."
  );
  const [capture, setCapture] = useState<CaptureResponse | null>(null);

  useEffect(() => {
    let canceled = false;

    async function capturePayment() {
      if (!providerOrderId) {
        setState("missing-order");
        setMessage(
          "PayPal returned you to MeetIQ, but the order token was missing."
        );
        return;
      }

      const authToken = window.localStorage.getItem(AUTH_TOKEN_KEY);
      if (!authToken) {
        setState("missing-auth");
        setMessage(
          "PayPal approval was received. Please sign in to MeetIQ to finish activation."
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
            : "Payment approval was received, but activation could not be confirmed."
        );
      }
    }

    capturePayment();

    return () => {
      canceled = true;
    };
  }, [providerOrderId]);

  const isSuccess = state === "captured";
  const isPending = state === "checking" || state === "capturing";

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-2xl flex-col items-center justify-center px-6 py-16 text-center">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          PayPal
        </p>

        <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-950">
          {isSuccess
            ? "Payment confirmed"
            : isPending
              ? "Confirming payment"
              : "PayPal approval received"}
        </h1>

        <p className="mt-4 text-base leading-7 text-slate-600">{message}</p>

        {capture?.billing ? (
          <div className="mt-6 rounded-xl bg-slate-50 p-4 text-left text-sm text-slate-700">
            <div>
              <span className="font-semibold">Plan:</span>{" "}
              {capture.billing.plan_code ?? "paid_pro"}
            </div>
            <div>
              <span className="font-semibold">Status:</span>{" "}
              {capture.billing.billing_status ?? "active"}
            </div>
            <div>
              <span className="font-semibold">Provider:</span>{" "}
              {capture.billing.provider ?? "paypal"}
            </div>
          </div>
        ) : null}

        {state === "failed" ? (
          <p className="mt-4 text-sm text-slate-500">
            Your PayPal approval may still be valid. Please check your usage page
            or contact support if activation does not update.
          </p>
        ) : null}

        <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
          <Link
            href="/usage"
            className="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            Check usage
          </Link>
          <Link
            href="/meetings"
            className="rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            Go to meetings
          </Link>
        </div>
      </div>
    </div>
  );
}
