"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { deleteDocument, listDocuments, uploadDocument } from "@/lib/api";
import type { DocumentOut, DocumentStatus } from "@/lib/types";
import { FileIcon, TrashIcon, UploadIcon } from "./icons";

const STATUS_STYLES: Record<DocumentStatus, string> = {
  ready: "bg-emerald-100 text-emerald-700",
  processing: "bg-amber-100 text-amber-700",
  pending: "bg-slate-100 text-slate-600",
  failed: "bg-rose-100 text-rose-700",
};

const ACCEPT = ".pdf,.docx,.txt,.md,.markdown";

function humanSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function DocumentsPanel({ open, onClose }: Props) {
  const [docs, setDocs] = useState<DocumentOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listDocuments();
      setDocs(data.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load documents");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) void refresh();
  }, [open, refresh]);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setUploading(true);
    setError(null);
    try {
      for (const file of Array.from(files)) {
        await uploadDocument(file);
      }
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteDocument(id);
      setDocs((prev) => prev.filter((d) => d.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  }

  return (
    <div
      className={`fixed inset-0 z-40 transition-opacity duration-200 ${
        open ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"
      }`}
      aria-hidden={!open}
    >
      <button
        type="button"
        aria-label="Close documents"
        className="absolute inset-0 bg-ink/20 backdrop-blur-sm cursor-pointer"
        onClick={onClose}
      />
      <aside
        className={`glass absolute right-0 top-0 flex h-full w-full max-w-md flex-col rounded-l-4xl p-6 transition-transform duration-300 ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
        role="dialog"
        aria-label="Documents"
      >
        <div className="flex items-center justify-between">
          <h2 className="font-display text-xl text-ink">Documents</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl px-3 py-1 text-sm font-semibold text-muted hover:bg-white hover:text-ink cursor-pointer"
          >
            Close
          </button>
        </div>

        <label
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            void handleFiles(e.dataTransfer.files);
          }}
          className={`mt-5 flex cursor-pointer flex-col items-center gap-2 rounded-3xl border-2 border-dashed p-6 text-center transition-colors ${
            dragging ? "border-primary bg-primary/5" : "border-white/70 bg-white/40"
          }`}
        >
          <UploadIcon className="h-7 w-7 text-primary" aria-hidden />
          <span className="text-sm font-semibold text-ink">
            {uploading ? "Uploading…" : "Drop files or click to upload"}
          </span>
          <span className="text-xs text-muted">PDF, DOCX, TXT, MD · up to 25 MB</span>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT}
            multiple
            className="hidden"
            onChange={(e) => void handleFiles(e.target.files)}
          />
        </label>

        {error && (
          <p className="mt-3 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>
        )}

        <div className="mt-5 flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-muted">
            {docs.length} document{docs.length === 1 ? "" : "s"}
          </span>
          <button
            type="button"
            onClick={() => void refresh()}
            className="text-xs font-semibold text-primary hover:underline cursor-pointer"
          >
            Refresh
          </button>
        </div>

        <div className="mt-3 flex-1 space-y-2 overflow-y-auto pr-1">
          {loading && docs.length === 0 && (
            <p className="text-sm text-muted">Loading…</p>
          )}
          {!loading && docs.length === 0 && (
            <p className="rounded-2xl bg-white/50 p-4 text-sm text-muted">
              No documents yet. Upload one to start asking grounded questions.
            </p>
          )}
          {docs.map((doc) => (
            <div
              key={doc.id}
              className="glass-soft flex items-center gap-3 rounded-2xl px-3 py-3"
            >
              <FileIcon className="h-5 w-5 shrink-0 text-primary" aria-hidden />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-ink">{doc.filename}</p>
                <p className="text-xs text-muted">
                  {humanSize(doc.size_bytes)} · {doc.chunk_count} chunks
                </p>
              </div>
              <span
                className={`rounded-full px-2.5 py-1 text-xs font-bold ${STATUS_STYLES[doc.status]}`}
              >
                {doc.status}
              </span>
              <button
                type="button"
                aria-label={`Delete ${doc.filename}`}
                onClick={() => void handleDelete(doc.id)}
                className="rounded-lg p-1.5 text-muted hover:bg-rose-50 hover:text-rose-600 cursor-pointer"
              >
                <TrashIcon className="h-4 w-4" aria-hidden />
              </button>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}
