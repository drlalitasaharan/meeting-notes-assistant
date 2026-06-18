import Link from "next/link";

import type { BillingStatus, UsageSummary } from "../lib/types";

type UsageSummaryCardProps = {
  usage: UsageSummary;
  billingStatus?: BillingStatus | null;
};

function isPaidAccess(billingStatus?: BillingStatus | null): boolean {
  return (
    billingStatus?.plan_code === "paid_pro" &&
    ["active", "trialing", "paid"].includes(billingStatus.billing_status)
  );
}

function formatProvider(provider?: string | null): string {
  if (!provider) {
    return "Manual";
  }

  return provider.charAt(0).toUpperCase() + provider.slice(1);
}

function formatPlanLabel(
  usage: UsageSummary,
  billingStatus?: BillingStatus | null,
): string {
  if (isPaidAccess(billingStatus)) {
    return "Paid access";
  }

  if (usage.is_pilot_override || usage.plan === "pilot") {
    return "Pilot access";
  }

  return "Free trial";
}

export default function UsageSummaryCard({ usage, billingStatus }: UsageSummaryCardProps) {
  const paidAccess = isPaidAccess(billingStatus);
  const usedText = paidAccess ? `${usage.meetings_used}` : `${usage.meetings_used} of ${usage.meeting_upload_limit}`;
  const hasRemainingUploads = paidAccess || usage.remaining_uploads > 0;

  return (
    <section
      style={{
        background: "#ffffff",
        border: "1px solid #d7eadf",
        borderRadius: 24,
        boxShadow: "0 18px 45px rgba(18, 51, 38, 0.08)",
        padding: 24,
      }}
    >
      <div
        style={{
          alignItems: "flex-start",
          display: "flex",
          gap: 18,
          justifyContent: "space-between",
          marginBottom: 20,
        }}
      >
        <div>
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
            Usage
          </p>
          <h2 style={{ color: "#123326", fontSize: 28, margin: "8px 0 6px" }}>
            {formatPlanLabel(usage, billingStatus)}
          </h2>
          <p style={{ color: "#5d6f66", margin: 0 }}>
            {paidAccess ? "Your MeetIQ paid access is active." : "Track your early-access meeting upload allowance."}
          </p>
        </div>

        <span
          style={{
            background: hasRemainingUploads ? "#e7f7ed" : "#fff3df",
            borderRadius: 999,
            color: hasRemainingUploads ? "#14532d" : "#8a4b00",
            fontSize: 13,
            fontWeight: 800,
            padding: "8px 12px",
            whiteSpace: "nowrap",
          }}
        >
          {paidAccess ? "Active" : `${paidAccess ? "Active" : usage.remaining_uploads} remaining`}
        </span>
      </div>

      <div
        style={{
          display: "grid",
          gap: 14,
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        }}
      >
        <div style={{ background: "#f7fbf8", borderRadius: 18, padding: 18 }}>
          <p style={{ color: "#5d6f66", fontSize: 13, margin: "0 0 6px" }}>
            Meetings used
          </p>
          <p style={{ color: "#123326", fontSize: 30, fontWeight: 800, margin: 0 }}>
            {usedText}
          </p>
        </div>

        <div style={{ background: "#f7fbf8", borderRadius: 18, padding: 18 }}>
          <p style={{ color: "#5d6f66", fontSize: 13, margin: "0 0 6px" }}>
            {paidAccess ? "Access status" : "Remaining uploads"}
          </p>
          <p style={{ color: "#123326", fontSize: 30, fontWeight: 800, margin: 0 }}>
            {paidAccess ? "Active" : usage.remaining_uploads}
          </p>
        </div>

        <div style={{ background: "#f7fbf8", borderRadius: 18, padding: 18 }}>
          <p style={{ color: "#5d6f66", fontSize: 13, margin: "0 0 6px" }}>
            {paidAccess ? "Provider" : "Max recording length"}
          </p>
          <p style={{ color: "#123326", fontSize: 30, fontWeight: 800, margin: 0 }}>
            {paidAccess ? formatProvider(billingStatus?.provider) : `${usage.max_duration_minutes} min`}
          </p>
        </div>
      </div>

      {!paidAccess && !hasRemainingUploads ? (
        <div
          style={{
            background: "#fff8ec",
            border: "1px solid #f7d8a8",
            borderRadius: 18,
            color: "#6f4200",
            lineHeight: 1.6,
            marginTop: 18,
            padding: 16,
          }}
        >
          You have used your current upload allowance.{" "}
          <Link href="/support" style={{ color: "#2f6f4e", fontWeight: 800 }}>
            Contact support
          </Link>{" "}
          to request pilot access or a higher limit.
        </div>
      ) : null}
    </section>
  );
}
