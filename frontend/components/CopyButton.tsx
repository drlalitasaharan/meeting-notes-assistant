"use client";

import { useState } from "react";
import { copyToClipboard } from "../lib/utils";

type CopyButtonProps = {
  text: string;
  label?: string;
};

export default function CopyButton({
  text,
  label = "Copy",
}: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await copyToClipboard(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      style={{
        background: "#ffffff",
        border: "1px solid #d1d5db",
        borderRadius: 8,
        padding: "8px 12px",
        cursor: "pointer",
        fontWeight: 600,
      }}
    >
      {copied ? "Copied" : label}
    </button>
  );
}
