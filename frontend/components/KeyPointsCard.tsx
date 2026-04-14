import CopyButton from "./CopyButton";
import {
  cardHeaderStyle,
  cardStyle,
  eyebrowStyle,
  mutedTextStyle,
  neutralPillStyle,
  sectionTitleStyle,
} from "./ui";

type KeyPointsCardProps = {
  items: string[];
};

export default function KeyPointsCard({ items }: KeyPointsCardProps) {
  const text = items.join("\n");

  return (
    <section style={cardStyle}>
      <div style={cardHeaderStyle}>
        <div>
          <p style={eyebrowStyle}>Highlights</p>
          <h2 style={sectionTitleStyle}>Key points</h2>
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <span style={neutralPillStyle}>{items.length} items</span>
          <CopyButton text={text} />
        </div>
      </div>

      {items.length > 0 ? (
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
            <li key={`${index}-${item.slice(0, 24)}`} style={{ paddingLeft: 2 }}>
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p style={mutedTextStyle}>No key points available.</p>
      )}
    </section>
  );
}
