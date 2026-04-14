import UploadForm from "../components/UploadForm";

export default function HomePage() {
  return (
    <div style={{ display: "grid", gap: 20 }}>
      <section
        style={{
          background: "#ffffff",
          border: "1px solid #e5e7eb",
          borderRadius: 16,
          padding: 24,
        }}
      >
        <h1 style={{ marginTop: 0, marginBottom: 12, fontSize: 32 }}>
          Turn meetings into clear notes
        </h1>
        <p style={{ margin: 0, color: "#4b5563", fontSize: 16, lineHeight: 1.6 }}>
          Upload an audio or video file and get a summary, key points, and action items.
        </p>
      </section>

      <UploadForm />
    </div>
  );
}
