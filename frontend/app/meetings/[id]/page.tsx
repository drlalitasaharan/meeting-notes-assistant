"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
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

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type PageProps = {
  params: {
    id: string;
  };
};

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

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

async function fetchText(path: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.text();
}

function formatLastUpdated(value: number | null) {
  if (!value) return "Not loaded yet";

  return new Date(value).toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function MeetingResultsPage({ params }: PageProps) {
  const meetingId = params.id;
  const searchParams = useSearchParams();
  const jobId = searchParams.get("jobId");

  const [status, setStatus] = useState("queued");
  const [notes, setNotes] = useState<MeetingNotes | null>(null);
  const [markdown, setMarkdown] = useState("");
  const [error, setError] = useState("");
  const [loadingResults, setLoadingResults] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);

  const loadNotes = useCallback(
    async (strict: boolean): Promise<boolean> => {
      try {
        const [notesResponse, markdownResponse] = await Promise.all([
          fetchJson<MeetingNotes>(`/v1/meetings/${meetingId}/notes/ai`),
          fetchText(`/v1/meetings/${meetingId}/notes.md`),
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

  const checkJob = useCallback(async () => {
    if (!jobId) return null;
    return fetchJson<JobResponse>(`/v1/jobs/${jobId}`);
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

  const pageTitle = useMemo(() => {
    if (notes?.meeting_id) {
      return `Meeting ${notes.meeting_id} results`;
    }
    return `Meeting ${meetingId} results`;
  }, [meetingId, notes?.meeting_id]);

  return (
    <div
      style={{
        display: "grid",
        gap: 20,
        maxWidth: 1180,
      }}
    >
      <section style={cardStyle}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: 16,
            flexWrap: "wrap",
          }}
        >
          <div>
            <p style={eyebrowStyle}>Meeting notes assistant</p>
            <h1
              style={{
                margin: "8px 0 10px",
                fontSize: 32,
                lineHeight: 1.15,
                color: "#111827",
              }}
            >
              {pageTitle}
            </h1>
            <p style={{ ...mutedTextStyle, fontSize: 15 }}>
              Review summary, key points, action items, and the markdown export in one place.
            </p>
          </div>

          <div style={pillRowStyle}>
            <span style={neutralPillStyle}>Meeting ID: {meetingId}</span>
            {jobId ? (
              <span style={neutralPillStyle}>Job: {jobId.slice(0, 8)}…</span>
            ) : null}
            <span style={neutralPillStyle}>
              Last updated: {formatLastUpdated(lastUpdated)}
            </span>
          </div>
        </div>
      </section>

      <StatusCard
        status={status}
        modelVersion={modelVersion}
        meetingId={meetingId}
        jobId={jobId}
        isPolling={Boolean(jobId && isPollingStatus(status) && !notes)}
      />

      {error ? <ErrorBanner message={error} /> : null}

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
          <SummaryCard summary={notes.summary} />

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
              gap: 20,
            }}
          >
            <KeyPointsCard items={notes.key_points} />
            <ActionItemsCard items={notes.action_items} />
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
