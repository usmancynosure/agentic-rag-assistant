/** Typed API client. Base URL comes from the environment, never hardcoded. */

import type {
  AgentQueryRequest,
  AgentQueryResponse,
  DocumentList,
  DocumentOut,
} from "./types";

const BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";
const PREFIX = "/api/v1";

function url(path: string): string {
  return `${BASE}${PREFIX}${path}`;
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      message = body?.error?.message ?? body?.detail?.[0]?.msg ?? message;
    } catch {
      /* keep default message */
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export async function listDocuments(): Promise<DocumentList> {
  return handle(await fetch(url("/documents"), { cache: "no-store" }));
}

export async function uploadDocument(file: File): Promise<DocumentOut> {
  const form = new FormData();
  form.append("file", file);
  return handle(await fetch(url("/documents"), { method: "POST", body: form }));
}

export async function deleteDocument(id: string): Promise<void> {
  const res = await fetch(url(`/documents/${id}`), { method: "DELETE" });
  if (!res.ok && res.status !== 204) {
    throw new Error(`Delete failed (${res.status})`);
  }
}

export async function agentQuery(req: AgentQueryRequest): Promise<AgentQueryResponse> {
  return handle(
    await fetch(url("/agent/query"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    }),
  );
}

export { BASE as API_BASE };
