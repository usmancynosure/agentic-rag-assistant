"use client";

import { useState } from "react";
import { BrainIcon, PaperclipIcon, ResearchIcon, SendIcon, SparkIcon } from "./icons";

interface ComposerProps {
  onSubmit: (question: string) => void;
  disabled?: boolean;
  verify: boolean;
  onToggleVerify: (v: boolean) => void;
}

/** The large rounded glass chat-input card with action chips + send. */
export default function Composer({ onSubmit, disabled, verify, onToggleVerify }: ComposerProps) {
  const [value, setValue] = useState("");

  function submit() {
    const q = value.trim();
    if (!q || disabled) return;
    onSubmit(q);
    setValue("");
  }

  return (
    <div className="glass w-full rounded-4xl p-3 shadow-glass">
      <div className="flex items-center gap-2 rounded-3xl px-4 py-3">
        <SparkIcon className="h-5 w-5 shrink-0 text-primary" aria-hidden />
        <input
          aria-label="Message the assistant"
          className="w-full bg-transparent text-base text-ink placeholder:text-muted/70 focus:outline-none"
          placeholder="Ask about your documents, or anything on the web…"
          value={value}
          disabled={disabled}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
        />
      </div>

      <div className="flex items-center justify-between gap-2 px-2 pb-1 pt-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="chip" aria-hidden>
            <PaperclipIcon className="h-4 w-4" /> Attach File
          </span>
          <button
            type="button"
            className="chip"
            aria-pressed={verify}
            onClick={() => onToggleVerify(!verify)}
            title="Verify the answer against sources"
            style={verify ? { color: "#4F46E5", borderColor: "#c7d2fe" } : undefined}
          >
            <BrainIcon className="h-4 w-4" /> Verify {verify ? "on" : "off"}
          </button>
          <span className="chip" aria-hidden>
            <ResearchIcon className="h-4 w-4" /> Deep Research
          </span>
        </div>

        <button
          type="button"
          onClick={submit}
          disabled={disabled}
          aria-label="Send"
          className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-primary-700 text-white shadow-rail transition-opacity duration-200 hover:opacity-90 disabled:opacity-40 cursor-pointer"
        >
          <SendIcon className="h-5 w-5" aria-hidden />
        </button>
      </div>
    </div>
  );
}
