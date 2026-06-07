"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clearAuthToken, getCurrentUser } from "../lib/api";

function isAuthError(err: unknown) {
  const status = typeof err === "object" && err !== null ? (err as any).status : undefined;
  if (status === 401 || status === 403) {
    return true;
  }

  if (err instanceof Error) {
    return /401|403|unauthorized|authentication credentials/i.test(err.message);
  }

  return false;
}

export default function HomePage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function verifyAuth() {
      try {
        await getCurrentUser();
        if (!active) return;
        router.replace("/upload");
      } catch (err) {
        if (!active) return;

        if (isAuthError(err)) {
          clearAuthToken();
          router.replace("/login?next=/upload");
          return;
        }

        setAuthError("Unable to verify your login status. Please refresh or try again later.");
      } finally {
        if (active) {
          setIsChecking(false);
        }
      }
    }

    verifyAuth();
    return () => {
      active = false;
    };
  }, [router]);

  if (isChecking) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 24,
          color: "#123326",
          background: "#f8fbf8",
        }}
      >
        <div style={{ maxWidth: 560, textAlign: "center" }}>
          <p style={{ margin: 0, fontSize: 18, color: "#4b5563" }}>
            Checking your authentication status...
          </p>
        </div>
      </div>
    );
  }

  if (authError) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 24,
          color: "#123326",
          background: "#f8fbf8",
        }}
      >
        <div style={{ maxWidth: 560, textAlign: "center" }}>
          <div
            style={{
              borderRadius: 20,
              border: "1px solid #cfe6d4",
              background: "#fbfffb",
              padding: 28,
              boxShadow: "0 10px 28px rgba(31, 90, 67, 0.10)",
            }}
          >
            <p style={{ margin: 0, fontSize: 18, color: "#123326", fontWeight: 800 }}>
              {authError}
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              style={{
                marginTop: 20,
                border: "none",
                borderRadius: 14,
                background: "#2f6f4e",
                color: "#ffffff",
                padding: "12px 18px",
                fontSize: 16,
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              Refresh
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
