export default function MeetingsPage() {
  return (
    <div
      style={{
        display: "grid",
        gap: 20,
        maxWidth: 1080,
      }}
    >
      <section
        style={{
          background: "#ffffff",
          border: "1px solid #e5e7eb",
          borderRadius: 16,
          padding: 24,
        }}
      >
        <h1
          style={{
            marginTop: 0,
            marginBottom: 12,
            fontSize: 32,
            color: "#111827",
          }}
        >
          Meetings
        </h1>

        <p
          style={{
            margin: 0,
            color: "#4b5563",
            fontSize: 16,
            lineHeight: 1.6,
          }}
        >
          This page will show recent meeting uploads and results.
        </p>
      </section>
    </div>
  );
}
