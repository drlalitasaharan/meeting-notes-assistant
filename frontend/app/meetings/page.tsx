"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getMeetings } from "../../lib/api";
import type { Meeting } from "../../lib/types";

function isCompleteStatus(status?: string | null): boolean {
  const normalized = (status || "").toLowerCase();
  return normalized === "done" || normalized === "succeeded";
}

function getStatusBadgeStyle(status?: string | null) {
  const normalized = (status || "new").toLowerCase();

  if (normalized === "done" || normalized === "succeeded") {
    return {
      background: "#e7f7ed",
      border: "1px solid #bbdfc5",
      color: "#14532d",
    };
  }

  if (normalized === "failed") {
    return {
      background: "#fef2f2",
      border: "1px solid #fecaca",
      color: "#991b1b",
    };
  }

  if (normalized === "running" || normalized === "processing") {
    return {
      background: "#eef2ff",
      border: "1px solid #c7d2fe",
      color: "#3730a3",
    };
  }

  return {
    background: "#fff8ec",
    border: "1px solid #f7d8a8",
    color: "#6f4200",
  };
}

function formatMeetingDate(value?: string | null): string {
  if (!value) {
    return "Created recently";
  }

  return `Created ${new Date(value).toLocaleString()}`;
}


function HowItWorksCard() {
  return (
    <section
      style={{
        background: "#ffffff",
        border: "1px solid #d7eadf",
        borderRadius: 24,
        color: "#5d6f66",
        lineHeight: 1.6,
        marginTop: 22,
        padding: 24,
      }}
    >
      <h2 style={{ color: "#123326", margin: "0 0 12px" }}>
        What to expect from your first upload
      </h2>

      <div
        style={{
          display: "grid",
          gap: 14,
          gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
        }}
      >
        <div>
          <strong style={{ color: "#123326" }}>Use a meeting recording</strong>
          <p style={{ margin: "6px 0 0" }}>
            MeetIQ works best for real conversations with updates, decisions,
            risks, owners, or next steps.
          </p>
        </div>

        <div>
          <strong style={{ color: "#123326" }}>Wait for processing</strong>
          <p style={{ margin: "6px 0 0" }}>
            While a meeting is processing, you can leave the page and return from
            your meetings list.
          </p>
        </div>

        <div>
          <strong style={{ color: "#123326" }}>Review before sharing</strong>
          <p style={{ margin: "6px 0 0" }}>
            Edit names, owners, dates, and decisions before using notes as the
            final meeting record.
          </p>
        </div>
      </div>
    </section>
  );
}

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadMeetings() {
      setIsLoading(true);
      setError(null);

      try {
        const response = await getMeetings();

        if (cancelled) {
          return;
        }

        setMeetings(response.items);
      } catch (err) {
        if (cancelled) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load meetings. Please sign in and try again.",
        );
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadMeetings();

    return () => {
      cancelled = true;
    };
  }, []);

  const authError =
    error &&
    (/401|unauthorized|authentication credentials/i.test(error) ||
      error.toLowerCase().includes("not provided"));

  return (
    <main
      style={{
        background: "linear-gradient(180deg, #f7fbf8 0%, #ffffff 100%)",
        minHeight: "100vh",
        padding: "48px 20px 80px",
      }}
    >
      <div style={{ margin: "0 auto", maxWidth: 980 }}>
        <section
          style={{
            background: "#ffffff",
            border: "1px solid #d7eadf",
            borderRadius: 28,
            boxShadow: "0 18px 45px rgba(18, 51, 38, 0.08)",
            padding: "clamp(28px, 5vw, 48px)",
          }}
        >
          <p
            style={{
              color: "#2f6f4e",
              fontSize: 13,
              fontWeight: 800,
              letterSpacing: "0.08em",
              margin: 0,
              textTransform: "uppercase",
            }}
          >
            MeetIQ meetings
          </p>

          <h1
            style={{
              color: "#123326",
              fontSize: "clamp(34px, 6vw, 52px)",
              letterSpacing: "-0.04em",
              lineHeight: 1.05,
              margin: "12px 0 14px",
            }}
          >
            Your meeting notes, in one place.
          </h1>

          <p
            style={{
              color: "#5d6f66",
              fontSize: 18,
              lineHeight: 1.65,
              margin: 0,
              maxWidth: 720,
            }}
          >
            Review your meeting history, open processed notes, and return to active
            uploads while MeetIQ prepares summaries, decisions, risks, and action items.
          </p>

          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 12,
              marginTop: 26,
            }}
          >
            <Link
              href="/upload"
              style={{
                background: "#2f6f4e",
                borderRadius: 999,
                color: "#ffffff",
                display: "inline-flex",
                fontWeight: 800,
                padding: "13px 20px",
                textDecoration: "none",
              }}
            >
              Upload meeting
            </Link>

            <Link
              href="/support"
              style={{
                border: "1px solid #b8d8c5",
                borderRadius: 999,
                color: "#123326",
                display: "inline-flex",
                fontWeight: 800,
                padding: "13px 20px",
                textDecoration: "none",
              }}
            >
              Send pilot feedback
            </Link>
          </div>
        </section>

        <HowItWorksCard />

        {isLoading ? (
          <section
            style={{
              background: "#ffffff",
              border: "1px solid #d7eadf",
              borderRadius: 24,
              color: "#5d6f66",
              marginTop: 22,
              padding: 24,
            }}
          >
            Loading your meetings...
          </section>
        ) : null}

        {!isLoading && error ? (
          <section
            style={{
              background: "#fff7f6",
              border: "1px solid #f5c2c7",
              borderRadius: 24,
              color: "#991b1b",
              lineHeight: 1.6,
              marginTop: 22,
              padding: 24,
            }}
          >
            <h2 style={{ color: "#7f1d1d", marginTop: 0 }}>
              {authError ? "Sign in required" : "Unable to load meetings"}
            </h2>
            <p style={{ margin: 0 }}>
              {authError ? "Please sign in to view your meeting history." : error}
            </p>

            {authError ? (
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 12,
                  marginTop: 18,
                }}
              >
                <Link
                  href="/login?next=/meetings"
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
                  Sign in
                </Link>

                <Link
                  href="/signup"
                  style={{
                    background: "#ffffff",
                    border: "1px solid #b8d8c5",
                    borderRadius: 999,
                    color: "#123326",
                    display: "inline-flex",
                    fontWeight: 800,
                    padding: "12px 18px",
                    textDecoration: "none",
                  }}
                >
                  Create an account
                </Link>
              </div>
            ) : null}
          </section>
        ) : null}

        {!isLoading && !error && meetings.length === 0 ? (
          <section
            style={{
              background: "#ffffff",
              border: "1px solid #d7eadf",
              borderRadius: 24,
              boxShadow: "0 18px 45px rgba(18, 51, 38, 0.06)",
              marginTop: 22,
              padding: 28,
            }}
          >
            <p
              style={{
                color: "#2f6f4e",
                fontSize: 13,
                fontWeight: 800,
                letterSpacing: "0.08em",
                margin: 0,
                textTransform: "uppercase",
              }}
            >
              No meetings yet
            </p>

            <h2 style={{ color: "#123326", fontSize: 28, margin: "8px 0 10px" }}>
              Upload your first recording.
            </h2>

            <p
              style={{
                color: "#5d6f66",
                fontSize: 16,
                lineHeight: 1.65,
                margin: 0,
                maxWidth: 680,
              }}
            >
              For the first pilot test, start with a structured 5–20 minute recording
              with clear audio. MeetIQ will turn it into notes, decisions, risks, and
              action items.
            </p>

            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: 12,
                marginTop: 22,
              }}
            >
              <Link
                href="/upload"
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
                Upload meeting
              </Link>

              <Link
                href="/support"
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
                Ask for help
              </Link>
            </div>
          </section>
        ) : null}

        {!isLoading && !error && meetings.length > 0 ? (
          <section
            style={{
              background: "#ffffff",
              border: "1px solid #d7eadf",
              borderRadius: 24,
              boxShadow: "0 18px 45px rgba(18, 51, 38, 0.06)",
              marginTop: 22,
              padding: 24,
            }}
          >
            <div
              style={{
                alignItems: "flex-start",
                display: "flex",
                gap: 18,
                justifyContent: "space-between",
                marginBottom: 20,
              }}
            >
              <div>
                <p
                  style={{
                    color: "#2f6f4e",
                    fontSize: 13,
                    fontWeight: 800,
                    letterSpacing: "0.08em",
                    margin: 0,
                    textTransform: "uppercase",
                  }}
                >
                  Meeting history
                </p>
                <h2 style={{ color: "#123326", fontSize: 28, margin: "8px 0 6px" }}>
                  Recent uploads
                </h2>
                <p style={{ color: "#5d6f66", margin: 0 }}>
                  Open a meeting to review, copy, edit, or download notes.
                </p>
              </div>

              <span
                style={{
                  background: "#e7f7ed",
                  borderRadius: 999,
                  color: "#14532d",
                  fontSize: 13,
                  fontWeight: 800,
                  padding: "8px 12px",
                  whiteSpace: "nowrap",
                }}
              >
                {meetings.length} total
              </span>
            </div>

            <div style={{ display: "grid", gap: 14 }}>
              {meetings.map((meeting) => {
                const statusStyle = getStatusBadgeStyle(meeting.status);

                return (
                  <Link
                    key={meeting.id}
                    href={`/meetings/${meeting.id}`}
                    style={{
                      background: "#f7fbf8",
                      border: "1px solid #d7eadf",
                      borderRadius: 18,
                      color: "inherit",
                      display: "block",
                      padding: 18,
                      textDecoration: "none",
                    }}
                  >
                    <div
                      style={{
                        alignItems: "flex-start",
                        display: "flex",
                        flexWrap: "wrap",
                        gap: 16,
                        justifyContent: "space-between",
                      }}
                    >
                      <div style={{ minWidth: 0 }}>
                        <h3
                          style={{
                            color: "#123326",
                            fontSize: 20,
                            margin: 0,
                          }}
                        >
                          {meeting.title || `Meeting ${meeting.id}`}
                        </h3>
                        <p
                          style={{
                            color: "#5d6f66",
                            fontSize: 15,
                            margin: "10px 0 0",
                          }}
                        >
                          {formatMeetingDate(meeting.created_at)}
                        </p>
                        {isCompleteStatus(meeting.status) ? (
                          <p
                            style={{
                              color: "#2f6f4e",
                              fontSize: 14,
                              fontWeight: 700,
                              margin: "10px 0 0",
                            }}
                          >
                            Notes are ready to review.
                          </p>
                        ) : null}
                      </div>

                      <span
                        style={{
                          ...statusStyle,
                          alignItems: "center",
                          borderRadius: 999,
                          display: "inline-flex",
                          fontSize: 13,
                          fontWeight: 800,
                          justifyContent: "center",
                          minWidth: 110,
                          padding: "8px 12px",
                          textTransform: "capitalize",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {meeting.status || "new"}
                      </span>
                    </div>
                  </Link>
                );
              })}
            </div>

            <div
              style={{
                background: "#f7fbf8",
                border: "1px solid #d7eadf",
                borderRadius: 18,
                color: "#365342",
                lineHeight: 1.65,
                marginTop: 18,
                padding: 16,
              }}
            >
              <strong style={{ color: "#123326" }}>Pilot feedback:</strong>{" "}
              If an upload gets stuck or the notes miss important decisions,{" "}
              <Link href="/support" style={{ color: "#2f6f4e", fontWeight: 800 }}>
                send feedback
              </Link>{" "}
              with the meeting title or ID.
            </div>
          </section>
        ) : null}
      </div>
    </main>
  );
}
