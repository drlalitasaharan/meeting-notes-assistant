"use client";

import { useState } from "react";
import CopyButton from "./CopyButton";
import { parseActionItem } from "../lib/notes";
import {
  bodyTextStyle,
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
  successTextStyle,
} from "./ui";

type ActionItemsCardProps = {
  items: string[];
  onSave: (items: string[]) => Promise<void>;
};

export default function ActionItemsCard({
  items,
  onSave,
}: ActionItemsCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(items.join("\n"));
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");

  const parsedItems = items.map(parseActionItem);
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
      setSaveMessage("");
      await onSave(updatedItems);
      setIsEditing(false);
      setSaveMessage("Changes saved");
      window.setTimeout(() => setSaveMessage(""), 2500);
    } catch (error) {
      setSaveError(
        error instanceof Error
          ? error.message
          : "Could not save the action items.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section style={cardStyle}>
      <div style={cardHeaderStyle}>
        <div>
          <p style={eyebrowStyle}>Execution</p>
          <h2 style={sectionTitleStyle}>Action items</h2>
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
            aria-label="Edit action items"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Priya — Update the proposal (due: tomorrow)"
            style={editorStyle}
          />
          <p style={{ ...mutedTextStyle, marginTop: 8 }}>
            Enter one action item per line. Use “Owner — Task” to retain
            owner display.
          </p>
        </>
      ) : parsedItems.length > 0 ? (
        <div style={{ display: "grid", gap: 12 }}>
          {parsedItems.map((item, index) => (
            <div
              key={`${index}-${item.raw.slice(0, 24)}`}
              style={{
                background: "#f9fafb",
                border: "1px solid #e5e7eb",
                borderRadius: 16,
                padding: 16,
              }}
            >
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 8,
                  marginBottom: 10,
                }}
              >
                <span style={neutralPillStyle}>
                  {item.owner
                    ? `Owner: ${item.owner}`
                    : "Owner: Unassigned"}
                </span>

                {item.due ? (
                  <span
                    style={{
                      ...neutralPillStyle,
                      background: "#eff6ff",
                      color: "#1d4ed8",
                      border: "1px solid #bfdbfe",
                    }}
                  >
                    Due: {item.due}
                  </span>
                ) : null}
              </div>

              <p style={bodyTextStyle}>{item.task}</p>
            </div>
          ))}
        </div>
      ) : (
        <p style={mutedTextStyle}>
          No clear action items detected.
        </p>
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
