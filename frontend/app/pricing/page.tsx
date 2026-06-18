import Link from "next/link";
import { PayPalCheckoutButton } from "./PayPalCheckoutButton";

const squareUrl = process.env.NEXT_PUBLIC_SQUARE_CHECKOUT_URL || "";
const manualPaymentUrl = process.env.NEXT_PUBLIC_MANUAL_PAYMENT_REQUEST_URL || "";

function PaymentLink({
  href,
  children,
  primary = false,
}: {
  href: string;
  children: React.ReactNode;
  primary?: boolean;
}) {
  const configured = href.trim().length > 0;

  if (!configured) {
    return (
      <span
        aria-disabled="true"
        style={{
          background: primary ? "#8fb7a1" : "#f3f7f4",
          border: primary ? "none" : "1px solid #d7eadf",
          borderRadius: 999,
          color: primary ? "#ffffff" : "#789086",
          display: "inline-flex",
          fontWeight: 800,
          justifyContent: "center",
          padding: "12px 18px",
        }}
      >
        Payment link coming soon
      </span>
    );
  }

  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      style={{
        background: primary ? "#2f6f4e" : "#ffffff",
        border: primary ? "none" : "1px solid #b8d8c5",
        borderRadius: 999,
        color: primary ? "#ffffff" : "#123326",
        display: "inline-flex",
        fontWeight: 800,
        justifyContent: "center",
        padding: "12px 18px",
        textDecoration: "none",
      }}
    >
      {children}
    </a>
  );
}

function PlanCard({
  title,
  price,
  description,
  features,
  children,
  highlighted = false,
}: {
  title: string;
  price: string;
  description: string;
  features: string[];
  children: React.ReactNode;
  highlighted?: boolean;
}) {
  return (
    <section
      style={{
        background: "#ffffff",
        border: highlighted ? "2px solid #2f6f4e" : "1px solid #d7eadf",
        borderRadius: 28,
        boxShadow: highlighted ? "0 18px 44px rgba(47, 111, 78, 0.14)" : "none",
        padding: 28,
      }}
    >
      <p
        style={{
          color: "#2f6f4e",
          fontSize: 13,
          fontWeight: 900,
          letterSpacing: "0.08em",
          margin: 0,
          textTransform: "uppercase",
        }}
      >
        {title}
      </p>
      <h2 style={{ color: "#123326", fontSize: 34, margin: "10px 0 8px" }}>{price}</h2>
      <p style={{ color: "#5d6f66", lineHeight: 1.6, margin: "0 0 20px" }}>
        {description}
      </p>

      <ul style={{ color: "#31473d", lineHeight: 1.8, margin: "0 0 24px", paddingLeft: 20 }}>
        {features.map((feature) => (
          <li key={feature}>{feature}</li>
        ))}
      </ul>

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>{children}</div>
    </section>
  );
}

