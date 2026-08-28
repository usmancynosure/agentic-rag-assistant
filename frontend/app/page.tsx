"use client";

import { useState } from "react";
import Composer from "@/components/Composer";
import Sidebar from "@/components/Sidebar";
import { BotIcon, FileIcon, ResearchIcon, SparkIcon } from "@/components/icons";

const CATEGORIES = [
  { label: "Documents", icon: FileIcon },
  { label: "Research", icon: ResearchIcon },
  { label: "Summarize", icon: SparkIcon },
  { label: "Compare", icon: BotIcon },
];

export default function Page() {
  const [verify, setVerify] = useState(true);

  return (
    <main className="mx-auto flex min-h-screen max-w-[1400px] gap-3 p-4">
      <div className="glass-soft sticky top-4 hidden h-[calc(100vh-2rem)] rounded-4xl px-2 md:flex">
        <Sidebar />
      </div>

      <section className="flex flex-1 flex-col">
        <header className="flex items-center justify-between px-2 py-3">
          <div className="glass flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-semibold">
            <BotIcon className="h-5 w-5 text-primary" aria-hidden />
            Agentic RAG · Opus 4.8
          </div>
          <h1 className="hidden font-display text-lg text-ink sm:block">Knowledge Assistant</h1>
          <a
            href="https://github.com/usmancynosure/agentic-rag-assistant"
            className="rounded-2xl bg-ink px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90"
          >
            GitHub
          </a>
        </header>

        <div className="flex flex-1 flex-col items-center justify-center px-4">
          <div className="animate-fade-up text-center">
            <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-3xl bg-gradient-to-br from-primary to-secondary text-white shadow-rail">
              <BotIcon className="h-9 w-9" aria-hidden />
            </div>
            <h2 className="font-display text-4xl leading-tight text-ink sm:text-5xl">
              Ask. <span className="text-primary">Verify.</span> Cite.
            </h2>
            <p className="mx-auto mt-3 max-w-xl text-base text-muted">
              Search your documents and the web, get grounded answers with sources — every claim
              checked before you trust it.
            </p>
          </div>

          <div className="mt-8 w-full max-w-3xl animate-fade-up">
            <Composer
              verify={verify}
              onToggleVerify={setVerify}
              onSubmit={(q) => {
                // Wired to the agent endpoint in the next chunk (5c).
                console.log("question:", q, "verify:", verify);
              }}
            />
            <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
              {CATEGORIES.map(({ label, icon: Icon }) => (
                <button key={label} type="button" className="chip">
                  <Icon className="h-4 w-4" /> {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
