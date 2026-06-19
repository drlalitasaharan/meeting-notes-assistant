import Link from "next/link";

export default function SquareSuccessPage() {
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
          Square
        </p>

        <h1 style={{ color: "#123326", fontSize: 42, lineHeight: 1.08, margin: "12px 0" }}>
          Payment received
        </h1>

        <p style={{ color: "#5d6f66", fontSize: 18, lineHeight: 1.65, margin: "0 0 24px" }}>
          Square payment was completed. MeetIQ will activate paid access after payment
          confirmation is received.
        </p>

        <p style={{ color: "#5d6f66", fontSize: 16, lineHeight: 1.6, margin: "0 0 24px" }}>
          During early access, Square webhooks confirm the payment. If your usage page
          does not update within a few moments, contact support with your account email.
        </p>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
          <Link
            href="/usage"
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
            Check usage
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
