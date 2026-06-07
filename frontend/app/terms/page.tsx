export default function TermsPage() {
  return (
    <div style={{ display: "grid", gap: 20, maxWidth: 860 }}>
      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h1 style={{ marginTop: 0, marginBottom: 12, fontSize: 32, color: "#111827" }}>Terms of Service</h1>
        <p style={{ margin: 0, color: "#4b5563", fontSize: 16, lineHeight: 1.6 }}>
          By using MeetIQ by Acjen AI, you agree to use the service responsibly and to upload recordings only when you have permission to do so.
        </p>
      </section>

      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h2 style={{ marginTop: 0, marginBottom: 12, fontSize: 24, color: "#111827" }}>Usage requirements</h2>
        <p style={{ color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          <strong>Permission:</strong> Upload recordings only if you own them or have explicit permission from all participants. Do not upload private, confidential, or proprietary content unless you are authorized to do so.
        </p>
        <p style={{ color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          <strong>AI-generated content:</strong> Generated meeting notes, summaries, and action items require human review before use. AI-generated content may contain mistakes or omissions and should not be relied upon as authoritative without verification.
        </p>
        <p style={{ color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          <strong>Not a transcript system:</strong> MeetIQ is not a legal, regulatory, compliance, evidentiary, or official transcript service. For official records or sensitive applications, use certified human transcription services.
        </p>
      </section>

      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h2 style={{ marginTop: 0, marginBottom: 12, fontSize: 24, color: "#111827" }}>Service availability</h2>
        <p style={{ color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          During early access, MeetIQ may experience downtime, changes, or temporary unavailability. We are not responsible for data loss or service interruptions during this period. Users are responsible for maintaining their own backups.
        </p>
      </section>
    </div>
  );
}
