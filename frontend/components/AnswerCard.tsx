import type { AgentQueryResponse } from "@/lib/types";
import { AlertIcon, CheckShieldIcon, ResearchIcon } from "./icons";

/** Render answer text, turning [n] markers into citation superscripts. */
function renderAnswer(text: string) {
  return text.split(/(\[\d+\])/g).map((part, i) => {
    if (/^\[\d+\]$/.test(part)) {
      return (
        <sup key={i} className="ml-0.5 font-extrabold text-primary-700">
          {part}
        </sup>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

function VerificationBadge({ res }: { res: AgentQueryResponse }) {
  const v = res.verification;
  if (!v) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
        <CheckShieldIcon className="h-4 w-4" aria-hidden /> Sources only
      </span>
    );
  }
  const pct = Math.round(v.confidence * 100);
  if (v.trustworthy) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700">
        <CheckShieldIcon className="h-4 w-4" aria-hidden /> Verified · {pct}% confidence
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-700">
      <AlertIcon className="h-4 w-4" aria-hidden /> Unverified · {pct}%
    </span>
  );
}

export default function AnswerCard({ res }: { res: AgentQueryResponse }) {
  const v = res.verification;
  return (
    <div className="glass animate-fade-up rounded-3xl p-5 sm:p-6">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <VerificationBadge res={res} />
        {res.tools_run.length > 0 && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold text-primary-700">
            <ResearchIcon className="h-4 w-4" aria-hidden />
            {res.tools_run.join(" + ")} · {res.iterations} pass{res.iterations === 1 ? "" : "es"}
          </span>
        )}
      </div>

      <p className="whitespace-pre-wrap leading-7 text-ink">{renderAnswer(res.answer)}</p>

      {v && !v.trustworthy && v.unsupported_claims.length > 0 && (
        <div className="mt-3 rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <p className="font-bold">Claims not supported by the sources:</p>
          <ul className="mt-1 list-disc pl-5">
            {v.unsupported_claims.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}

      {res.sources.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-xs font-bold uppercase tracking-wider text-muted">Sources</p>
          <div className="space-y-2">
            {res.sources.map((s) => (
              <div
                key={s.chunk_id}
                className="glass-soft flex items-start gap-3 rounded-2xl px-3 py-2.5"
              >
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-indigo-50 text-xs font-extrabold text-primary-700">
                  {s.index}
                </span>
                <div className="min-w-0 flex-1 text-sm">
                  {s.origin === "web" && s.url ? (
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noreferrer"
                      className="font-bold text-primary-700 hover:underline"
                    >
                      {s.filename}
                    </a>
                  ) : (
                    <span className="font-bold text-ink">
                      {s.filename}
                      {s.page != null ? ` · p.${s.page}` : ""}
                    </span>
                  )}
                  <p className="text-muted">{s.snippet}</p>
                </div>
                <span className="shrink-0 text-xs font-bold tabular-nums text-accent">
                  {s.score.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
