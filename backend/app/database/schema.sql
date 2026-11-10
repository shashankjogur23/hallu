-- ==============================================================================
-- HalluGuard Database Schema for Supabase (PostgreSQL)
-- ==============================================================================
-- Execute this SQL in your Supabase project's SQL Editor:
-- Dashboard -> SQL Editor -> New Query -> Paste & Run
-- ==============================================================================

-- 1. Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 2. Documents Table
-- Stores metadata of uploaded/indexed reference documents (PDF, TXT, etc.)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL, -- e.g. "application/pdf", "text/plain"
    file_size INTEGER NOT NULL, -- in bytes
    chunk_count INTEGER NOT NULL DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Index for searching documents by filename or creation date
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON public.documents (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_filename ON public.documents (filename);

-- ------------------------------------------------------------------------------
-- 3. Verifications Table
-- Stores each hallucination verification run and its high-level verdict
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.verifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES public.documents(id) ON DELETE SET NULL,
    question TEXT,
    answer TEXT NOT NULL,
    context TEXT[] NOT NULL,
    is_hallucinated BOOLEAN NOT NULL DEFAULT FALSE,
    hallucination_score DOUBLE PRECISION,
    span_count INTEGER NOT NULL DEFAULT 0,
    model_name TEXT NOT NULL,
    execution_time_ms DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Index for querying verification history
CREATE INDEX IF NOT EXISTS idx_verifications_created_at ON public.verifications (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_verifications_is_hallucinated ON public.verifications (is_hallucinated);
CREATE INDEX IF NOT EXISTS idx_verifications_document_id ON public.verifications (document_id);

-- ------------------------------------------------------------------------------
-- 4. Verification Spans Table
-- Stores fine-grained span-level detections for each verification
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.verification_spans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    verification_id UUID NOT NULL REFERENCES public.verifications(id) ON DELETE CASCADE,
    span_text TEXT NOT NULL,
    start_offset INTEGER NOT NULL,
    end_offset INTEGER NOT NULL,
    confidence DOUBLE PRECISION,
    category TEXT, -- contradiction, unsupported_addition, fabricated_reference, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Index for joining spans with verification records
CREATE INDEX IF NOT EXISTS idx_spans_verification_id ON public.verification_spans (verification_id);

-- ------------------------------------------------------------------------------
-- 5. Row Level Security (RLS) Configuration
-- Enable RLS and define policies for service-role and authenticated access
-- ------------------------------------------------------------------------------
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.verification_spans ENABLE ROW LEVEL SECURITY;

-- Service role full access policy (for backend operations via SUPABASE_SERVICE_ROLE_KEY)
CREATE POLICY "Service role full access on documents"
    ON public.documents
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on verifications"
    ON public.verifications
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on verification_spans"
    ON public.verification_spans
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Authenticated users read-only policy (for frontend dashboard in later phases)
CREATE POLICY "Authenticated users can read verifications"
    ON public.verifications
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Authenticated users can read verification_spans"
    ON public.verification_spans
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Authenticated users can read documents"
    ON public.documents
    FOR SELECT
    TO authenticated
    USING (true);

