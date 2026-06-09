"use client";

import { useState } from "react";

import CopyButton from "./CopyButton";
import { downloadTextFile } from "../lib/utils";
import {
  cardHeaderStyle,
  cardStyle,
  eyebrowStyle,
  markdownPreStyle,
  mutedTextStyle,
  sectionTitleStyle,
} from "./ui";

type TranscriptCardProps = {
  markdown: string;
  filename: string;
};

export default function TranscriptCard({
  markdown,
  filename,
}: TranscriptCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <section style={cardStyle}>
      <div style={cardHeaderStyle}>
        <div>
          <p style={eyebrowStyle}>Export</p>
          <h2 style={sectionTitleStyle}>Markdown notes</h2>
          <p style={{ ...mutedTextStyle, marginTop: 8 }}>
            Preview, copy, or download your saved meeting notes.
          </p>
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <CopyButton text={markdown} />
          <button
            type="button"
            onClick={() => downloadTextFile(filename, markdown)}
            style={{
              background: "#ffffff",
              border: "1px solid #d1d5db",
              borderRadius: 10,
              padding: "10px 14px",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Download .md
          </button>
        </div>
      </div>

      <details
        onToggle={(event) =>
          setIsExpanded(event.currentTarget.open)
        }
      >
        <summary
          style={{
            cursor: "pointer",
            fontWeight: 600,
            color: "#111827",
            marginBottom: 16,
          }}
        >
          {isExpanded
              ? "Hide full markdown export"
              : "Show full markdown export"}
        </summary>

        <pre style={markdownPreStyle}>{markdown}</pre>
      </details>
    </section>
  );
}
