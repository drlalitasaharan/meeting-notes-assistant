import type { CSSProperties } from "react";

export const cardStyle: CSSProperties = {
  background: "#ffffff",
  border: "1px solid #e5e7eb",
  borderRadius: 20,
  padding: 24,
  boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
};

export const cardHeaderStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  gap: 12,
  marginBottom: 16,
  flexWrap: "wrap",
};

export const eyebrowStyle: CSSProperties = {
  margin: 0,
  color: "#6b7280",
  fontSize: 12,
  fontWeight: 700,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
};

export const sectionTitleStyle: CSSProperties = {
  margin: "6px 0 0",
  fontSize: 24,
  lineHeight: 1.2,
  color: "#111827",
};

export const bodyTextStyle: CSSProperties = {
  margin: 0,
  color: "#374151",
  fontSize: 16,
  lineHeight: 1.8,
};

export const mutedTextStyle: CSSProperties = {
  margin: 0,
  color: "#6b7280",
  fontSize: 14,
  lineHeight: 1.6,
};

export const pillRowStyle: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 8,
};

export const neutralPillStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  borderRadius: 999,
  padding: "6px 10px",
  fontSize: 12,
  fontWeight: 700,
  background: "#f3f4f6",
  color: "#374151",
  border: "1px solid #e5e7eb",
};

export const nestedPanelStyle: CSSProperties = {
  background: "#f9fafb",
  border: "1px solid #e5e7eb",
  borderRadius: 16,
  padding: 16,
};

export const markdownPreStyle: CSSProperties = {
  margin: 0,
  whiteSpace: "pre-wrap",
  wordBreak: "break-word",
  background: "#f9fafb",
  border: "1px solid #e5e7eb",
  borderRadius: 16,
  padding: 18,
  color: "#374151",
  lineHeight: 1.7,
  overflowX: "auto",
  fontSize: 14,
};

export function getStatusBadgeStyle(status: string): CSSProperties {
  const normalized = status.toLowerCase();

  if (normalized === "succeeded") {
    return {
      display: "inline-flex",
      alignItems: "center",
      borderRadius: 999,
      padding: "8px 12px",
      fontSize: 13,
      fontWeight: 700,
      background: "#ecfdf5",
      color: "#065f46",
      border: "1px solid #a7f3d0",
    };
  }

  if (normalized === "failed") {
    return {
      display: "inline-flex",
      alignItems: "center",
      borderRadius: 999,
      padding: "8px 12px",
      fontSize: 13,
      fontWeight: 700,
      background: "#fef2f2",
      color: "#991b1b",
      border: "1px solid #fecaca",
    };
  }

  if (normalized === "running") {
    return {
      display: "inline-flex",
      alignItems: "center",
      borderRadius: 999,
      padding: "8px 12px",
      fontSize: 13,
      fontWeight: 700,
      background: "#eff6ff",
      color: "#1d4ed8",
      border: "1px solid #bfdbfe",
    };
  }

  return {
    display: "inline-flex",
    alignItems: "center",
    borderRadius: 999,
    padding: "8px 12px",
    fontSize: 13,
    fontWeight: 700,
    background: "#fffbeb",
    color: "#92400e",
    border: "1px solid #fde68a",
  };
}
