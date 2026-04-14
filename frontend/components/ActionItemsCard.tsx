import CopyButton from "./CopyButton";
import { parseActionItem } from "../lib/notes";
import {
  bodyTextStyle,
  cardHeaderStyle,
  cardStyle,
  eyebrowStyle,
  mutedTextStyle,
  neutralPillStyle,
  sectionTitleStyle,
} from "./ui";

type ActionItemsCardProps = {
  items: string[];
};

export default function ActionItemsCard({ items }: ActionItemsCardProps) {
  const parsedItems = items.map(parseActionItem);
  const text = items.join("\n");

  return (
    <section style={cardStyle}>
      <div style={cardHeaderStyle}>
        <div>
          <p style={eyebrowStyle}>Execution</p>
          <h2 style={sectionTitleStyle}>Action items</h2>
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <span style={neutralPillStyle}>{items.length} items</span>
          <CopyButton text={text} />
        </div>
      </div>

      {parsedItems.length > 0 ? (
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
                  {item.owner ? `Owner: ${item.owner}` : "Owner: Unassigned"}
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
        <p style={mutedTextStyle}>No clear action items detected.</p>
      )}
    </section>
  );
}
