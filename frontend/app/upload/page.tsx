"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { createMeeting, uploadMeetingFile } from "../../lib/api";

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

    setIsUploading(true);

    try {
      const meeting = await createMeeting(title.trim());

      await uploadMeetingFile(meeting.id, file);

      router.push(`/meetings/${meeting.id}`);
    } catch (err) {
      console.error(err);
      setError("Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-4xl font-bold tracking-tight text-slate-950">
          Turn meetings into clear notes
        </h1>
        <p className="mt-4 text-lg text-slate-600">
          Upload an audio or video file and get a summary, key points, and action items.
        </p>
      </section>

      <section className="mt-8 rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="title" className="block text-lg font-bold text-slate-950">
              Meeting title
            </label>
            <input
              id="title"
              name="title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              className="mt-3 w-full rounded-2xl border border-slate-300 px-4 py-4 text-lg text-slate-950"
              placeholder="Client weekly sync"
            />
          </div>

          <div>
            <label htmlFor="file" className="block text-lg font-bold text-slate-950">
              Audio or video file
            </label>
            <input
              id="file"
              name="file"
              type="file"
              accept="audio/*,video/*,.m4a,.mp3,.mp4,.wav,.webm,.ogg,.flac"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              className="mt-3 w-full rounded-2xl border border-slate-300 px-4 py-4 text-lg text-slate-950"
            />
            <p className="mt-3 text-slate-500">
              Upload an audio or video file to generate structured meeting notes.
            </p>
            {file ? (
              <p className="mt-2 text-slate-950">
                Selected file: <strong>{file.name}</strong>
              </p>
            ) : null}
          </div>

          <button
            type="submit"
            disabled={isUploading}
            className="w-full rounded-2xl bg-slate-950 px-6 py-4 text-lg font-bold text-white disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isUploading ? "Uploading..." : "Upload meeting"}
          </button>

          {error ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-red-800">
              {error}
            </div>
          ) : null}
        </form>
      </section>
    </main>
  );
}
