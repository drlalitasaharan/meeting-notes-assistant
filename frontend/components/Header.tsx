import Link from "next/link";

export default function Header() {
  return (
    <header
      style={{
        background: "#ffffff",
        borderBottom: "1px solid #e5e7eb",
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
          href="/"
          style={{
            textDecoration: "none",
            color: "#111827",
            fontWeight: 700,
            fontSize: 18,
          }}
        >
          Meeting Notes Assistant
        </Link>

        <nav style={{ display: "flex", gap: 16 }}>
          <Link
            href="/"
            style={{ textDecoration: "none", color: "#374151", fontWeight: 500 }}
          >
            New Upload
          </Link>
          <Link
            href="/meetings"
            style={{ textDecoration: "none", color: "#374151", fontWeight: 500 }}
          >
            Meetings
          </Link>
        </nav>
      </div>
    </header>
  );
}
