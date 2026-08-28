"use client";

import { useEffect, useRef, useState } from "react";
import AnswerCard from "@/components/AnswerCard";
import Composer from "@/components/Composer";
import DocumentsPanel from "@/components/DocumentsPanel";
import Sidebar from "@/components/Sidebar";
import { BotIcon, FolderIcon } from "@/components/icons";
import { agentQuery } from "@/lib/api";
import type { AgentQueryResponse } from "@/lib/types";

interface Turn {
  id: number;
  question: string;
  response?: AgentQueryResponse;
  error?: string;
}

const SUGGESTIONS = [
  "Summarize the key points across my documents",
  "What does the onboarding policy say about SLAs?",
  "Compare the two contracts I uploaded",
];

export default function Page() {
  const [verify, setVerify] = useState(true);
  const [docsOpen, setDocsOpen] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [pending, setPending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const nextId = useRef(1);

  const empty = turns.length === 0;

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns, pending]);

  async function ask(question: string) {
    if (pending) return;
    const id = nextId.current++;
    setTurns((prev) => [...prev, { id, question }]);
    setPending(true);
    try {
      const response = await agentQuery({ question, verify });
      setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, response } : t)));
    } catch (e) {
      const error = e instanceof Error ? e.message : "Something went wrong";
      setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, error } : t)));
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="mx-auto flex h-screen max-w-[1400px] gap-3 p-4">
      <DocumentsPanel open={docsOpen} onClose={() => setDocsOpen(false)} />

      <div className="glass-soft sticky top-4 hidden h-[calc(100vh-2rem)] rounded-4xl px-2 md:flex">
        <Sidebar onOpenDocuments={() => setDocsOpen(true)} />
      </div>

      <section className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center justify-between px-2 py-3">
          <div className="glass flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-semibold">
            <BotIcon className="h-5 w-5 text-primary" aria-hidden />
            Agentic RAG · Opus 4.8
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setDocsOpen(true)}
              className="glass flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-semibold text-ink transition-colors hover:text-primary cursor-pointer"
            >
              <FolderIcon className="h-5 w-5" aria-hidden /> Documents
            </button>
            <a
              href="https://github.com/usmancynosure/agentic-rag-assistant"
              className="rounded-2xl bg-ink px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90"
            >
              GitHub
            </a>
          </div>
        </header>

        {/* Conversation (answers on top) */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-1 sm:px-2">
          {empty ? (
            <div className="flex h-full flex-col items-center justify-center px-4 text-center">
              <div className="animate-fade-up">
                <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-3xl bg-gradient-to-br from-primary to-secondary text-white shadow-rail">
                  <BotIcon className="h-9 w-9" aria-hidden />
                </div>
                <h2 className="font-display text-4xl leading-tight text-ink sm:text-5xl">
                  Ask. <span className="text-primary">Verify.</span> Cite.
                </h2>
                <p className="mx-auto mt-3 max-w-xl text-base text-muted">
                  Search your documents and the web, get grounded answers with sources — every
                  claim checked before you trust it.
                </p>
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button key={s} type="button" className="chip" onClick={() => void ask(s)}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="mx-auto flex max-w-3xl flex-col gap-4 py-4">
              {turns.map((turn) => (
                <div key={turn.id} className="flex flex-col gap-3">
                  <div className="flex justify-end">
                    <div className="max-w-[85%] rounded-3xl rounded-br-lg bg-gradient-to-br from-primary to-primary-700 px-4 py-2.5 text-white shadow-rail">
                      {turn.question}
                    </div>
                  </div>
                  {turn.response && <AnswerCard res={turn.response} />}
                  {turn.error && (
                    <div className="rounded-3xl bg-rose-50 px-4 py-3 text-sm text-rose-700">
                      {turn.error}
                    </div>
                  )}
                </div>
              ))}
              {pending && (
                <div className="glass flex w-fit items-center gap-2 rounded-3xl px-4 py-3 text-sm text-muted">
                  <span className="flex gap-1">
                    <span className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.3s]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.15s]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-primary" />
                  </span>
                  Planning tools, searching, verifying…
                </div>
              )}
            </div>
          )}
        </div>

        {/* Composer (Ask below) */}
        <div className="mx-auto w-full max-w-3xl px-1 pb-1 pt-3 sm:px-2">
          <Composer verify={verify} onToggleVerify={setVerify} onSubmit={ask} disabled={pending} />
        </div>
      </section>
    </main>
  );
}
