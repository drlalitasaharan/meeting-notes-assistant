"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import ActionItemsCard from "../../../components/ActionItemsCard";
import ErrorBanner from "../../../components/ErrorBanner";
import KeyPointsCard from "../../../components/KeyPointsCard";
import StatusCard from "../../../components/StatusCard";
import SummaryCard from "../../../components/SummaryCard";
import TranscriptCard from "../../../components/TranscriptCard";
import {
  cardStyle,
  eyebrowStyle,
  mutedTextStyle,
  neutralPillStyle,
  pillRowStyle,
} from "../../../components/ui";
import {
  deleteMeeting,
  getJobStatus,
  getMeetingMarkdown,
  getMeetingNotes,
  updateMeetingNotesSection,
} from "../../../lib/api";
import type { EditableNotesSection } from "../../../lib/types";

type MeetingNotes = {
  meeting_id: number;
  status?: string;
  model_version?: string;
  summary: string;
  key_points: string[];
  action_items: string[];
};

type JobResponse = {
  id?: string;
  status?: string;
  artifact_url?: string | null;
};

function normalizeStatus(raw?: string | null): string {
  const status = (raw ?? "").toLowerCase().trim();

  if (
    ["done", "succeeded", "success", "completed", "complete", "finished"].includes(
      status,
    )
  ) {
    return "succeeded";
  }

  if (["failed", "error"].includes(status)) {
    return "failed";
  }

  if (["queued", "pending"].includes(status)) {
    return "queued";
  }

  if (["running", "started", "deferred", "processing", "in_progress"].includes(status)) {
    return "running";
  }

  return status || "queued";
}

function isPollingStatus(status: string) {
  const normalized = normalizeStatus(status);
  return normalized === "queued" || normalized === "running";
}