export default function PricingPage() {
  return (
    <main
      style={{
        background: "linear-gradient(180deg, #f7fbf8 0%, #ffffff 100%)",
        minHeight: "100vh",
        padding: "56px 20px 88px",
      }}
    >
      <div style={{ margin: "0 auto", maxWidth: 1080 }}>
        <div style={{ marginBottom: 34, maxWidth: 760 }}>
          <p
            style={{
              color: "#2f6f4e",
              fontSize: 13,
              fontWeight: 900,
              letterSpacing: "0.08em",
              margin: 0,
              textTransform: "uppercase",
            }}
          >
            MeetIQ pricing
          </p>
          <h1 style={{ color: "#123326", fontSize: 46, lineHeight: 1.05, margin: "12px 0" }}>
            Start with one meeting. Upgrade when you are ready.
          </h1>
          <p style={{ color: "#5d6f66", fontSize: 18, lineHeight: 1.65, margin: 0 }}>
            MeetIQ turns meeting recordings into clear summaries, decisions, risks, and
            action items. Early-access plans are available for individuals, pilots, and
            selected teams while billing automation continues to improve.
          </p>
        </div>

        <div
          style={{
            display: "grid",
            gap: 22,
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          }}
        >
          <PlanCard
            title="Free trial"
            price="$0"
            description="Best for first-time users testing MeetIQ before upgrading."
            features={[
              "1 meeting upload",
              "Up to 30 minutes per recording",
              "Structured summaries, decisions, risks, and action items",
              "Copy-ready notes and Markdown download",
              "Basic email support",
            ]}
          >
            <Link
              href="/signup"
              style={{
                background: "#2f6f4e",
                borderRadius: 999,
                color: "#ffffff",
                display: "inline-flex",
                fontWeight: 800,
                justifyContent: "center",
                padding: "12px 18px",
                textDecoration: "none",
              }}
            >
              Start free trial
            </Link>
            <Link
              href="/login"
              style={{
                border: "1px solid #b8d8c5",
                borderRadius: 999,
                color: "#123326",
                display: "inline-flex",
                fontWeight: 800,
                justifyContent: "center",
                padding: "12px 18px",
                textDecoration: "none",
              }}
            >
              Sign in
            </Link>
          </PlanCard>

          <PlanCard
            title="Starter"
            price="$23/month"
            description="Best for individuals, founders, consultants, and small teams."
            highlighted
            features={[
              "Up to 20 meeting uploads per month during early access",
              "AI-generated summaries, decisions, risks, and action items",
              "Copy-ready notes and Markdown download",
              "Email support",
              "PayPal checkout",
            ]}
          >
            <PayPalCheckoutButton />
            <PaymentLink href={squareUrl}>Pay with Square</PaymentLink>
            <PaymentLink href={manualPaymentUrl}>Request invoice/manual payment</PaymentLink>
          </PlanCard>

          <PlanCard
            title="Pro Pilot"
            price="$49/month"
            description="Best for frequent meeting users, consultants, operators, and small teams that need more capacity."
            features={[
              "Up to 100 meeting uploads per month during early access",
              "AI-generated summaries, decisions, risks, and action items",
              "Copy-ready notes and Markdown download",
              "Priority email support during early access",
              "Manual activation while billing automation improves",
            ]}
          >
            <Link
              href="/support"
              style={{
                background: "#2f6f4e",
                borderRadius: 999,
                color: "#ffffff",
                display: "inline-flex",
                fontWeight: 800,
                justifyContent: "center",
                padding: "12px 18px",
                textDecoration: "none",
              }}
            >
              Request Pro Pilot access
            </Link>
            <PaymentLink href={manualPaymentUrl}>Request invoice/manual payment</PaymentLink>
          </PlanCard>

          <PlanCard
            title="Business / Team"
            price="Custom pricing"
            description="Best for teams with higher usage, privacy-conscious workflows, or internal review needs."
            features={[
              "Custom meeting upload allowances",
              "Team onboarding during early access",
              "Export and deletion support",
              "Priority email support",
              "Request-based approval before activation",
            ]}
          >
            <Link
              href="/support"
              style={{
                background: "#2f6f4e",
                borderRadius: 999,
                color: "#ffffff",
                display: "inline-flex",
                fontWeight: 800,
                justifyContent: "center",
                padding: "12px 18px",
                textDecoration: "none",
              }}
            >
              Request team access
            </Link>
            <PaymentLink href={manualPaymentUrl}>Request invoice/manual payment</PaymentLink>
          </PlanCard>
        </div>

        <section
          style={{
            background: "#fbfffb",
            border: "1px solid #d7eadf",
            borderRadius: 24,
            color: "#5d6f66",
            lineHeight: 1.6,
            marginTop: 24,
            padding: 24,
          }}
        >
          <h2 style={{ color: "#123326", margin: "0 0 8px" }}>Early-access billing and limits</h2>
          <p style={{ margin: "0 0 12px" }}>
            PayPal checkout activates paid access after payment confirmation. Webhooks remain a backup verification path. Square checkout is coming soon.
          </p>
          <p style={{ margin: 0 }}>
            During early access, Starter and Pro Pilot usage allowances may be reviewed manually. Business / Team plans are request-based; we confirm expected usage, team size, recording volume, billing method, and support needs before activating team access.
          </p>
        </section>
      </div>
    </main>
  );
}
