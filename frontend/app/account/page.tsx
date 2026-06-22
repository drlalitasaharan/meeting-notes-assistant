"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import UsageSummaryCard from "../../components/UsageSummaryCard";
import { getBillingStatus, getCurrentUser, getUsageSummary } from "../../lib/api";
import type { BillingStatus, UsageSummary, UserRead } from "../../lib/types";

function formatValue(value?: string | null): string {
  return value && value.trim().length > 0 ? value : "Not available";
}

function formatPlan(planCode?: string | null, usagePlan?: string | null): string {
  const plan = planCode || usagePlan;

  if (!plan) {
    return "Not available";
  }

  const labels: Record<string, string> = {
    free_trial: "Free trial",
    paid_pro: "Starter",
    pilot: "Pilot access",
    pro_pilot: "Pro Pilot",
    starter: "Starter",
  };

  return labels[plan] || plan.replace(/_/g, " ");
}

function formatDisplayName(user: UserRead | null): string {
  if (!user) {
    return "Not available";
  }

  const name = [user.first_name, user.last_name].filter(Boolean).join(" ").trim();
  return name || formatValue(user.organization_name);
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        borderBottom: "1px solid #e4f0e8",
        display: "grid",
        gap: 8,
        gridTemplateColumns: "minmax(140px, 0.4fr) 1fr",
        padding: "14px 0",
      }}
    >
      <dt style={{ color: "#5d6f66", fontWeight: 800 }}>{label}</dt>
      <dd style={{ color: "#123326", margin: 0 }}>{value}</dd>
    </div>
  );
}

export default function AccountPage() {
  const [user, setUser] = useState<UserRead | null>(null);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [billingStatus, setBillingStatus] = useState<BillingStatus | null>(null);
  const [status, setStatus] = useState<"loading" | "authenticated" | "unauthenticated">(
    "loading",
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadAccount() {
      try {
        const [userData, usageData, billingData] = await Promise.all([
          getCurrentUser(),
          getUsageSummary(),
          getBillingStatus(),
        ]);

        if (!isMounted) {
          return;
        }

        setUser(userData);
        setUsage(usageData);
        setBillingStatus(billingData);
        setStatus("authenticated");
        setError(null);
      } catch (err) {
        if (!isMounted) {
          return;
        }

        setUser(null);
        setUsage(null);
        setBillingStatus(null);
        setStatus("unauthenticated");
        setError(err instanceof Error ? err.message : "Unable to load account details.");
      }
    }

    void loadAccount();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <main
      style={{
        background: "linear-gradient(180deg, #f7fbf8 0%, #ffffff 100%)",
        minHeight: "100vh",
        padding: "48px 20px 80px",
      }}
    >
      <div style={{ margin: "0 auto", maxWidth: 960 }}>
        <div style={{ marginBottom: 28 }}>
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
            MeetIQ account
          </p>
          <h1 style={{ color: "#123326", fontSize: 42, margin: "10px 0 10px" }}>
            Account details
          </h1>
          <p style={{ color: "#5d6f66", fontSize: 18, lineHeight: 1.6, margin: 0 }}>
            Review your profile, billing status, usage allowance, and password security
            information.
          </p>
        </div>

        {status === "loading" ? (
          <section
            style={{
              background: "#ffffff",
              border: "1px solid #d7eadf",
              borderRadius: 24,
              color: "#5d6f66",
              padding: 24,
            }}
          >
            Loading your account...
          </section>
        ) : null}

        {status === "unauthenticated" ? (
          <section
            style={{
              background: "#ffffff",
              border: "1px solid #d7eadf",
              borderRadius: 24,
              color: "#5d6f66",
              lineHeight: 1.6,
              padding: 24,
            }}
          >
            <h2 style={{ color: "#123326", marginTop: 0 }}>Sign in required</h2>
            <p>{error || "Please sign in to view your account details."}</p>
            <Link
              href="/login?next=/account"
              style={{
                background: "#2f6f4e",
                borderRadius: 999,
                color: "#ffffff",
                display: "inline-block",
                fontWeight: 800,
                padding: "12px 18px",
                textDecoration: "none",
              }}
            >
              Sign in
            </Link>
          </section>
        ) : null}

        {status === "authenticated" ? (
          <>
            <section
              style={{
                background: "#ffffff",
                border: "1px solid #d7eadf",
                borderRadius: 24,
                boxShadow: "0 18px 45px rgba(18, 51, 38, 0.08)",
                marginBottom: 22,
                padding: 24,
              }}
            >
              <h2 style={{ color: "#123326", margin: "0 0 8px" }}>Profile</h2>
              <dl style={{ margin: 0 }}>
                <DetailRow label="Email" value={formatValue(user?.email)} />
                <DetailRow label="Display name" value={formatDisplayName(user)} />
                <DetailRow
                  label="Organization"
                  value={formatValue(user?.organization_name)}
                />
                <DetailRow
                  label="Current plan"
                  value={formatPlan(billingStatus?.plan_code, usage?.plan)}
                />
                <DetailRow
                  label="Billing status"
                  value={formatValue(billingStatus?.billing_status)}
                />
              </dl>
            </section>

            <section
              style={{
                background: "#fbfffb",
                border: "1px solid #d7eadf",
                borderRadius: 24,
                color: "#5d6f66",
                lineHeight: 1.6,
                marginBottom: 22,
                padding: 24,
              }}
            >
              <h2 style={{ color: "#123326", margin: "0 0 8px" }}>Password</h2>
              <p style={{ margin: "0 0 8px" }}>
                For security, your password is never shown.
              </p>
              <p style={{ margin: 0 }}>
                Password changes are coming soon. Contact support if you need help.
              </p>
            </section>

            {usage ? (
              <UsageSummaryCard usage={usage} billingStatus={billingStatus} />
            ) : null}
          </>
        ) : null}
      </div>
    </main>
  );
}