function formatLastUpdated(value: number | null) {
  if (!value) return "Not loaded yet";

  return new Date(value).toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function MeetingResultsPage() {
  const params = useParams<{ id: string }>();
  const meetingId = params.id;
  const router = useRouter();
  const searchParams = useSearchParams();
  const jobId = searchParams.get("jobId");

  const [status, setStatus] = useState("queued");
  const [notes, setNotes] = useState<MeetingNotes | null>(null);
  const [markdown, setMarkdown] = useState("");
  const [error, setError] = useState("");
  const [loadingResults, setLoadingResults] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);

  const loadNotes = useCallback(
    async (strict: boolean): Promise<boolean> => {
      try {
        const [notesResponse, markdownResponse] = await Promise.all([
          getMeetingNotes(Number(meetingId)),
          getMeetingMarkdown(Number(meetingId)),
        ]);

        setNotes(notesResponse);
        setMarkdown(markdownResponse);
        setStatus(normalizeStatus(notesResponse.status ?? "succeeded"));
        setLastUpdated(Date.now());
        setLoadingResults(false);
        setError("");
        return true;
      } catch (err) {
        if (strict) {
          const message =
            err instanceof Error
              ? err.message
              : "Failed to load meeting notes.";
          setError(message);
          setLoadingResults(false);
        }
        return false;
      }
    },
    [meetingId],
  );

  const saveNotesSection = useCallback(
    async (
      section: EditableNotesSection,
      value: string | string[],
    ): Promise<void> => {
      await updateMeetingNotesSection(
        Number(meetingId),
        section,
        value,
      );

      const refreshed = await loadNotes(true);
      if (!refreshed) {
        throw new Error(
          "The notes were saved, but the page could not refresh.",
        );
      }
    },
    [loadNotes, meetingId],
  );

  const handleDeleteMeeting = useCallback(async () => {
    if (isDeleting) return;

    const confirmed = window.confirm(
      "Delete this meeting? This will remove the meeting, generated notes, and the uploaded recording reference. Download your notes first if you need a local copy.",
    );

    if (!confirmed) {
      return;
    }

    setIsDeleting(true);
    setError("");

    try {
      await deleteMeeting(Number(meetingId));
      router.push("/meetings");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to delete meeting.";
      setError(message);
      setIsDeleting(false);
    }
  }, [isDeleting, meetingId, router]);

  const checkJob = useCallback(async () => {
    if (!jobId) return null;
    return getJobStatus(jobId);
  }, [jobId]);

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      setLoadingResults(true);
      setError("");

      const notesLoaded = await loadNotes(false);
      if (cancelled) return;

      if (notesLoaded) {
        return;
      }

      if (!jobId) {
        setStatus("queued");
        setLoadingResults(false);
        return;
      }

      try {
        const job = await checkJob();
        if (!job || cancelled) return;

        const nextStatus = normalizeStatus(job.status);
        setStatus(nextStatus);

        if (nextStatus === "succeeded") {
          await loadNotes(true);
        } else if (nextStatus === "failed") {
          setError("Processing failed. Check worker logs and try again.");
          setLoadingResults(false);
        } else {
          setLoadingResults(false);
        }
      } catch (err) {
        if (cancelled) return;
        const message =
          err instanceof Error
            ? err.message
            : "Failed to check meeting status.";
        setError(message);
        setLoadingResults(false);
      }
    }

    initialize();

    return () => {
      cancelled = true;
    };
  }, [checkJob, jobId, loadNotes]);

  useEffect(() => {
    if (!jobId || !isPollingStatus(status) || notes) return;

    const timer = window.setInterval(async () => {
      try {
        const notesLoaded = await loadNotes(false);
        if (notesLoaded) return;

        const job = await checkJob();
        if (!job) return;

        const nextStatus = normalizeStatus(job.status ?? status);
        setStatus(nextStatus);

        if (nextStatus === "succeeded") {
          await loadNotes(true);
        } else if (nextStatus === "failed") {
          setError("Processing failed. Check worker logs and try again.");
          setLoadingResults(false);
        }
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Failed while polling job status.";
        setError(message);
      }
    }, 2500);

    return () => window.clearInterval(timer);
  }, [checkJob, jobId, loadNotes, notes, status]);

  const modelVersion = notes?.model_version ?? null;

  const pageTitle = useMemo(
    () =>
      notes
        ? "Your meeting notes are ready"
        : "Preparing your meeting notes",
    [notes],
  );

  return (
    <div
      style={{
        display: "grid",
        gap: 20,
        width: "100%",
        maxWidth: 980,
        minWidth: 0,
      }}
    >
      <section
        style={{
          ...cardStyle,
          padding: "clamp(26px, 5vw, 42px)",
          borderColor: "#bbf7d0",
          background:
            "linear-gradient(135deg, #ecfdf3 0%, #f7fcf8 58%, #ffffff 100%)",
          boxShadow: "0 12px 34px rgba(22, 101, 52, 0.08)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: 24,
            flexWrap: "wrap",
          }}
        >
          <div style={{ maxWidth: 620 }}>
            <p style={{ ...eyebrowStyle, color: "#166534" }}>
              MeetIQ by Acjen AI
            </p>

            <h1
              style={{
                margin: "10px 0 12px",
                fontSize: "clamp(30px, 5vw, 44px)",
                lineHeight: 1.08,
                letterSpacing: "-0.03em",
                color: "#102a1a",
              }}
            >
              {pageTitle}
            </h1>

            <p
              style={{
                ...mutedTextStyle,
                fontSize: 17,
                color: "#4b6353",
              }}
            >
              {notes

                ? "Review, edit, copy, and export your notes."

                : "MeetIQ is processing your recording. You can return from Meetings when your notes are ready."}

              </p>
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              flexWrap: "wrap",
              gap: 10,
            }}
          >
            <a
              href="/upload"
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "11px 16px",
                borderRadius: 10,
                border: "1px solid #166534",
                background: "#166534",
                color: "#ffffff",
                fontWeight: 700,
                textDecoration: "none",
              }}
            >
              Upload another recording
            </a>

            <a
              href="/meetings"
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "11px 16px",
                borderRadius: 10,
                border: "1px solid #bbd7c2",
                background: "#ffffff",
                color: "#166534",
                fontWeight: 700,
                textDecoration: "none",
              }}
            >
              View all meetings
            </a>

            <button
              type="button"
              onClick={handleDeleteMeeting}
              disabled={isDeleting}
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "11px 16px",
                borderRadius: 10,
                border: "1px solid #fecaca",
                background: isDeleting ? "#fef2f2" : "#ffffff",
                color: "#b91c1c",
                cursor: isDeleting ? "not-allowed" : "pointer",
                fontWeight: 700,
              }}
            >
              {isDeleting ? "Deleting..." : "Delete meeting"}
            </button>
          </div>
        </div>
      </section>

      <StatusCard
        status={status}
        modelVersion={modelVersion}
        meetingId={meetingId}
        jobId={jobId}
        lastUpdated={formatLastUpdated(lastUpdated)}
        isPolling={Boolean(jobId && isPollingStatus(status) && !notes)}
      />

      {error ? <ErrorBanner message={error} /> : null}

      {error ? (
        <aside
          style={{
            background: "#fff8ec",
            border: "1px solid #f7d8a8",
            borderRadius: 16,
            color: "#6f4200",
            fontSize: 14,
            lineHeight: 1.6,
            padding: "14px 16px",
          }}
        >
          <strong>Need help with this meeting?</strong>{" "}
          <a
            href="/support"
            style={{
              color: "#2f6f4e",
              fontWeight: 800,
              textDecoration: "none",
            }}
          >
            Contact support
          </a>{" "}
          and include Meeting ID {meetingId}.
        </aside>
      ) : null}

      {notes ? (
        <aside
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: 12,
            padding: "16px 18px",
            borderRadius: 16,
            border: "1px solid #bbf7d0",
            background: "#f0fdf4",
            color: "#365342",
            fontSize: 14,
            lineHeight: 1.6,
          }}
        >
          <span aria-hidden="true" style={{ fontSize: 18 }}>
            ✓
          </span>
          <span>
            Review names, owners, deadlines, and important decisions before
            sharing your notes. Download your Markdown export below before deleting this meeting
            if you need a local copy.
          </span>
        </aside>
      ) : null}

      {loadingResults && !notes ? (
        <section style={cardStyle}>
          <h2 style={{ marginTop: 0, marginBottom: 8, color: "#111827" }}>
            Loading results
          </h2>
          <p style={mutedTextStyle}>
            We will refresh this page state automatically while the backend job is still running.
          </p>
        </section>
      ) : null}

      {notes ? (
        <>
          <SummaryCard
            summary={notes.summary}
            onSave={(summary) =>
              saveNotesSection("summary", summary)
            }
          />

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: 20,
            }}
          >
            <KeyPointsCard
              items={notes.key_points}
              onSave={(items) =>
                saveNotesSection("key_points", items)
              }
            />
            <ActionItemsCard
              items={notes.action_items}
              onSave={(items) =>
                saveNotesSection("action_items", items)
              }
            />
          </div>

          {markdown ? (
            <TranscriptCard
              markdown={markdown}
              filename={`meeting-${meetingId}-notes.md`}
            />
          ) : null}
        </>
      ) : null}
    </div>
  );
}
