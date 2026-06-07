export default function SupportPage() {
  return (
    <div style={{ display: "grid", gap: 20, maxWidth: 860 }}>
      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h1 style={{ marginTop: 0, marginBottom: 12, fontSize: 32, color: "#111827" }}>Support</h1>
        <p style={{ margin: 0, color: "#4b5563", fontSize: 16, lineHeight: 1.6 }}>
          Need help with MeetIQ? Contact us at <strong>support@acjen.ai</strong>.
        </p>
      </section>

      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h2 style={{ marginTop: 0, marginBottom: 12, fontSize: 24, color: "#111827" }}>When contacting support, please include:</h2>
        <ul style={{ margin: "12px 0 0 20px", color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          <li>Your account email address</li>
          <li>The meeting filename (if applicable)</li>
          <li>Approximate time of upload</li>
          <li>A clear description of the issue or question</li>
        </ul>
      </section>

      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h2 style={{ marginTop: 0, marginBottom: 12, fontSize: 24, color: "#111827" }}>We can help with:</h2>
        <ul style={{ margin: "12px 0 0 20px", color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          <li>Account access and password reset</li>
          <li>Upload failures and file format questions</li>
          <li>Meeting history and file recovery</li>
          <li>Processing issues and job status</li>
          <li>Privacy and data questions</li>
        </ul>
      </section>
    </div>
  );
}
