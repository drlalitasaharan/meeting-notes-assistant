export default function SupportedRecordingsPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <p className="text-sm text-gray-500">Last updated: June 15, 2026</p>

      <h1 className="mt-3 text-3xl font-bold">Supported Meeting Recordings</h1>

      <p className="mt-6">
        MeetIQ is designed for meeting recordings where people are discussing
        decisions, tasks, risks, updates, or next steps.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Best recording types</h2>
      <p className="mt-3">
        For best results, upload clear meeting recordings with minimal background
        noise, limited speaker overlap, and enough context for the AI to identify
        decisions and action items.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Current pilot limits</h2>
      <p className="mt-3">
        The free trial is designed for one meeting upload up to 30 minutes.
        Approved pilot users may have different limits.
      </p>

      <h2 className="mt-8 text-xl font-semibold">File formats</h2>
      <p className="mt-3">
        Use the file types shown on the upload page. Common meeting formats such
        as MP3, M4A, MP4, MOV, or WebM may be supported depending on the current
        deployment. WAV is not currently promised unless the upload page
        explicitly lists it as supported.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Not recommended</h2>
      <p className="mt-3">
        MeetIQ is not optimized for music, audiobooks, lectures without action
        items, private calls without consent, recordings with heavy background
        noise, or files that do not contain a real meeting.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Review required</h2>
      <p className="mt-3">
        Generated notes should be reviewed before sharing or using them as a
        final meeting record.
      </p>
    </main>
  );
}
