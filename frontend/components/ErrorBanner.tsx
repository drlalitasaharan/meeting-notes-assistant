type ErrorBannerProps = {
  message: string;
  actionHref?: string;
  actionLabel?: string;
};

export default function ErrorBanner({
  message,
  actionHref,
  actionLabel,
}: ErrorBannerProps) {
  return (
    <div
      style={{
        background: "#fef2f2",
        border: "1px solid #fecaca",
        color: "#991b1b",
        padding: "12px 14px",
        borderRadius: 10,
        marginTop: 12,
      }}
    >
      <span>{message}</span>
      {actionHref && actionLabel ? (
        <>
          {" "}
          <a
            href={actionHref}
            style={{
              color: "#991b1b",
              fontWeight: 800,
              textDecoration: "underline",
            }}
          >
            {actionLabel}
          </a>
        </>
      ) : null}
    </div>
  );
}
