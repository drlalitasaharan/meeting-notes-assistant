"use client";

import { useState } from "react";
import CopyButton from "./CopyButton";
import {
  cardHeaderStyle,
  cardStyle,
  editorStyle,
  eyebrowStyle,
  inlineErrorStyle,
  mutedTextStyle,
  neutralPillStyle,
  primaryButtonStyle,
  secondaryButtonStyle,
  sectionTitleStyle,
} from "./ui";

type KeyPointsCardProps = {
  items: string[];
  onSave: (items: string[]) => Promise<void>;
};

export default function KeyPointsCard({
  items,
  onSave,
}: KeyPointsCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(items.join("\n"));
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState("");

  const text = items.join("\n");

  function startEditing() {
    setDraft(items.join("\n"));
    setSaveError("");
    setIsEditing(true);
  }

  function cancelEditing() {
    setDraft(items.join("\n"));
    setSaveError("");
    setIsEditing(false);
  }

  async function saveItems() {
    const updatedItems = draft
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean);

    try {
      setIsSaving(true);
      setSaveError("");
      await onSave(updatedItems);
      setIsEditing(false);
    } catch (error) {
      setSaveError(
        error instanceof Error
          ? error.message
          : "Could not save the key points.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section style={cardStyle}>
      <div style={cardHeaderStyle}>
        <div>
          <p style={eyebrowStyle}>Highlights</p>
          <h2 style={sectionTitleStyle}>Key points</h2>
        </div>

        <div
          style={{
            display: "flex",
            gap: 8,
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <span style={neutralPillStyle}>{items.length} items</span>

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
                onClick={saveItems}
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
              <CopyButton text={text} />
            </>
          )}
        </div>
      </div>

      {isEditing ? (
        <>
          <textarea
            aria-label="Edit key points"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Enter one key point per line"
            style={editorStyle}
          />
          <p style={{ ...mutedTextStyle, marginTop: 8 }}>
            Enter one key point per line.
          </p>
        </>
      ) : items.length > 0 ? (
        <ul
          style={{
            margin: 0,
            paddingLeft: 22,
            color: "#374151",
            lineHeight: 1.8,
            display: "grid",
            gap: 12,
          }}
        >
          {items.map((item, index) => (
            <li
              key={`${index}-${item.slice(0, 24)}`}
              style={{ paddingLeft: 2 }}
            >
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p style={mutedTextStyle}>No key points available.</p>
      )}

      {saveError ? <p style={inlineErrorStyle}>{saveError}</p> : null}
    </section>
  );
}
