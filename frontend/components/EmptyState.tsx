import Link from "next/link";

type EmptyStateProps = {
  eyebrow?: string;
  title: string;
  body: string;
  primaryHref?: string;
  primaryLabel?: string;
  secondaryHref?: string;
  secondaryLabel?: string;
};

export default function EmptyState({
  eyebrow = "Getting started",
  title,
  body,
  primaryHref,
  primaryLabel,
  secondaryHref,
  secondaryLabel,
}: EmptyStateProps) {
  return (
    <section
      style={{
        background: "#ffffff",
        border: "1px solid #d7eadf",
        borderRadius: 24,
        color: "#5d6f66",
        lineHeight: 1.6,
        marginTop: 22,
        padding: 26,
      }}
    >
      <p
        style={{
          color: "#2f6f4e",
          fontSize: 12,
          fontWeight: 800,
          letterSpacing: "0.08em",
          margin: 0,
          textTransform: "uppercase",
        }}
      >
        {eyebrow}
      </p>

      <h2 style={{ color: "#123326", margin: "10px 0 8px" }}>{title}</h2>
      <p style={{ margin: 0, maxWidth: 720 }}>{body}</p>

      {(primaryHref && primaryLabel) || (secondaryHref && secondaryLabel) ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 20 }}>
          {primaryHref && primaryLabel ? (
            <Link
              href={primaryHref}
              style={{
                background: "#2f6f4e",
                borderRadius: 999,
                color: "#ffffff",
                display: "inline-flex",
                fontWeight: 800,
                padding: "12px 18px",
                textDecoration: "none",
              }}
            >
              {primaryLabel}
            </Link>
          ) : null}

          {secondaryHref && secondaryLabel ? (
            <Link
              href={secondaryHref}
              style={{
                border: "1px solid #b8d8c5",
                borderRadius: 999,
                color: "#123326",
                display: "inline-flex",
                fontWeight: 800,
                padding: "12px 18px",
                textDecoration: "none",
              }}
            >
              {secondaryLabel}
            </Link>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
