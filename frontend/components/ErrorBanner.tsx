type ErrorBannerProps = {
  message: string;
};

export default function ErrorBanner({ message }: ErrorBannerProps) {
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
      {message}
    </div>
  );
}
