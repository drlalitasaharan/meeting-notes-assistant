import Link from "next/link";

export default function Header() {
  return (
    <header
      style={{
        background: "rgba(251, 255, 251, 0.92)",
        borderBottom: "1px solid #cfe6d4",
      }}
    >
      <div
        style={{
          maxWidth: 1080,
          margin: "0 auto",
          padding: "14px 16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 16,
        }}
      >
        <Link
          href="/upload"
          style={{
            textDecoration: "none",
            color: "#123326",
            fontWeight: 700,
            fontSize: 18,
          }}
        >
          MeetIQ by Acjen AI
        </Link>

        <nav style={{ display: "flex", gap: 16 }}>
          <Link
            href="/upload"
            style={{ textDecoration: "none", color: "#2f6f4e", fontWeight: 500 }}
          >
            New Upload
          </Link>
          <Link
            href="/meetings"
            style={{ textDecoration: "none", color: "#2f6f4e", fontWeight: 500 }}
          >
            Meetings
          </Link>
        </nav>
      </div>
    </header>
  );
}
