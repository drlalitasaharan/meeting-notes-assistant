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
  return (
    <section style={cardStyle}>
      <div style={cardHeaderStyle}>
        <div>
          <p style={eyebrowStyle}>Export</p>
          <h2 style={sectionTitleStyle}>Markdown notes</h2>
          <p style={{ ...mutedTextStyle, marginTop: 8 }}>
            Keep this collapsed by default so the primary UI stays focused on summary and actions.
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

      <details>
        <summary
          style={{
            cursor: "pointer",
            fontWeight: 600,
            color: "#111827",
            marginBottom: 16,
          }}
        >
          Show full markdown export
        </summary>

        <pre style={markdownPreStyle}>{markdown}</pre>
      </details>
    </section>
  );
}
