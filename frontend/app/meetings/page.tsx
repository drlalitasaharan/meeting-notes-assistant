"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getMeetings } from "../../lib/api";
import type { Meeting } from "../../lib/types";

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
        if (cancelled) return;
        setMeetings(response.items);
      } catch (err) {
        if (cancelled) return;
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

    loadMeetings();
    return () => {
      cancelled = true;
    };
  }, []);

  const authError = error && /401|unauthorized/i.test(error);

  return (
    <div style={{ display: "grid", gap: 20, maxWidth: 1080 }}>
      <section
        style={{
          background: "#ffffff",
          border: "1px solid #e5e7eb",
          borderRadius: 16,
          padding: 24,
        }}
      >
        <h1
          style={{
            marginTop: 0,
            marginBottom: 12,
            fontSize: 32,
            color: "#111827",
          }}
        >
          Meetings
        </h1>

        <p
          style={{
            margin: 0,
            color: "#4b5563",
            fontSize: 16,
            lineHeight: 1.6,
          }}
        >
          Review your personal meeting history, access active uploads, and open detailed notes.
        </p>
      </section>

      {isLoading ? (
        <section
          style={{
            background: "#ffffff",
            border: "1px solid #e5e7eb",
            borderRadius: 16,
            padding: 24,
          }}
        >
          <p style={{ margin: 0, color: "#4b5563", fontSize: 16 }}>
            Loading your meetings...
          </p>
        </section>
      ) : error ? (
        <section
          style={{
            background: "#fff7f6",
            border: "1px solid #f5c2c7",
            borderRadius: 16,
            padding: 24,
          }}
        >
          <p style={{ margin: 0, color: "#991b1b", fontSize: 16, lineHeight: 1.6 }}>
            {authError
              ? "Please sign in to access your meetings."
              : error}
          </p>
          {authError ? (
            <div style={{ marginTop: 16, display: "flex", gap: 12, flexWrap: "wrap" }}>
              <Link
                href="/login"
                style={{
                  padding: "12px 18px",
                  borderRadius: 14,
                  background: "#2f6f4e",
                  color: "#ffffff",
                  textDecoration: "none",
                  fontWeight: 700,
                }}
              >
                Sign in
              </Link>
              <Link
                href="/signup"
                style={{
                  padding: "12px 18px",
                  borderRadius: 14,
                  background: "#ffffff",
                  color: "#2f6f4e",
                  border: "1px solid #2f6f4e",
                  textDecoration: "none",
                  fontWeight: 700,
                }}
              >
                Create an account
              </Link>
            </div>
          ) : null}
        </section>
      ) : meetings.length === 0 ? (
        <section
          style={{
            background: "#ffffff",
            border: "1px solid #e5e7eb",
            borderRadius: 16,
            padding: 24,
          }}
        >
          <p style={{ margin: 0, color: "#4b5563", fontSize: 16, lineHeight: 1.6 }}>
            You don’t have any meetings yet. Upload a recording to get started.
          </p>
          <Link
            href="/upload"
            style={{
              display: "inline-block",
              marginTop: 18,
              padding: "12px 18px",
              borderRadius: 14,
              background: "#2f6f4e",
              color: "#ffffff",
              textDecoration: "none",
              fontWeight: 700,
            }}
          >
            Upload meeting
          </Link>
        </section>
      ) : (
        <section
          style={{
            background: "#ffffff",
            border: "1px solid #e5e7eb",
            borderRadius: 16,
            padding: 24,
          }}
        >
          <div style={{ display: "grid", gap: 18 }}>
            {meetings.map((meeting) => (
              <Link
                key={meeting.id}
                href={`/meetings/${meeting.id}`}
                style={{
                  display: "block",
                  padding: 18,
                  borderRadius: 16,
                  border: "1px solid #e5e7eb",
                  textDecoration: "none",
                  color: "inherit",
                  background: "#f8faf9",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
                  <div>
                    <h2
                      style={{
                        margin: 0,
                        fontSize: 20,
                        color: "#111827",
                      }}
                    >
                      {meeting.title || `Meeting ${meeting.id}`}
                    </h2>
                    <p
                      style={{
                        margin: "10px 0 0",
                        color: "#4b5563",
                        fontSize: 15,
                      }}
                    >
                      Created {meeting.created_at ? new Date(meeting.created_at).toLocaleString() : "recently"}
                    </p>
                  </div>
                  <div
                    style={{
                      minWidth: 120,
                      padding: "8px 14px",
                      borderRadius: 999,
                      background: meeting.status === "done" || meeting.status === "succeeded" ? "#e7f7ed" : "#eef2ff",
                      color: meeting.status === "done" || meeting.status === "succeeded" ? "#14532d" : "#3730a3",
                      fontWeight: 700,
                      textTransform: "capitalize",
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    {meeting.status || "new"}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
