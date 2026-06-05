export default function TermsPage() {
  return (
    <div style={{ display: "grid", gap: 20, maxWidth: 860 }}>
      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h1 style={{ marginTop: 0, marginBottom: 12, fontSize: 32, color: "#111827" }}>Terms of Service</h1>
        <p style={{ margin: 0, color: "#4b5563", fontSize: 16, lineHeight: 1.6 }}>
          By using Meeting Notes Assistant, you agree to upload recordings only when you have permission to do so.
        </p>
      </section>

      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h2 style={{ marginTop: 0, marginBottom: 12, fontSize: 24, color: "#111827" }}>Usage requirements</h2>
        <p style={{ color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          Upload recordings only if you own them or have explicit permission from participants. Do not upload private or confidential content unless you are authorized to do so.
        </p>
        <p style={{ color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          The service is provided as a meeting note assistant. Users are responsible for verifying generated notes before relying on them for decisions.
        </p>
      </section>
    </div>
  );
}
