"use client";

import { FormEvent, useState } from "react";

import { submitMeetingFeedback } from "../lib/api";
import type {
  FeedbackMeetingType,
  FeedbackMostUseful,
  FeedbackUsefulness,
  FeedbackWouldUseAgain,
} from "../lib/types";

type Option<T extends string> = {
  label: string;
  value: T;
};

const usefulnessOptions: Option<FeedbackUsefulness>[] = [
  { label: "Yes", value: "yes" },
  { label: "Somewhat", value: "somewhat" },
  { label: "No", value: "no" },
];

const mostUsefulOptions: Option<FeedbackMostUseful>[] = [
  { label: "Summary", value: "summary" },
  { label: "Decisions", value: "decisions" },
  { label: "Action items", value: "action_items" },
  { label: "Risks", value: "risks" },
  { label: "Nothing yet", value: "nothing_yet" },
];

const wouldUseAgainOptions: Option<FeedbackWouldUseAgain>[] = [
  { label: "Yes", value: "yes" },
  { label: "Maybe", value: "maybe" },
  { label: "No", value: "no" },
];

const meetingTypeOptions: Option<FeedbackMeetingType>[] = [
  { label: "Internal", value: "internal" },
  { label: "Client", value: "client" },
  { label: "Sales", value: "sales" },
  { label: "Research", value: "research" },
  { label: "Project", value: "project" },
  { label: "Other", value: "other" },
];

function OptionGroup<T extends string>({
  legend,
  name,
  options,
  value,
  onChange,
}: {
  legend: string;
  name: string;
  options: Option<T>[];
  value: T;
  onChange: (value: T) => void;
}) {
  return (
    <fieldset
      style={{
        border: "none",
        display: "grid",
        gap: 10,
        margin: 0,
        padding: 0,
      }}
    >
      <legend style={{ color: "#123326", fontWeight: 800, marginBottom: 2 }}>
        {legend}
      </legend>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
        {options.map((option) => {
          const selected = value === option.value;
          return (
            <label
              key={option.value}
              style={{
                alignItems: "center",
                background: selected ? "#e7f7ed" : "#ffffff",
                border: selected ? "1px solid #2f6f4e" : "1px solid #b8d8c5",
                borderRadius: 999,
                color: selected ? "#123326" : "#365342",
                cursor: "pointer",
                display: "inline-flex",
                fontWeight: 800,
                gap: 8,
                padding: "9px 12px",
              }}
            >
              <input
                checked={selected}
                name={name}
                onChange={() => onChange(option.value)}
                style={{ margin: 0 }}
                type="radio"
                value={option.value}
              />
              {option.label}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

export default function MeetingFeedbackForm({ meetingId }: { meetingId: number }) {
  const [usefulness, setUsefulness] = useState<FeedbackUsefulness>("yes");
  const [mostUseful, setMostUseful] = useState<FeedbackMostUseful>("summary");
  const [improvementText, setImprovementText] = useState("");
  const [wouldUseAgain, setWouldUseAgain] = useState<FeedbackWouldUseAgain>("yes");
  const [meetingType, setMeetingType] = useState<FeedbackMeetingType>("internal");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<"idle" | "success" | "error">("idle");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setSubmitStatus("idle");

    try {
      await submitMeetingFeedback({
        meeting_id: meetingId,
        usefulness,
        most_useful: mostUseful,
        improvement_text: improvementText.trim() || null,
        would_use_again: wouldUseAgain,
        meeting_type: meetingType,
      });
      setSubmitStatus("success");
    } catch {
      setSubmitStatus("error");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section
      style={{
        background: "#ffffff",
        border: "1px solid #d7eadf",
        borderRadius: 20,
        boxShadow: "0 10px 28px rgba(31, 90, 67, 0.08)",
        padding: "clamp(20px, 4vw, 28px)",
      }}
    >
      <h2 style={{ color: "#123326", margin: "0 0 8px" }}>Was this useful?</h2>
      <p style={{ color: "#5d6f66", lineHeight: 1.6, margin: "0 0 20px" }}>
        MeetIQ is in early access. Your feedback helps improve meeting summaries,
        decisions, risks, and action items.
      </p>

      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 20 }}>
        <OptionGroup
          legend="Was the output useful?"
          name="usefulness"
          options={usefulnessOptions}
          value={usefulness}
          onChange={(value) => setUsefulness(value)}
        />

        <OptionGroup
          legend="What was most useful?"
          name="most-useful"
          options={mostUsefulOptions}
          value={mostUseful}
          onChange={(value) => setMostUseful(value)}
        />

        <label style={{ color: "#123326", display: "grid", fontWeight: 800, gap: 8 }}>
          What needs improvement?
          <textarea
            value={improvementText}
            onChange={(event) => setImprovementText(event.target.value)}
            rows={4}
            style={{
              border: "1px solid #b8d8c5",
              borderRadius: 14,
              color: "#123326",
              lineHeight: 1.5,
              minHeight: 110,
              padding: "12px 14px",
              resize: "vertical",
              width: "100%",
            }}
          />
        </label>

        <OptionGroup
          legend="Would you use this again for a real meeting?"
          name="would-use-again"
          options={wouldUseAgainOptions}
          value={wouldUseAgain}
          onChange={(value) => setWouldUseAgain(value)}
        />

        <OptionGroup
          legend="What type of meeting was this?"
          name="meeting-type"
          options={meetingTypeOptions}
          value={meetingType}
          onChange={(value) => setMeetingType(value)}
        />

        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center" }}>
          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              background: isSubmitting ? "#8fb7a1" : "#2f6f4e",
              border: "none",
              borderRadius: 999,
              color: "#ffffff",
              cursor: isSubmitting ? "not-allowed" : "pointer",
              display: "inline-flex",
              fontWeight: 800,
              justifyContent: "center",
              padding: "12px 18px",
            }}
          >
            {isSubmitting ? "Submitting..." : "Submit feedback"}
          </button>

          {submitStatus === "success" ? (
            <p style={{ color: "#14532d", fontWeight: 800, margin: 0 }}>
              Thank you — this helps improve MeetIQ.
            </p>
          ) : null}

          {submitStatus === "error" ? (
            <p style={{ color: "#991b1b", fontWeight: 800, margin: 0 }}>
              We could not save your feedback. Please try again.
            </p>
          ) : null}
        </div>
      </form>
    </section>
  );
}
