
const SUPPORT_EMAIL = process.env.NEXT_PUBLIC_SUPPORT_EMAIL ?? "support@acjen.ai";

function buildMailto(subject: string, body: string): string {
  return `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(
    subject,
  )}&body=${encodeURIComponent(body)}`;
}

const generalSupportBody = [
  "Hi MeetIQ support,",
  "",
  "I need help with my MeetIQ account or meeting notes.",
  "",
  "Account email:",
  "Meeting title or Meeting ID, if relevant:",
  "Issue type: Upload / Processing / Notes quality / Usage limit / Billing / Other",
  "",
  "What happened:",
  "",
  "Expected result:",
  "",
  "Screenshot or extra context:",
  "",
  "Thanks.",
].join("\n");

const processingIssueBody = [
  "Hi MeetIQ support,",
  "",
  "A meeting recording did not process as expected.",
  "",
  "Account email:",
  "Meeting title:",
  "Meeting ID:",
  "Approximate recording length:",
  "File type:",
  "",
  "What happened:",
  "",
  "Any error message shown:",
  "",
  "Thanks.",
].join("\n");

const limitRequestBody = [
  "Hi MeetIQ support,",
  "",
  "I would like help with my MeetIQ upload limit or pilot access.",
  "",
  "Account email:",
  "Current plan or access type:",
  "Requested meeting volume:",
  "Typical recording length:",
  "",
  "Use case:",
  "",
  "Thanks.",
].join("\n");

const notesQualityBody = [
  "Hi MeetIQ support,",
  "",
  "I need help with the quality of generated meeting notes.",
  "",
  "Account email:",
  "Meeting title:",
  "Meeting ID:",
  "",
  "What looks incorrect or missing:",
  "",
  "Important names, owners, deadlines, or decisions to check:",
  "",
  "Thanks.",
].join("\n");

