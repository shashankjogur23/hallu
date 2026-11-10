/**
 * Central API client for HalluGuard FastAPI backend.
 */

import type {
  HealthResponse,
  VerificationRequest,
  VerificationResponse,
  DocumentDetail,
  DocumentListResponse,
  VerificationHistoryResponse,
  VerificationStats,
  ChunkResponse,
  RetrieveResponse,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    try {
      const response = await fetch(url, options);

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            if (Array.isArray(errorData.detail)) {
              errorMessage = errorData.detail.map((d: any) => `${d.loc?.slice(-1)[0] || 'field'}: ${d.msg}`).join(', ');
            } else {
              errorMessage = String(errorData.detail);
            }
          }
        } catch {
          // Response wasn't json, use default status text
        }
        throw new Error(errorMessage);
      }

      return (await response.json()) as T;
    } catch (err: any) {
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        throw new Error(
          `Unable to connect to HalluGuard backend at ${this.baseUrl}. Please verify the FastAPI server is running.`
        );
      }
      throw err;
    }
  }

  /**
   * Health check
   */
  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  /**
   * Main hallucination verification
   */
  async verifyAnswer(payload: VerificationRequest): Promise<VerificationResponse> {
    return this.request<VerificationResponse>('/verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
  }

  /**
   * Upload and ingest reference document (PDF or TXT)
   */
  async uploadDocument(
    file: File,
    chunkSize: number = 500,
    chunkOverlap: number = 100
  ): Promise<DocumentDetail> {
    const formData = new FormData();
    formData.append('file', file);

    const queryParams = new URLSearchParams({
      chunk_size: String(chunkSize),
      chunk_overlap: String(chunkOverlap),
    });

    return this.request<DocumentDetail>(`/documents/upload?${queryParams.toString()}`, {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * List all uploaded documents
   */
  async listDocuments(): Promise<DocumentListResponse> {
    return this.request<DocumentListResponse>('/documents');
  }

  /**
   * Get single document details
   */
  async getDocument(documentId: string): Promise<DocumentDetail> {
    return this.request<DocumentDetail>(`/documents/${documentId}`);
  }

  /**
   * Delete uploaded document
   */
  async deleteDocument(documentId: string): Promise<{ deleted: boolean; id: string }> {
    return this.request<{ deleted: boolean; id: string }>(`/documents/${documentId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Chunk text directly
   */
  async chunkText(
    text: string,
    chunkSize: number = 500,
    chunkOverlap: number = 100,
    documentName?: string
  ): Promise<ChunkResponse> {
    const params = new URLSearchParams({
      text,
      chunk_size: String(chunkSize),
      chunk_overlap: String(chunkOverlap),
    });
    if (documentName) {
      params.append('document_name', documentName);
    }
    return this.request<ChunkResponse>(`/context/chunk?${params.toString()}`, {
      method: 'POST',
    });
  }

  /**
   * Retrieve relevant context chunks for a query
   */
  async retrieveContexts(
    query: string,
    contexts: string[],
    topK: number = 3
  ): Promise<RetrieveResponse> {
    return this.request<RetrieveResponse>('/context/retrieve', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        contexts,
        top_k: topK,
      }),
    });
  }

  /**
   * Get verification history
   */
  async getVerificationHistory(limit: number = 50): Promise<VerificationHistoryResponse> {
    return this.request<VerificationHistoryResponse>(`/verifications/history?limit=${limit}`);
  }

  /**
   * Get real verification counts and statistics
   */
  async getVerificationStats(): Promise<VerificationStats> {
    return this.request<VerificationStats>('/verifications/stats');
  }
}

export const api = new ApiService(API_BASE_URL);
