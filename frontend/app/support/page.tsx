export default function SupportPage() {
  return (
    <div style={{ display: "grid", gap: 20, maxWidth: 860 }}>
      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h1 style={{ marginTop: 0, marginBottom: 12, fontSize: 32, color: "#111827" }}>Support</h1>
        <p style={{ margin: 0, color: "#4b5563", fontSize: 16, lineHeight: 1.6 }}>
          Need help with your meeting uploads or account? We're here to help.
        </p>
      </section>

      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <p style={{ color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          For support, contact us at <strong>support@acjen.ai</strong>. Please include your account email and a brief description of the issue.
        </p>
        <p style={{ color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          We can help with upload issues, file format questions, and finding your meeting history.
        </p>
      </section>
    </div>
  );
}
