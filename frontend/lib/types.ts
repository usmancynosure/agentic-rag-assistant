/** TypeScript mirrors of the backend DTOs. */

export type DocumentStatus = "pending" | "processing" | "ready" | "failed";

export interface DocumentOut {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  status: DocumentStatus;
  chunk_count: number;
  error: string | null;
  created_at: string;
}

export interface DocumentList {
  items: DocumentOut[];
  total: number;
}

export interface Citation {
  index: number;
  chunk_id: string;
  document_id: string | null;
  filename: string;
  page: number | null;
  origin: "vector" | "web";
  url: string | null;
}

export interface Source extends Citation {
  score: number;
  snippet: string;
}

export interface Verification {
  trustworthy: boolean;
  verdict: "high" | "medium" | "low";
  confidence: number;
  grounded: boolean;
  grounding_score: number;
  unsupported_claims: string[];
  citations_valid: boolean;
  citation_coverage: number;
  invalid_citation_indices: number[];
  uncited_sentences: string[];
  reasoning: string;
}

export interface AgentQueryResponse {
  answer: string;
  citations: Citation[];
  sources: Source[];
  tools_run: string[];
  iterations: number;
  verification: Verification | null;
}

export interface AgentQueryRequest {
  question: string;
  document_id?: string | null;
  max_iterations?: number | null;
  verify?: boolean;
}
