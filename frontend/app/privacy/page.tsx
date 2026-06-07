export default function PrivacyPage() {
  return (
    <div style={{ display: "grid", gap: 20, maxWidth: 860 }}>
      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h1 style={{ marginTop: 0, marginBottom: 12, fontSize: 32, color: "#111827" }}>Privacy</h1>
        <p style={{ margin: 0, color: "#4b5563", fontSize: 16, lineHeight: 1.6 }}>
          MeetIQ by Acjen AI stores meeting recordings and generated notes for your account only.
        </p>
      </section>

      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h2 style={{ marginTop: 0, marginBottom: 12, fontSize: 24, color: "#111827" }}>How we use your data</h2>
        <p style={{ color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          You upload meeting audio or video recordings to MeetIQ. We process these recordings to generate structured meeting notes, summaries, action items, and other analysis. Files are stored in your account and are not shared with other users.
        </p>
        <p style={{ color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          <strong>Important:</strong> Only upload recordings that you own or have explicit permission to upload. Do not upload private, confidential, or proprietary content unless you are authorized to do so.
        </p>
      </section>

      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h2 style={{ marginTop: 0, marginBottom: 12, fontSize: 24, color: "#111827" }}>AI-generated content</h2>
        <p style={{ color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          AI-generated summaries, action items, decisions, and other analysis may contain mistakes, omissions, or inaccuracies. Always review generated content before relying on it for decisions.
        </p>
        <p style={{ color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          MeetIQ is not a legal, regulatory, compliance, or official transcript system. For sensitive or official records, use human transcription or certified recording services.
        </p>
      </section>

      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h2 style={{ marginTop: 0, marginBottom: 12, fontSize: 24, color: "#111827" }}>Questions?</h2>
        <p style={{ color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          If you have questions about how your recordings are stored, processed, or shared, contact us at <strong>support@acjen.ai</strong>.
        </p>
      </section>
    </div>
  );
}
