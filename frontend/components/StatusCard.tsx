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
  meetingId: string | number;
  jobId?: string | null;
  lastUpdated?: string;
  isPolling?: boolean;
};

function statusLabel(status: string): string {
  const normalized = status.toLowerCase();

  if (normalized === "succeeded") return "Notes ready";
  if (normalized === "failed") return "Processing failed";
  if (normalized === "running") return "Processing recording";

  return "Waiting to process";
}

function statusDescription(status: string, isPolling: boolean): string {
  const normalized = status.toLowerCase();

  if (normalized === "succeeded") {
    return "Your structured meeting notes are available below.";
  }

  if (normalized === "failed") {
    return "We could not finish processing this recording. Please try again.";
  }

  if (normalized === "running") {
    return isPolling
      ? "MeetIQ is processing your recording and will refresh this page automatically."
      : "MeetIQ is processing your recording.";
  }

  return "Your recording is queued and will begin processing shortly.";
}

export default function StatusCard({
  status,
  modelVersion,
  meetingId,
  jobId,
  lastUpdated,
  isPolling = false,
}: StatusCardProps) {
  const normalizedStatus = status.toLowerCase();

  return (
    <section
      style={{
        ...cardStyle,
        minWidth: 0,
        borderColor:
          normalizedStatus === "succeeded" ? "#bbf7d0" : "#e5e7eb",
      }}
    >
      <div style={cardHeaderStyle}>
        <div>
          <p style={eyebrowStyle}>Status</p>
          <h2 style={sectionTitleStyle}>Meeting status</h2>
        </div>

        <span style={getStatusBadgeStyle(status)}>
          {statusLabel(status)}
        </span>
      </div>

      <p style={mutedTextStyle}>
        {statusDescription(status, isPolling)}
      </p>

      <details style={{ marginTop: 18 }}>
        <summary
          style={{
            cursor: "pointer",
            color: "#4b6353",
            fontSize: 14,
            fontWeight: 700,
          }}
        >
          Processing details
        </summary>

        <div style={{ ...pillRowStyle, marginTop: 14 }}>
          <span style={neutralPillStyle}>
            Meeting ID: {meetingId}
          </span>

          {jobId ? (
            <span style={neutralPillStyle}>
              Job: {jobId.slice(0, 8)}…
            </span>
          ) : null}

          {modelVersion ? (
            <span style={neutralPillStyle}>
              Model: {modelVersion}
            </span>
          ) : null}

          {lastUpdated ? (
            <span style={neutralPillStyle}>
              Last updated: {lastUpdated}
            </span>
          ) : null}
        </div>
      </details>
    </section>
  );
}
