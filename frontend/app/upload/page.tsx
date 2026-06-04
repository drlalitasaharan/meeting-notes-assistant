"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { createMeeting, uploadMeetingFile } from "../../lib/api";

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
  background: "#ffffff",
  border: "1px solid #e5e7eb",
  borderRadius: 24,
  boxShadow: "0 2px 8px rgba(15, 23, 42, 0.06)",
};

const inputStyle = {
  width: "100%",
  border: "1px solid #cbd5e1",
  borderRadius: 14,
  padding: "14px 16px",
  fontSize: 18,
  color: "#0f172a",
  boxSizing: "border-box" as const,
};

const labelStyle = {
  display: "block",
  marginBottom: 10,
  fontSize: 18,
  fontWeight: 800,
  color: "#0f172a",
};

export default function UploadPage() {
  const router = useRouter();

  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

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

      const upload = await uploadMeetingFile(meeting.id, file);
      const jobQuery = upload.job_id ? `?jobId=${encodeURIComponent(upload.job_id)}` : "";

      router.push(`/meetings/${meeting.id}${jobQuery}`);
    } catch (err) {
      console.error(err);
      setError("Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 28 }}>
      <section style={{ ...cardStyle, padding: 36 }}>
        <h1
          style={{
            margin: 0,
            fontSize: 44,
            lineHeight: 1.1,
            letterSpacing: "-0.04em",
            color: "#0f172a",
          }}
        >
          Turn recordings into decision-ready notes
        </h1>
        <p
          style={{
            margin: "18px 0 0",
            fontSize: 20,
            lineHeight: 1.6,
            color: "#475569",
          }}
        >
          Upload a meeting recording and get structured summaries, key points, and action items.
        </p>
      </section>

      <section style={{ ...cardStyle, padding: 32 }}>
        <form onSubmit={handleSubmit} style={{ display: "grid", gap: 24 }}>
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
            />
            <p style={{ margin: "12px 0 0", color: "#64748b", fontSize: 16 }}>
              Upload an audio or video file to generate structured, decision-ready meeting notes.
            </p>

            <div
              style={{
                marginTop: 16,
                border: "1px solid #e2e8f0",
                background: "#f8fafc",
                borderRadius: 18,
                padding: 18,
                boxShadow: "0 1px 3px rgba(15, 23, 42, 0.04)",
              }}
            >
              <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
                <div
                  style={{
                    width: 34,
                    height: 34,
                    borderRadius: "50%",
                    background: "#ffffff",
                    border: "1px solid #e2e8f0",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#334155",
                    fontWeight: 800,
                    flexShrink: 0,
                  }}
                >
                  i
                </div>
                <div>
                  <p style={{ margin: 0, fontWeight: 800, color: "#0f172a", fontSize: 16 }}>
                    Recommended upload format
                  </p>
                  <p style={{ margin: "8px 0 0", color: "#475569", lineHeight: 1.6 }}>
                    For best results, upload compressed meeting recordings under{" "}
                    <strong style={{ color: "#0f172a" }}>24 MB</strong>.
                  </p>
                  <p style={{ margin: "6px 0 0", color: "#475569", lineHeight: 1.6 }}>
                    Supported formats:{" "}
                    <strong style={{ color: "#0f172a" }}>
                      M4A, MP3, MP4, WAV, WEBM, OGG, FLAC, MPEG, MPGA, and OGA
                    </strong>.
                  </p>
                  <p style={{ margin: "6px 0 0", color: "#475569", lineHeight: 1.6 }}>
                    For longer meetings, <strong style={{ color: "#0f172a" }}>M4A or MP3</strong>{" "}
                    is recommended. Avoid AIFF/AIF and large uncompressed WAV files.
                  </p>
                </div>
              </div>
            </div>

            {file ? (
              <p style={{ margin: "12px 0 0", color: "#0f172a", fontSize: 16 }}>
                Selected file: <strong>{file.name}</strong>
              </p>
            ) : null}
          </div>

          <button
            type="submit"
            disabled={isUploading}
            style={{
              width: "100%",
              border: "none",
              borderRadius: 16,
              background: isUploading ? "#334155" : "#0f172a",
              color: "#ffffff",
              padding: "16px 24px",
              fontSize: 20,
              fontWeight: 800,
              cursor: isUploading ? "not-allowed" : "pointer",
              opacity: isUploading ? 0.7 : 1,
            }}
          >
            {isUploading ? "Uploading..." : "Upload meeting"}
          </button>

          {error ? (
            <div
              style={{
                border: "1px solid #fecaca",
                background: "#fef2f2",
                color: "#991b1b",
                borderRadius: 16,
                padding: "14px 16px",
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
