import {
  cardHeaderStyle,
  cardStyle,
  eyebrowStyle,
  getStatusBadgeStyle,
  mutedTextStyle,
  neutralPillStyle,
  pillRowStyle,
  sectionTitleStyle,
} from "./ui";

type StatusCardProps = {
  status: string;
  modelVersion?: string | null;
  meetingId?: string | number;
  jobId?: string | null;
  isPolling?: boolean;
};

function getStatusLabel(status: string) {
  switch (status.toLowerCase()) {
    case "queued":
      return "Waiting to start";
    case "running":
      return "Processing your meeting";
    case "succeeded":
      return "Notes ready";
    case "failed":
      return "Processing failed";
    default:
      return status || "Unknown status";
  }
}

function getStatusHelp(status: string, isPolling?: boolean) {
  switch (status.toLowerCase()) {
    case "queued":
      return "Your upload is accepted and waiting for worker execution.";
    case "running":
      return isPolling
        ? "We are polling automatically and will load notes as soon as they are ready."
        : "Processing is in progress.";
    case "succeeded":
      return "Notes, key points, action items, and markdown export are available below.";
    case "failed":
      return "The backend job did not finish successfully. Check the worker logs and retry if needed.";
    default:
      return "Status is being checked.";
  }
}

export default function StatusCard({
  status,
  modelVersion,
  meetingId,
  jobId,
  isPolling = false,
}: StatusCardProps) {
  return (
    <section style={cardStyle}>
      <div style={cardHeaderStyle}>
        <div>
          <p style={eyebrowStyle}>Processing</p>
          <h2 style={sectionTitleStyle}>Meeting status</h2>
        </div>

        <span style={getStatusBadgeStyle(status)}>{getStatusLabel(status)}</span>
      </div>

      <p style={{ ...mutedTextStyle, fontSize: 15, color: "#4b5563" }}>
        {getStatusHelp(status, isPolling)}
      </p>

      <div style={{ ...pillRowStyle, marginTop: 16 }}>
        <span style={neutralPillStyle}>Raw status: {status}</span>
        {typeof meetingId !== "undefined" ? (
          <span style={neutralPillStyle}>Meeting ID: {meetingId}</span>
        ) : null}
        {jobId ? (
          <span style={neutralPillStyle}>Job: {jobId.slice(0, 8)}…</span>
        ) : null}
        {modelVersion ? (
          <span style={neutralPillStyle}>Model: {modelVersion}</span>
        ) : null}
        {isPolling && status !== "succeeded" && status !== "failed" ? (
          <span style={neutralPillStyle}>Auto-refresh on</span>
        ) : null}
      </div>
    </section>
  );
}
