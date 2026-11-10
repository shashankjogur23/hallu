/**
 * HalluGuard API TypeScript type definitions.
 * Synchronized with FastAPI Pydantic schemas.
 */

export interface HallucinationSpan {
  start: number;
  end: number;
  text: string;
  confidence: number | null;
  category?: string | null;
}

export interface ClaimDetail {
  start: number;
  end: number;
  text: string;
  confidence: number | null;
  category: 'contradiction' | 'unsupported' | 'supported' | string;
  source: string;
  explanation?: string | null;
}

export interface DetectorBreakdown {
  lettucedetect_spans: number;
  lettucedetect_verdict: string;
  nli_contradictions: number;
  nli_max_contradiction: number;
  fusion_verdict: string;
  fusion_source: string;
  lettucedetect_latency_ms?: number;
  nli_latency_ms?: number;
}

export interface VerificationSummary {
  is_hallucinated: boolean;
  span_count: number;
  max_confidence: number | null;
  verdict: 'CLEAN' | 'HALLUCINATED' | 'SUPPORTED' | 'CONTRADICTED' | 'UNSUPPORTED' | 'INSUFFICIENT_EVIDENCE' | string;
  message: string;
}

export interface VerificationRequest {
  question?: string | null;
  answer: string;
  context: string[] | string;
  min_confidence?: number;
}

export interface VerificationResponse {
  id: string;
  question: string | null;
  answer: string;
  context: string[];
  spans: HallucinationSpan[];
  summary: VerificationSummary;
  model: string;
  execution_time_ms: number;
  contradicted_claims?: ClaimDetail[];
  unsupported_claims?: ClaimDetail[];
  supported_claims?: ClaimDetail[];
  detector_breakdown?: DetectorBreakdown | null;
  retrieved_evidence?: string[];
}

export interface HealthResponse {
  status: string;
  detector_loaded: boolean;
  nli_loaded?: boolean;
  hybrid_ready?: boolean;
  model_name: string;
  device: string;
  supabase_configured: boolean;
  version: string;
}

export interface ChunkItem {
  chunk_index: number;
  text: string;
  char_start: number;
  char_end: number;
}

export interface ChunkResponse {
  document_name?: string | null;
  total_chunks: number;
  chunks: ChunkItem[];
}

export interface RetrievedChunk {
  chunk_index: number;
  text: string;
  score: number;
}

export interface RetrieveResponse {
  query: string;
  retrieved_chunks: RetrievedChunk[];
}

export interface DocumentMetadata {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  chunk_count: number;
  created_at: string;
  is_persistent: boolean;
}

export interface DocumentDetail extends DocumentMetadata {
  extracted_text: string;
  chunks: ChunkItem[];
}

export interface DocumentListResponse {
  documents: DocumentMetadata[];
  total_documents: number;
  is_persistent: boolean;
  storage_notice: string;
}

export interface VerificationHistoryItem {
  id: string;
  question: string | null;
  answer: string;
  context: string[];
  spans: HallucinationSpan[];
  summary: VerificationSummary;
  model: string;
  execution_time_ms: number;
  created_at: string;
}

export interface VerificationHistoryResponse {
  verifications: VerificationHistoryItem[];
  total: number;
  is_persistent: boolean;
  storage_notice: string;
}

export interface VerificationStats {
  total_verifications: number;
  flagged_answers: number;
  clean_answers: number;
  is_persistent: boolean;
  source: string;
}

