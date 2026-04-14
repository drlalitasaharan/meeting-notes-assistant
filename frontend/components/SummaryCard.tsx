import CopyButton from "./CopyButton";
import {
  bodyTextStyle,
  cardHeaderStyle,
  cardStyle,
  eyebrowStyle,
  sectionTitleStyle,
} from "./ui";

type SummaryCardProps = {
  summary: string;
};

export default function SummaryCard({ summary }: SummaryCardProps) {
  return (
    <section style={cardStyle}>
      <div style={cardHeaderStyle}>
        <div>
          <p style={eyebrowStyle}>Overview</p>
          <h2 style={sectionTitleStyle}>Summary</h2>
        </div>
        <CopyButton text={summary} />
      </div>

      <p style={{ ...bodyTextStyle, fontSize: 17 }}>{summary}</p>
    </section>
  );
}
