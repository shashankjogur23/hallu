"""Pydantic schemas for verification and document processing."""

from pydantic import BaseModel, Field, field_validator
from typing import Any


class VerificationRequest(BaseModel):
    """Input payload for hallucination verification."""

    question: str | None = Field(
        default=None,
        description="The user question or prompt. Optional (used in QA mode; if omitted, summarization mode is used).",
    )
    answer: str = Field(
        ...,
        min_length=1,
        description="The AI-generated answer to verify for hallucinations.",
    )
    context: list[str] | str = Field(
        ...,
        description="Ground truth reference passage(s). Can be a list of passage strings or a single text block.",
    )
    min_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold (0.0 to 1.0) to include a detected span.",
    )

    @field_validator("answer")
    @classmethod
    def validate_answer_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Answer cannot be empty or contain only whitespace.")
        return v

    @field_validator("context")
    @classmethod
    def validate_context_not_empty(cls, v: list[str] | str) -> list[str]:
        if isinstance(v, str):
            if not v.strip():
                raise ValueError("Context cannot be empty.")
            return [v.strip()]
        if isinstance(v, list):
            cleaned = [item.strip() for item in v if isinstance(item, str) and item.strip()]
            if not cleaned:
                raise ValueError("Context list must contain at least one non-empty passage.")
            return cleaned
        raise ValueError("Context must be a string or a list of strings.")


class HallucinationSpan(BaseModel):
    """Detected hallucinated span with character offsets and confidence."""

    start: int = Field(..., description="Start character offset in the answer string.")
    end: int = Field(..., description="End character offset in the answer string.")
    text: str = Field(..., description="The hallucinated text substring.")
    confidence: float | None = Field(
        default=None,
        description="Model confidence probability (0.0 to 1.0) for this hallucinated span.",
    )
    category: str | None = Field(
        default=None,
        description="Optional taxonomy category if classified.",
    )


class ClaimDetail(BaseModel):
    """Detailed claim with semantic categorization and explanation."""

    start: int = Field(..., description="Start character offset in answer.")
    end: int = Field(..., description="End character offset in answer.")
    text: str = Field(..., description="The claim substring.")
    confidence: float | None = Field(default=None, description="Detector confidence score.")
    category: str = Field(..., description="Claim category: 'contradiction', 'unsupported', or 'supported'.")
    source: str = Field(default="hybrid", description="Detection source: 'lettucedetect_token' or 'nli_cross_encoder'.")
    explanation: str | None = Field(default=None, description="Human-readable explanation of why this claim was flagged.")


class DetectorBreakdown(BaseModel):
    """Component-level metrics and verdicts from each model."""

    lettucedetect_spans: int = Field(default=0, description="Count of token-level spans from LettuceDetect.")
    lettucedetect_verdict: str = Field(default="UNKNOWN", description="LettuceDetect verdict.")
    nli_contradictions: int = Field(default=0, description="Count of contradictory propositions from NLI.")
    nli_max_contradiction: float = Field(default=0.0, description="Peak contradiction probability from NLI.")
    fusion_verdict: str = Field(..., description="Final fused verdict.")
    fusion_source: str = Field(..., description="Decision fusion rule applied.")
    lettucedetect_latency_ms: float = Field(default=0.0, description="LettuceDetect execution time.")
    nli_latency_ms: float = Field(default=0.0, description="NLI execution time.")


class VerificationSummary(BaseModel):
    """High-level summary of verification results."""

    is_hallucinated: bool = Field(
        ..., description="True if any hallucinated or contradictory span was detected above threshold."
    )
    span_count: int = Field(
        ..., description="Total count of suspicious spans detected."
    )
    max_confidence: float | None = Field(
        default=None, description="Highest confidence score among all detected spans."
    )
    verdict: str = Field(
        ..., description="'SUPPORTED', 'CONTRADICTED', 'UNSUPPORTED', or 'INSUFFICIENT_EVIDENCE' (or legacy 'CLEAN'/'HALLUCINATED')."
    )
    message: str = Field(..., description="Human-readable verification outcome.")


class VerificationResponse(BaseModel):
    """Response payload for hallucination verification."""

    id: str = Field(..., description="Unique verification identifier.")
    question: str | None = Field(default=None, description="Original question.")
    answer: str = Field(..., description="Verified answer text.")
    context: list[str] = Field(..., description="Reference contexts used.")
    spans: list[HallucinationSpan] = Field(
        default_factory=list, description="List of detected hallucination spans."
    )
    summary: VerificationSummary = Field(
        ..., description="Summary verdict of the verification."
    )
    model: str = Field(..., description="Name/path of the detector model used.")
    execution_time_ms: float = Field(
        ..., description="Inference time in milliseconds."
    )
    contradicted_claims: list[ClaimDetail] = Field(
        default_factory=list, description="Claims conflicting directly with reference context."
    )
    unsupported_claims: list[ClaimDetail] = Field(
        default_factory=list, description="Claims fabricated or unestablished by reference context."
    )
    supported_claims: list[ClaimDetail] = Field(
        default_factory=list, description="Claims substantiated by reference context."
    )
    detector_breakdown: DetectorBreakdown | None = Field(
        default=None, description="Detailed component breakdown from LettuceDetect and NLI."
    )
    retrieved_evidence: list[str] = Field(
        default_factory=list, description="Evidence passages utilized during verification."
    )


class HealthResponse(BaseModel):
    """Response payload for system health check."""

    status: str
    detector_loaded: bool
    nli_loaded: bool = False
    hybrid_ready: bool = False
    model_name: str
    device: str
    supabase_configured: bool
    version: str


class ChunkItem(BaseModel):
    """A single text chunk from a document."""

    chunk_index: int
    text: str
    char_start: int
    char_end: int


class ChunkResponse(BaseModel):
    """Result of document text chunking."""

    document_name: str | None = None
    total_chunks: int
    chunks: list[ChunkItem]


class RetrieveRequest(BaseModel):
    """Payload to retrieve relevant context chunks for a query."""

    query: str = Field(..., min_length=1, description="Question or text to match.")
    contexts: list[str] = Field(
        ..., min_length=1, description="List of text chunks to search."
    )
    top_k: int = Field(default=3, ge=1, description="Number of top chunks to return.")


class RetrievedChunk(BaseModel):
    """A retrieved chunk with its similarity score."""

    chunk_index: int
    text: str
    score: float


class RetrieveResponse(BaseModel):
    """Result of relevant context retrieval."""

    query: str
    retrieved_chunks: list[RetrievedChunk]



class DocumentMetadata(BaseModel):
    """Metadata describing an ingested reference document."""

    id: str
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    created_at: str
    is_persistent: bool


class DocumentDetail(DocumentMetadata):
    """Full detail of an ingested document including text and chunks."""

    extracted_text: str
    chunks: list[ChunkItem]


class DocumentListResponse(BaseModel):
    """List of available documents with storage status notice."""

    documents: list[DocumentMetadata]
    total_documents: int
    is_persistent: bool
    storage_notice: str


class VerificationHistoryItem(BaseModel):
    """Stored verification record."""

    id: str
    question: str | None = None
    answer: str
    context: list[str]
    spans: list[HallucinationSpan]
    summary: VerificationSummary
    model: str
    execution_time_ms: float
    created_at: str


class VerificationHistoryResponse(BaseModel):
    """Verification history response with persistence status notice."""

    verifications: list[VerificationHistoryItem]
    total: int
    is_persistent: bool
    storage_notice: str
