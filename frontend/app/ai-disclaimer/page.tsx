export default function AiDisclaimerPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <p className="text-sm text-gray-500">Last updated: June 15, 2026</p>

      <h1 className="mt-3 text-3xl font-bold">AI Disclaimer</h1>

      <p className="mt-6">
        MeetIQ uses AI to help convert meeting recordings into structured notes.
        The product is designed to save time, but AI-generated content should
        always be reviewed by a person.
      </p>

      <h2 className="mt-8 text-xl font-semibold">AI may make mistakes</h2>
      <p className="mt-3">
        Generated notes may miss details, misunderstand speakers, merge separate
        topics, or phrase decisions and action items imperfectly. Audio quality,
        speaker overlap, accents, background noise, and meeting length can affect
        results.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Review before use</h2>
      <p className="mt-3">
        Users should review, edit, and verify notes before sharing them,
        assigning work, making decisions, or using them as an official record.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Not a source of truth</h2>
      <p className="mt-3">
        MeetIQ helps prepare a draft record of a meeting. The final source of
        truth remains the actual meeting, the participants, and any approved
        official documentation.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Sensitive meetings</h2>
      <p className="mt-3">
        Do not use MeetIQ for highly sensitive, regulated, confidential, or
        legally restricted meetings unless you have confirmed that the product is
        appropriate for that use case.
      </p>
    </main>
  );
}