export default function SupportPage() {
  const generalMailto = buildMailto("MeetIQ support request", generalSupportBody);
  const processingMailto = buildMailto(
    "MeetIQ processing issue",
    processingIssueBody,
  );
  const limitMailto = buildMailto("MeetIQ upload limit request", limitRequestBody);
  const billingMailto = `mailto:${SUPPORT_EMAIL}?subject=MeetIQ%20billing%20support&body=Account%20email:%0A%0APayment%20or%20billing%20question:%0A%0APayPal%20payment%20date%20or%20order%20details,%20if%20available:%0A%0AWhat%20you%20need%20help%20with:%0A`;
const notesQualityMailto = buildMailto(
    "MeetIQ notes quality issue",
    notesQualityBody,
  );

  return (
    <>

      <main
        style={{
          background: "linear-gradient(180deg, #f7fbf8 0%, #ffffff 100%)",
          minHeight: "100vh",
          padding: "48px 20px 80px",
        }}
      >
        <div style={{ margin: "0 auto", maxWidth: 980 }}>
          <section
            style={{
              background: "#ffffff",
              border: "1px solid #d7eadf",
              borderRadius: 28,
              boxShadow: "0 18px 45px rgba(18, 51, 38, 0.08)",
              padding: "clamp(28px, 5vw, 48px)",
            }}
          >
            <p
              style={{
                color: "#2f6f4e",
                fontSize: 13,
                fontWeight: 800,
                letterSpacing: "0.08em",
                margin: 0,
                textTransform: "uppercase",
              }}
            >
              MeetIQ support
            </p>

            <h1
              style={{
                color: "#123326",
                fontSize: "clamp(34px, 6vw, 52px)",
                letterSpacing: "-0.04em",
                lineHeight: 1.05,
                margin: "12px 0 14px",
              }}
            >
              Need help with your meeting notes?
            </h1>

            <p
              style={{
                color: "#5d6f66",
                fontSize: 18,
                lineHeight: 1.65,
                margin: 0,
                maxWidth: 720,
              }}
            >
              Email support for upload issues, processing errors, usage limits, billing
              questions, or notes quality review. Please include your account email and
              meeting title or ID when possible.
            </p>

            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: 12,
                marginTop: 26,
              }}
            >
              <a
                href={generalMailto}
                style={{
                  background: "#2f6f4e",
                  borderRadius: 999,
                  color: "#ffffff",
                  display: "inline-flex",
                  fontWeight: 800,
                  padding: "13px 20px",
                  textDecoration: "none",
                }}
              >
                Email support
              </a>

              <a
                href={`mailto:${SUPPORT_EMAIL}`}
                style={{
                  border: "1px solid #b8d8c5",
                  borderRadius: 999,
                  color: "#123326",
                  display: "inline-flex",
                  fontWeight: 800,
                  padding: "13px 20px",
                  textDecoration: "none",
                }}
              >
                {SUPPORT_EMAIL}
              </a>
            </div>
          </section>

          <section
            style={{
              display: "grid",
              gap: 16,
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              marginTop: 22,
            }}
          >
            {[
              {
                title: "Upload or processing issue",
                body: "Use this when a file upload fails, processing gets stuck, or results do not appear.",
                href: processingMailto,
              },
              {
                title: "Usage limit or pilot access",
                body: "Use this to request a higher upload limit, pilot access, or account allowance review.",
                href: limitMailto,
              },
              {
                title: "Notes quality review",
                body: "Use this when names, owners, deadlines, decisions, or action items need review.",
                href: notesQualityMailto,
              },
              {
                title: "Billing support",
                body: "Use this for PayPal payment confirmation issues, manual invoice requests, cancellation requests, or refund questions during early access.",
                href: billingMailto,
              },
            ].map((item) => (
              <article
                key={item.title}
                style={{
                  background: "#ffffff",
                  border: "1px solid #d7eadf",
                  borderRadius: 22,
                  padding: 22,
                }}
              >
                <h2 style={{ color: "#123326", fontSize: 20, margin: "0 0 8px" }}>
                  {item.title}
                </h2>
                <p style={{ color: "#5d6f66", lineHeight: 1.6, margin: "0 0 16px" }}>
                  {item.body}
                </p>
                <a
                  href={item.href}
                  style={{
                    color: "#2f6f4e",
                    fontWeight: 800,
                    textDecoration: "none",
                  }}
                >
                  Start email →
                </a>
              </article>
            ))}
          </section>

          <section
            style={{
              background: "#f7fbf8",
              border: "1px solid #d7eadf",
              borderRadius: 22,
              color: "#365342",
              lineHeight: 1.7,
              marginTop: 22,
              padding: 22,
            }}
          >
            <h2 style={{ color: "#123326", marginTop: 0 }}>What to include</h2>
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              <li>Your account email.</li>
              <li>Meeting title or Meeting ID, if the issue is meeting-specific.</li>
              <li>What happened and what you expected instead.</li>
              <li>Screenshot or error text, if available.</li>
              <li>Avoid sharing sensitive meeting details unless needed for support.</li>
            </ul>
          </section>

          <section
            style={{
              background: "#fbfffb",
              border: "1px solid #d7eadf",
              borderRadius: 22,
              color: "#365342",
              lineHeight: 1.7,
              marginTop: 22,
              padding: 22,
            }}
          >
            <h2 style={{ color: "#123326", marginTop: 0 }}>
              Billing, cancellation, and refund questions
            </h2>
            <p style={{ marginTop: 0 }}>
              During early access, billing changes are handled manually by the
              MeetIQ team. Contact support if your PayPal payment completed but
              paid access is not active, if you need help with a manual invoice
              or payment request, or if you want to request cancellation of paid
              access.
            </p>
            <p style={{ marginBottom: 0 }}>
              Refund and cancellation requests are reviewed manually during
              early access. Please include your account email, payment date,
              and a short description of the issue. Do not send payment card,
              bank, or password details.
            </p>
          </section>

          <section
            style={{
              background: "#ffffff",
              border: "1px solid #d7eadf",
              borderRadius: 22,
              color: "#365342",
              lineHeight: 1.7,
              marginTop: 22,
              padding: 22,
            }}
          >
            <h2 style={{ color: "#123326", marginTop: 0 }}>What happens next</h2>
            <p style={{ marginTop: 0 }}>
              We review support requests using the account email, Meeting ID, visible
              error message, and admin processing status. For privacy, avoid sending
              full transcripts, confidential meeting details, or sensitive recordings
              unless we specifically ask for them.
            </p>
            <p style={{ marginBottom: 0 }}>
              If your meeting is stuck or failed, include the Meeting ID shown on the
              results page so we can check processing status, last error, and whether
              the job needs to be retried.
            </p>
          </section>

        </div>
      </main>
    </>
  );
}
