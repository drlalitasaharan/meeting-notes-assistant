"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createMeeting, uploadMeetingFile } from "../lib/api";
import ErrorBanner from "./ErrorBanner";

export default function UploadForm() {
  const router = useRouter();

  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!file) {
      setError("Please choose an audio or video file.");
      return;
    }

    setIsSubmitting(true);
    setError("");

    try {
      const finalTitle = title.trim() || file.name;

      const meeting = await createMeeting(finalTitle);
      const uploadResponse = await uploadMeetingFile(meeting.id, file);

      const jobId = uploadResponse.job_id ?? uploadResponse.id;

      if (!jobId) {
        throw new Error("Upload succeeded, but no job ID was returned.");
      }

      router.push(`/meetings/${meeting.id}?jobId=${jobId}`);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Something went wrong during upload.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        background: "#ffffff",
        border: "1px solid #e5e7eb",
        borderRadius: 16,
        padding: 20,
        boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
      }}
    >
      <div style={{ display: "grid", gap: 16 }}>
        <div>
          <label
            htmlFor="meeting-title"
            style={{
              display: "block",
              fontWeight: 600,
              marginBottom: 8,
            }}
          >
            Meeting title
          </label>
          <input
            id="meeting-title"
            type="text"
            placeholder="Weekly team sync"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            style={{
              width: "100%",
              padding: "12px 14px",
              borderRadius: 10,
              border: "1px solid #d1d5db",
              outline: "none",
            }}
          />
        </div>

        <div>
          <label
            htmlFor="meeting-file"
            style={{
              display: "block",
              fontWeight: 600,
              marginBottom: 8,
            }}
          >
            Audio or video file
          </label>
          <input
            id="meeting-file"
            type="file"
            accept="audio/*,video/*"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            style={{
              width: "100%",
              padding: "12px 14px",
              borderRadius: 10,
              border: "1px solid #d1d5db",
              background: "#ffffff",
            }}
          />
          <p style={{ marginTop: 8, marginBottom: 0, color: "#6b7280", fontSize: 14 }}>
            Upload an audio or video file to generate structured meeting notes.
          </p>
          {file ? (
            <p style={{ marginTop: 8, marginBottom: 0, color: "#111827", fontSize: 14 }}>
              Selected file: <strong>{file.name}</strong>
            </p>
          ) : null}
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          style={{
            background: isSubmitting ? "#9ca3af" : "#111827",
            color: "#ffffff",
            border: "none",
            borderRadius: 10,
            padding: "12px 16px",
            fontWeight: 600,
            cursor: isSubmitting ? "not-allowed" : "pointer",
          }}
        >
          {isSubmitting ? "Uploading..." : "Upload meeting"}
        </button>
      </div>

      {error ? <ErrorBanner message={error} /> : null}
    </form>
  );
}
