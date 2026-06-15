export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <p className="text-sm text-gray-500">Last updated: June 15, 2026</p>

      <h1 className="mt-3 text-3xl font-bold">Privacy Policy</h1>

      <p className="mt-6">
        MeetIQ helps users turn meeting recordings into structured notes,
        decisions, risks, and action items. This Privacy Policy explains what
        information may be collected, how it is used, and how users can request
        support or deletion.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Information we process</h2>
      <p className="mt-3">
        When you use MeetIQ, we may process account information, uploaded meeting
        recordings, generated notes, transcript text, file metadata, usage
        activity, and support requests.
      </p>

      <h2 className="mt-8 text-xl font-semibold">How we use information</h2>
      <p className="mt-3">
        We use this information to provide the service, process recordings,
        generate notes, troubleshoot issues, prevent abuse, improve reliability,
        and respond to support requests.
      </p>

      <h2 className="mt-8 text-xl font-semibold">AI processing</h2>
      <p className="mt-3">
        Uploaded recordings may be processed by transcription and AI systems to
        generate meeting notes. AI-generated outputs should be reviewed by the
        user before being relied on, shared, or used for decisions.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Storage and deletion</h2>
      <p className="mt-3">
        Meeting files and generated outputs may be stored so users can access,
        review, export, or delete their meetings. When a user deletes a meeting,
        MeetIQ is designed to remove the related meeting record and associated
        stored media from active storage. Temporary logs, backups, or provider
        retention systems may persist for a limited time.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Third-party providers</h2>
      <p className="mt-3">
        MeetIQ may use trusted service providers for hosting, storage,
        authentication, email, analytics, transcription, and AI processing. These
        providers are used only to operate and support the product.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Sensitive information</h2>
      <p className="mt-3">
        Do not upload recordings that contain highly sensitive, regulated, or
        legally restricted information unless you are authorized to do so and
        have confirmed that MeetIQ is appropriate for that use case.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Support and requests</h2>
      <p className="mt-3">
        For privacy, deletion, or support requests, contact the support email
        listed on the Support page.
      </p>
    </main>
  );
}
