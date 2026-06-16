export default function DataRetentionPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <p className="text-sm text-gray-500">Last updated: June 15, 2026</p>

      <h1 className="mt-3 text-3xl font-bold">Deletion and Retention</h1>

      <p className="mt-6">
        This page explains how MeetIQ handles uploaded recordings, generated
        notes, and deletion requests.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Uploaded recordings</h2>
      <p className="mt-3">
        Uploaded meeting recordings may be stored while the meeting is being
        processed and while the meeting remains available in the user account.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Generated notes</h2>
      <p className="mt-3">
        Generated summaries, decisions, risks, action items, and transcript text
        may be stored so users can review, copy, export, or delete meeting
        outputs.
      </p>

      <h2 className="mt-8 text-xl font-semibold">User deletion</h2>
      <p className="mt-3">
        When a meeting is deleted, MeetIQ is designed to remove the meeting from
        the account view and delete associated active storage objects where
        supported by the current deployment.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Backups and logs</h2>
      <p className="mt-3">
        Some limited technical records may remain temporarily in logs, backups,
        or infrastructure provider systems for security, reliability, debugging,
        abuse prevention, and legal purposes. These records are not intended to
        be used as the active product copy of a deleted meeting.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Support troubleshooting</h2>
      <p className="mt-3">
        For support, MeetIQ may use operational metadata such as account email,
        Meeting ID, processing status, timestamps, and last error. Users should
        avoid sending full transcripts, confidential meeting content, or
        sensitive recordings unless needed for troubleshooting.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Account deletion requests</h2>
      <p className="mt-3">
        Users may request account or data deletion by contacting the support
        email listed on the Support page.
      </p>
    </main>
  );
}
