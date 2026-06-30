"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import {
  clearAuthToken,
  createMeeting,
  getCurrentUser,
  uploadMeetingFile,
} from "../../lib/api";

const MAX_UPLOAD_BYTES = 24 * 1024 * 1024;

const SUPPORTED_EXTENSIONS = new Set([
  "flac",
  "m4a",
  "mp3",
  "mp4",
  "mpeg",
  "mpga",
  "oga",
  "ogg",
  "wav",
  "webm",
]);

function getFileExtension(fileName: string) {
  return fileName.split(".").pop()?.toLowerCase() ?? "";
}

function validateUploadFile(file: File): string | null {
  const extension = getFileExtension(file.name);

  if (!SUPPORTED_EXTENSIONS.has(extension)) {
    return "Unsupported file type. Please upload m4a, mp3, mp4, wav, webm, ogg, flac, mpeg, mpga, or oga.";
  }

  if (file.size > MAX_UPLOAD_BYTES) {
    return "This file is too large for hosted transcription. Please upload a file under 24 MB or use compressed m4a/mp3.";
  }

  return null;
}

const cardStyle = {
  background: "#fbfffb",
  border: "1px solid #cfe6d4",
  borderRadius: 20,
  boxShadow: "0 10px 28px rgba(31, 90, 67, 0.10)",
};

const inputStyle = {
  width: "100%",
  border: "1px solid #bfd8c5",
  borderRadius: 14,
  padding: "12px 14px",
  fontSize: 16,
  color: "#123326",
  boxSizing: "border-box" as const,
};

const labelStyle = {
  display: "block",
  marginBottom: 10,
  fontSize: 16,
  fontWeight: 800,
  color: "#123326",
};


function UploadGuidanceCard() {
  return (
    <section
      style={{
        ...cardStyle,
        marginBottom: 22,
        padding: 24,
      }}
    >
      <p
        style={{
          color: "#2f6f4e",
          fontSize: 12,
          fontWeight: 800,
          letterSpacing: "0.08em",
          margin: 0,
          textTransform: "uppercase",
        }}
      >
        How MeetIQ works
      </p>

      <h2 style={{ color: "#123326", margin: "10px 0 10px" }}>
        Upload a meeting recording. Get structured notes.
      </h2>

      <div
        style={{
          display: "grid",
          gap: 14,
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          marginTop: 18,
        }}
      >
        {[
          {
            title: "1. Upload",
            body: "Choose a clear meeting recording and add a short title.",
          },
          {
            title: "2. Process",
            body: "MeetIQ transcribes and prepares summary, decisions, risks, and action items.",
          },
          {
            title: "3. Review",
            body: "Check names, owners, deadlines, and decisions before sharing.",
          },
        ].map((step) => (
          <article
            key={step.title}
            style={{
              background: "#ffffff",
              border: "1px solid #d7eadf",
              borderRadius: 16,
              padding: 16,
            }}
          >
            <strong style={{ color: "#123326" }}>{step.title}</strong>
            <p style={{ color: "#5d6f66", lineHeight: 1.55, margin: "8px 0 0" }}>
              {step.body}
            </p>
          </article>
        ))}
      </div>

      <p style={{ color: "#5d6f66", lineHeight: 1.6, margin: "18px 0 0" }}>
        Best results come from real meetings with clear audio, limited background
        noise, and visible decision or action-item discussion. The free trial is
        designed for one meeting up to 30 minutes.
      </p>
    </section>
  );
}

