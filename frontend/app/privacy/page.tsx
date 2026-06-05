export default function PrivacyPage() {
  return (
    <div style={{ display: "grid", gap: 20, maxWidth: 860 }}>
      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h1 style={{ marginTop: 0, marginBottom: 12, fontSize: 32, color: "#111827" }}>Privacy</h1>
        <p style={{ margin: 0, color: "#4b5563", fontSize: 16, lineHeight: 1.6 }}>
          Meeting Notes Assistant stores meeting recordings and generated notes for your account only.
        </p>
      </section>

      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h2 style={{ marginTop: 0, marginBottom: 12, fontSize: 24, color: "#111827" }}>How we use your data</h2>
        <p style={{ color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          We use uploaded audio and video only to generate structured meeting notes and summaries. Files are stored in your account and are not shared with other users.
        </p>
        <p style={{ color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          Only users with permission to upload a recording should do so. If you did not create the recording or lack permission, please do not upload it.
        </p>
        <p style={{ color: "#4b5563", fontSize: 16, lineHeight: 1.7 }}>
          If you have questions about how your recordings are stored or processed, contact support.
        </p>
      </section>
    </div>
  );
}
