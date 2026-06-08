"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signupUser } from "../../lib/api";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [organizationName, setOrganizationName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (!email.trim() || !password.trim() || !firstName.trim() || !lastName.trim()) {
      setError("Please enter email, password, first name, and last name.");
      return;
    }

    setIsSubmitting(true);
    try {
      await signupUser(
        email.trim(),
        password,
        firstName.trim(),
        lastName.trim(),
        organizationName.trim() || undefined,
      );
      router.push("/meetings");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Sign up failed. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 20, maxWidth: 760 }}>
      <section style={{ background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: 16, padding: 28 }}>
        <h1 style={{ marginTop: 0, marginBottom: 12, fontSize: 32, color: "#111827" }}>Create an account</h1>
        <p style={{ margin: 0, color: "#4b5563", fontSize: 16, lineHeight: 1.6 }}>
          Start saving meeting recordings to your own private workspace.
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

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <label style={{ display: "grid", gap: 6, fontSize: 16, fontWeight: 700, color: "#111827" }}>
              First name
              <input
                value={firstName}
                onChange={(event) => setFirstName(event.target.value)}
                style={{ width: "100%", padding: 12, borderRadius: 12, border: "1px solid #d1d5db", fontSize: 16 }}
              />
            </label>

            <label style={{ display: "grid", gap: 6, fontSize: 16, fontWeight: 700, color: "#111827" }}>
              Last name
              <input
                value={lastName}
                onChange={(event) => setLastName(event.target.value)}
                style={{ width: "100%", padding: 12, borderRadius: 12, border: "1px solid #d1d5db", fontSize: 16 }}
              />
            </label>
          </div>

          <label style={{ display: "grid", gap: 6, fontSize: 16, fontWeight: 700, color: "#111827" }}>
            Organization (optional)
            <input
              value={organizationName}
              onChange={(event) => setOrganizationName(event.target.value)}
              style={{ width: "100%", padding: 12, borderRadius: 12, border: "1px solid #d1d5db", fontSize: 16 }}
            />
          </label>

          <label style={{ display: "grid", gap: 6, fontSize: 16, fontWeight: 700, color: "#111827" }}>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              style={{ width: "100%", padding: 12, borderRadius: 12, border: "1px solid #d1d5db", fontSize: 16 }}
            />
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
            {isSubmitting ? "Creating account..." : "Create account"}
          </button>

          {error ? (
            <div style={{ color: "#991b1b", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 12, padding: 14, fontSize: 16 }}>
              {error}
            </div>
          ) : null}
        </form>

        <p style={{ margin: 0, textAlign: "center", color: "#4b5563", fontSize: 16 }}>
          Already have an account?{" "}
          <Link
            href="/login"
            style={{ color: "#2f6f4e", fontWeight: 700, textDecoration: "none" }}
          >
            Sign in
          </Link>
        </p>
      </section>
    </div>
  );
}