export default function UploadPage() {
  const router = useRouter();

  const [authStatus, setAuthStatus] = useState<"checking" | "authenticated" | "unauthenticated" | "error">("checking");
  const [authError, setAuthError] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [confidentialMode, setConfidentialMode] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

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


  function getUploadFailureMessage(err: unknown): string {
    const status = typeof err === "object" && err !== null ? (err as any).status : undefined;
    const message = err instanceof Error ? err.message : "";

    if (message.includes("free-trial upload") || message.includes("Free trial")) {
      return message;
    }

    if (status === 400 || status === 413 || /unsupported file|file type|too large|30 minutes|duration/i.test(message)) {
      return message || "This recording could not be uploaded. Please check the file type, size, and duration.";
    }

    if (status === 402) {
      return message || "Your current plan limit has been reached.";
    }

    if (status === 503 || /queue|storage|network|fetch failed/i.test(message)) {
      return "MeetIQ could not start processing right now. Please try again in a few minutes.";
    }

    return "Upload failed. Please check your connection and try again. If it keeps happening, contact support with the file type and recording length.";
  }


  useEffect(() => {
    let active = true;

    async function verifyAuth() {
      try {
        await getCurrentUser();

        if (!active) {
          return;
        }

        setAuthError(null);
        setAuthStatus("authenticated");
      } catch (err) {
        if (!active) {
          return;
        }

        if (isAuthError(err)) {
          clearAuthToken();
          setAuthStatus("unauthenticated");
          router.replace("/login?next=/upload");
          return;
        }

        setAuthError("Unable to verify your login status. Please refresh or try again later.");
        setAuthStatus("error");
      }
    }

    verifyAuth();

    return () => {
      active = false;
    };
  }, [router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (authStatus !== "authenticated") {
      router.replace("/login?next=/upload");
      return;
    }

    if (!title.trim()) {
      setError("Please enter a meeting title.");
      return;
    }

    if (!file) {
      setError("Please choose an audio or video file.");
      return;
    }

    const fileError = validateUploadFile(file);
    if (fileError) {
      setError(fileError);
      return;
    }

    setIsUploading(true);

    try {
      const meeting = await createMeeting(title.trim());
      const upload = await uploadMeetingFile(meeting.id, file, confidentialMode);
      const jobQuery = upload.job_id ? `?jobId=${encodeURIComponent(upload.job_id)}` : "";

      router.push(`/meetings/${meeting.id}${jobQuery}`);
    } catch (err) {
      if (isAuthError(err)) {
        clearAuthToken();
        setAuthStatus("unauthenticated");
        router.replace("/login?next=/upload");
        return;
      }

      console.error(err);
      setError(getUploadFailureMessage(err));
    } finally {
      setIsUploading(false);
    }
  }

  if (authStatus === "checking") {
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
            Verifying your session before uploading...
          </p>
        </div>
      </div>
    );
  }

  if (authStatus === "unauthenticated") {
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
            Redirecting you to sign in...
          </p>
        </div>
      </div>
    );
  }

  if (authStatus === "error") {
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
              {authError ?? "Unable to verify your login status. Please refresh or try again later."}
            </p>
            <button
              type="button"
              onClick={() => router.refresh()}
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

  return (
    <div style={{ display: "grid", gap: 20 }}>
      <section style={{ ...cardStyle, padding: 28 }}>
        <h1
          style={{
            margin: 0,
            fontSize: "clamp(30px, 4vw, 38px)",
            lineHeight: 1.12,
            letterSpacing: "-0.04em",
            color: "#123326",
          }}
        >
          Turn recordings into decision-ready notes
        </h1>
        <p
          style={{
            margin: "14px 0 0",
            fontSize: 16,
            lineHeight: 1.45,
            color: "#416153",
          }}
        >
          Upload a meeting recording and get structured summaries, key points, and action items.
        </p>
      </section>

      <section style={{ ...cardStyle, padding: 26 }}>
        <form onSubmit={handleSubmit} style={{ display: "grid", gap: 18 }}>
          <div>
            <label htmlFor="title" style={labelStyle}>
              Meeting title
            </label>
            <input
              id="title"
              name="title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              style={inputStyle}
              placeholder="Client weekly sync"
              disabled={authStatus !== "authenticated"}
            />
          </div>

          <div>
            <label htmlFor="file" style={labelStyle}>
              Audio or video file
            </label>
            <input
              id="file"
              name="file"
              type="file"
              accept=".flac,.m4a,.mp3,.mp4,.mpeg,.mpga,.oga,.ogg,.wav,.webm,audio/flac,audio/mp4,audio/mpeg,audio/ogg,audio/wav,audio/webm,video/mp4,video/webm"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              style={inputStyle}
              disabled={authStatus !== "authenticated"}
            />
            <p style={{ margin: "12px 0 0", color: "#5f7b6b", fontSize: 16 }}>
              Upload an audio or video file to generate structured, decision-ready meeting notes.
            </p>

            <div
              style={{
                marginTop: 14,
                border: "1px solid #cfe6d4",
                background: "#eef7ef",
                borderRadius: 14,
                padding: 15,
                boxShadow: "0 4px 14px rgba(31, 90, 67, 0.08)",
              }}
            >
              <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
                <div
                  style={{
                    width: 30,
                    height: 30,
                    borderRadius: "50%",
                    background: "#fbfffb",
                    border: "1px solid #cfe6d4",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#2f6f4e",
                    fontWeight: 800,
                    flexShrink: 0,
                  }}
                >
                  i
                </div>
                <div>
                  <p style={{ margin: 0, fontWeight: 800, color: "#123326", fontSize: 16 }}>
                    Recommended upload format
                  </p>
                  <p style={{ margin: "5px 0 0", color: "#416153", lineHeight: 1.45 }}>
                    For best results, upload compressed meeting recordings under{" "}
                    <strong style={{ color: "#123326" }}>24 MB</strong>.
                  </p>
                  <p style={{ margin: "5px 0 0", color: "#416153", lineHeight: 1.45 }}>
                    Supported formats:{" "}
                    <strong style={{ color: "#123326" }}>
                      M4A, MP3, MP4, WAV, WEBM, OGG, FLAC, MPEG, MPGA, and OGA
                    </strong>.
                  </p>
                  <p style={{ margin: "5px 0 0", color: "#416153", lineHeight: 1.45 }}>
                    For longer meetings, <strong style={{ color: "#123326" }}>M4A or MP3</strong>{" "}
                    is recommended. Avoid AIFF/AIF and large uncompressed WAV files.
                  </p>
                </div>
              </div>
            </div>

            {file ? (
              <p
                style={{
                  margin: "12px 0 0",
                  color: "#123326",
                  fontSize: 16,
                  overflowWrap: "anywhere",
                }}
              >
                Selected file: <strong>{file.name}</strong>
              </p>
            ) : null}
          </div>

          <label
            htmlFor="confidential-mode"
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: 12,
              background: "#f0fdf4",
              border: "1px solid #bbf7d0",
              borderRadius: 16,
              padding: 16,
              color: "#123326",
              cursor:
                isUploading || authStatus !== "authenticated"
                  ? "not-allowed"
                  : "pointer",
              opacity: authStatus !== "authenticated" ? 0.7 : 1,
            }}
          >
            <input
              id="confidential-mode"
              type="checkbox"
              checked={confidentialMode}
              disabled={isUploading || authStatus !== "authenticated"}
              onChange={(event) => setConfidentialMode(event.target.checked)}
              style={{ marginTop: 4 }}
            />
            <span>
              <strong style={{ display: "block", marginBottom: 4 }}>
                Enable Confidential Mode
              </strong>
              <span style={{ color: "#365342", fontSize: 14, lineHeight: 1.55 }}>
                MeetIQ still uses hosted cloud processing. When enabled, the
                original recording is automatically deleted after notes are
                generated. Generated notes remain available in your account.
              </span>
            </span>
          </label>

          <button
            type="submit"
            disabled={isUploading || authStatus !== "authenticated"}
            style={{
              width: "100%",
              border: "none",
              borderRadius: 14,
              background: isUploading ? "#4f7f65" : "#2f6f4e",
              color: "#ffffff",
              padding: "14px 22px",
              fontSize: 16,
              fontWeight: 800,
              cursor: isUploading || authStatus !== "authenticated" ? "not-allowed" : "pointer",
              opacity: isUploading || authStatus !== "authenticated" ? 0.7 : 1,
            }}
          >
            {isUploading ? "Uploading..." : "Upload meeting"}
          </button>

          {authError ? (
            <div
              style={{
                border: "1px solid #f5c2c7",
                background: "#f8d7da",
                color: "#842029",
                borderRadius: 14,
                padding: "12px 14px",
                fontSize: 16,
              }}
            >
              {authError}
            </div>
          ) : null}

          {error ? (
            <div
              style={{
                border: "1px solid #fecaca",
                background: "#fef2f2",
                color: "#991b1b",
                borderRadius: 14,
                padding: "12px 14px",
                fontSize: 16,
              }}
            >
              {error}
            </div>
          ) : null}
        </form>
      </section>
    </div>
  );
}
