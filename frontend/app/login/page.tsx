"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { loginUser } from "../../lib/api";

function isValidNextPath(path: string): boolean {
  return typeof path === "string" && path.startsWith("/") && !path.includes("//");
}

function LoginPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const requestedNextPath = searchParams.get("next") ?? "";
  const nextPath = isValidNextPath(requestedNextPath) ? requestedNextPath : "/meetings";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (!email.trim() || !password.trim()) {
      setError("Please enter both email and password.");
      return;
    }

    setIsSubmitting(true);
    try {
      await loginUser(email.trim(), password);
      router.push(nextPath);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Login failed. Please check your credentials and try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 20, maxWidth: 760 }}>
      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h1 style={{ marginTop: 0, marginBottom: 12, fontSize: 32, color: "#111827" }}>Sign in</h1>
        <p style={{ margin: 0, color: "#4b5563", fontSize: 16, lineHeight: 1.6 }}>
          Access your meeting uploads, review history, and continue any active transcription jobs.
        </p>
      </section>

      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <form onSubmit={handleSubmit} style={{ display: "grid", gap: 18 }}>
          <label style={{ display: "grid", gap: 6, fontSize: 16, fontWeight: 700, color: "#111827" }}>
            Email address
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              style={{ width: "100%", padding: 12, borderRadius: 12, border: "1px solid #d1d5db", fontSize: 16 }}
            />
          </label>

          <label style={{ display: "grid", gap: 6, fontSize: 16, fontWeight: 700, color: "#111827" }}>
            Password
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                autoComplete="current-password"
                onChange={(event) => setPassword(event.target.value)}
                style={{ flex: 1, padding: 12, borderRadius: 12, border: "1px solid #d1d5db", fontSize: 16 }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                aria-pressed={showPassword}
                style={{
                  padding: "8px 12px",
                  borderRadius: 8,
                  border: "1px solid #d1d5db",
                  background: "#f9fafb",
                  color: "#4b5563",
                  cursor: "pointer",
                  fontSize: 14,
                  fontWeight: 600,
                  whiteSpace: "nowrap",
                }}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </label>

          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              width: "100%",
              padding: 14,
              borderRadius: 14,
              border: "none",
              background: "#2f6f4e",
              color: "#ffffff",
              fontWeight: 700,
              cursor: isSubmitting ? "not-allowed" : "pointer",
            }}
          >
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>

          {error ? (
            <div style={{ color: "#991b1b", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 12, padding: 14, fontSize: 16 }}>
              {error}
            </div>
          ) : null}
        </form>

        <p style={{ margin: "8px 0 0", textAlign: "center", color: "#4b5563", fontSize: 16 }}>
          New to MeetIQ?{" "}
          <Link
            href="/signup"
            style={{ color: "#2f6f4e", fontWeight: 700, textDecoration: "none" }}
          >
            Create an account
          </Link>
        </p>
      </section>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<main style={{ padding: 24 }}>Loading login...</main>}>
      <LoginPageContent />
    </Suspense>
  );
}
