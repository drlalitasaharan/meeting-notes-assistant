export type ParsedActionItem = {
  raw: string;
  owner: string | null;
  task: string;
  due: string | null;
};

function cleanText(value: string): string {
  return value
    .replace(/\s+/g, " ")
    .replace(/\s+\)/g, ")")
    .trim();
}

export function parseActionItem(item: string): ParsedActionItem {
  const raw = item.trim();

  let due: string | null = null;
  const dueMatch = raw.match(/\(due:\s*([^)]+)\)/i);
  if (dueMatch?.[1]) {
    due = cleanText(dueMatch[1]);
  }

  let withoutDue = raw.replace(/\(due:\s*([^)]+)\)/gi, "").trim();
  withoutDue = withoutDue.replace(/\s{2,}/g, " ").trim();

  let owner: string | null = null;
  let task = withoutDue;

  const ownerSplit = withoutDue.match(/^([^–—-]{1,40})\s*[–—-]\s*(.+)$/);
  if (ownerSplit) {
    owner = cleanText(ownerSplit[1]);
    task = cleanText(ownerSplit[2]);
  }

  task = task.replace(/^[•*-]\s*/, "").trim();

  return {
    raw,
    owner: owner || null,
    task: task || raw,
    due,
  };
}
