"use client";

import { useState } from "react";
import CopyButton from "./CopyButton";
import {
  bodyTextStyle,
  cardHeaderStyle,
  cardStyle,
  editorStyle,
  eyebrowStyle,
  inlineErrorStyle,
  primaryButtonStyle,
  secondaryButtonStyle,
  sectionTitleStyle,
  successTextStyle,
} from "./ui";

type SummaryCardProps = {
  summary: string;
  onSave: (summary: string) => Promise<void>;
};

export default function SummaryCard({
  summary,
  onSave,
}: SummaryCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(summary);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");

  function startEditing() {
    setDraft(summary);
    setSaveError("");
    setIsEditing(true);
  }

  function cancelEditing() {
    setDraft(summary);
    setSaveError("");
    setIsEditing(false);
  }

  async function saveSummary() {
    const cleaned = draft.trim();

    if (!cleaned) {
      setSaveError("Summary cannot be empty.");
      return;
    }

    try {
      setIsSaving(true);
      setSaveError("");
      setSaveMessage("");
      await onSave(cleaned);
      setIsEditing(false);
      setSaveMessage("Changes saved");
      window.setTimeout(() => setSaveMessage(""), 2500);
    } catch (error) {
      setSaveError(
        error instanceof Error
          ? error.message
          : "Could not save the summary.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section style={cardStyle}>
      <div style={cardHeaderStyle}>
        <div>
          <p style={eyebrowStyle}>Overview</p>
          <h2 style={sectionTitleStyle}>Summary</h2>
        </div>

        <div
          style={{
            display: "flex",
            gap: 8,
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          {isEditing ? (
            <>
              <button
                type="button"
                onClick={cancelEditing}
                disabled={isSaving}
                style={{
                  ...secondaryButtonStyle,
                  opacity: isSaving ? 0.6 : 1,
                }}
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={saveSummary}
                disabled={isSaving}
                style={{
                  ...primaryButtonStyle,
                  opacity: isSaving ? 0.6 : 1,
                }}
              >
                {isSaving ? "Saving..." : "Save"}
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={startEditing}
                style={secondaryButtonStyle}
              >
                Edit
              </button>
              <CopyButton text={summary} />
            </>
          )}
        </div>
      </div>

      {isEditing ? (
        <textarea
          aria-label="Edit summary"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          style={editorStyle}
        />
      ) : (
        <p style={{ ...bodyTextStyle, fontSize: 17 }}>{summary}</p>
      )}

      {saveError ? <p style={inlineErrorStyle}>{saveError}</p> : null}
      {saveMessage ? (
        <p role="status" aria-live="polite" style={successTextStyle}>
          ✓ {saveMessage}
        </p>
      ) : null}
    </section>
  );
}
