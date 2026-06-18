import Link from "next/link";

export default function BillingCancelPage() {
  return (
    <main
      style={{
        background: "linear-gradient(180deg, #f7fbf8 0%, #ffffff 100%)",
        minHeight: "100vh",
        padding: "72px 20px",
      }}
    >
      <section
        style={{
          background: "#ffffff",
          border: "1px solid #c8e6d3",
          borderRadius: 28,
          boxShadow: "0 20px 60px rgba(47, 111, 78, 0.10)",
          margin: "0 auto",
          maxWidth: 760,
          padding: 36,
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
          MeetIQ billing
        </p>

        <h1 style={{ color: "#123326", fontSize: 42, lineHeight: 1.08, margin: "12px 0" }}>
          PayPal checkout canceled.
        </h1>

        <p style={{ color: "#5d6f66", fontSize: 18, lineHeight: 1.65, margin: "0 0 24px" }}>
          No MeetIQ paid access was activated from this checkout. You can return to pricing
          whenever you are ready.
        </p>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
          <Link
            href="/pricing"
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
            Return to pricing
          </Link>

          <Link
            href="/meetings"
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
            Go to meetings
          </Link>
        </div>
      </section>
    </main>
  );
}
