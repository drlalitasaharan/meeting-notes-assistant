"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import UsageSummaryCard from "../../components/UsageSummaryCard";
import { getCurrentUser, getUsageSummary } from "../../lib/api";
import type { UsageSummary } from "../../lib/types";

export default function UsagePage() {
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [status, setStatus] = useState<"loading" | "authenticated" | "unauthenticated">(
    "loading",
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadUsage() {
      try {
        await getCurrentUser();
        const usageData = await getUsageSummary();

        if (!isMounted) {
          return;
        }

        setUsage(usageData);
        setStatus("authenticated");
        setError(null);
      } catch (err) {
        if (!isMounted) {
          return;
        }

        setUsage(null);
        setStatus("unauthenticated");
        setError(err instanceof Error ? err.message : "Unable to load usage.");
      }
    }

    void loadUsage();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <>

      <main
        style={{
          background: "linear-gradient(180deg, #f7fbf8 0%, #ffffff 100%)",
          minHeight: "100vh",
          padding: "48px 20px 80px",
        }}
      >
        <div style={{ margin: "0 auto", maxWidth: 960 }}>
          <div style={{ marginBottom: 28 }}>
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
              MeetIQ account
            </p>
            <h1 style={{ color: "#123326", fontSize: 42, margin: "10px 0 10px" }}>
              Usage dashboard
            </h1>
            <p style={{ color: "#5d6f66", fontSize: 18, lineHeight: 1.6, margin: 0 }}>
              View your early-access meeting upload limit, remaining uploads, and recording
              length allowance.
            </p>
          </div>

          {status === "loading" ? (
            <section
              style={{
                background: "#ffffff",
                border: "1px solid #d7eadf",
                borderRadius: 24,
                color: "#5d6f66",
                padding: 24,
              }}
            >
              Loading your usage...
            </section>
          ) : null}

          {status === "unauthenticated" ? (
            <section
              style={{
                background: "#ffffff",
                border: "1px solid #d7eadf",
                borderRadius: 24,
                color: "#5d6f66",
                lineHeight: 1.6,
                padding: 24,
              }}
            >
              <h2 style={{ color: "#123326", marginTop: 0 }}>Sign in required</h2>
              <p>{error || "Please sign in to view your usage dashboard."}</p>
              <Link
                href="/login?next=/usage"
                style={{
                  background: "#2f6f4e",
                  borderRadius: 999,
                  color: "#ffffff",
                  display: "inline-block",
                  fontWeight: 800,
                  padding: "12px 18px",
                  textDecoration: "none",
                }}
              >
                Sign in
              </Link>
            </section>
          ) : null}

          {usage ? <UsageSummaryCard usage={usage} /> : null}

          {usage ? (
            <div style={{ display: "flex", gap: 12, marginTop: 22, flexWrap: "wrap" }}>
              <Link
                href="/upload"
                style={{
                  background: "#2f6f4e",
                  borderRadius: 999,
                  color: "#ffffff",
                  fontWeight: 800,
                  padding: "12px 18px",
                  textDecoration: "none",
                }}
              >
                Upload meeting
              </Link>
              <Link
                href="/meetings"
                style={{
                  border: "1px solid #b8d8c5",
                  borderRadius: 999,
                  color: "#123326",
                  fontWeight: 800,
                  padding: "12px 18px",
                  textDecoration: "none",
                }}
              >
                View meetings
              </Link>
            </div>
          ) : null}
        </div>
      </main>
    </>
  );
}
