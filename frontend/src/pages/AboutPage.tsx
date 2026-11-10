import React from 'react';
import {
  Info,
  Cpu,
  Layers,
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  GitBranch,
} from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Page Header */}
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Info className="w-6 h-6 text-blue-600" />
          <span>About HalluGuard & Methodology</span>
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Theoretical grounding, architecture, model lineage, and operational scope.
        </p>
      </div>

      {/* Overview Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs space-y-4">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-indigo-600" />
          <span>1. What are Hallucinations in Generative AI?</span>
        </h2>
        <p className="text-sm text-slate-700 leading-relaxed">
          Large Language Models (LLMs) like GPT-4, Gemini, and Claude generate text probabilistically based on learned token associations. While proficient in natural language fluency, they frequently generate assertions that appear convincing but are factually unsupported, logically contradictory, or fabricated.
        </p>
        <p className="text-sm text-slate-700 leading-relaxed">
          In high-stakes domains—such as healthcare, legal discovery, financial reporting, and Retrieval-Augmented Generation (RAG)—unverified answers risk serious real-world harm. Factual grounding verification is therefore essential to detect unsupported claims before they reach end users.
        </p>
      </div>

      {/* How HalluGuard Works */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs space-y-6">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Layers className="w-5 h-5 text-blue-600" />
          <span>2. How HalluGuard Operates</span>
        </h2>
        <p className="text-sm text-slate-700 leading-relaxed">
          HalluGuard is an end-to-end hallucination detection framework. Rather than returning an opaque, answer-level binary verdict, HalluGuard operates at the fine-grained <strong>token and character span level</strong>.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 font-bold text-xs flex items-center justify-center">
              1
            </div>
            <h3 className="font-bold text-slate-900 text-sm">Context Ingestion</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Accepts ground truth context from uploaded PDFs, text files, or direct excerpts. Automatically splits passages into coherent semantic chunks.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-700 font-bold text-xs flex items-center justify-center">
              2
            </div>
            <h3 className="font-bold text-slate-900 text-sm">ModernBERT Inference</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Feeds the reference context, question, and answer into the encoder model. Evaluates token-level hallucination probabilities via cross-attention.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="w-7 h-7 rounded-lg bg-purple-100 text-purple-700 font-bold text-xs flex items-center justify-center">
              3
            </div>
            <h3 className="font-bold text-slate-900 text-sm">Span Localization</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Aggregates positive hallucination tokens into contiguous character spans with confidence scores and highlights unsupported statements directly.
            </p>
          </div>
        </div>
      </div>

      {/* Role of LettuceDetect */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs space-y-4">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-emerald-600" />
          <h2 className="text-lg font-bold text-slate-900">
            3. The Role of LettuceDetect & Model Attribution
          </h2>
        </div>

        <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-200 text-xs text-blue-900 leading-relaxed space-y-2">
          <div className="font-bold flex items-center gap-1.5 text-blue-950">
            <GitBranch className="w-4 h-4 text-blue-600" />
            <span>Pretrained Model Lineage Notice</span>
          </div>
          <p>
            HalluGuard integrates the official pretrained <strong>KRLabsOrg/LettuceDetect</strong> model (specifically <code className="bg-white px-1.5 py-0.5 rounded border border-blue-200 font-mono">KRLabsOrg/lettucedect-base-modernbert-en-v1</code>).
          </p>
          <p>
            <strong>We do not claim to have trained a new foundation model from scratch.</strong> Our contribution is developing the HalluGuard framework: the production FastAPI backend, model lifespan loader, PyMuPDF ingestion engine, retrieval pipeline, database persistence layer, and interactive verification UI.
          </p>
        </div>

        <div className="space-y-2 text-sm text-slate-700 leading-relaxed">
          <p>
            LettuceDetect is inspired by the Luna architecture (COLING Industry 2025). It uses ModernBERT's native 8192-token context window and optimized unpadded FlashAttention-style representations to classify whether each token in an answer is supported by the context.
          </p>
        </div>
      </div>

      {/* Project Limitations */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs space-y-4">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-600" />
          <span>4. Known Framework Limitations</span>
        </h2>

        <div className="space-y-3 text-xs text-slate-700">
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-slate-900">Grounding vs. Universal Truth:</span>
              <p className="mt-0.5 text-slate-600">
                The detector flags claims that lack evidence in the provided reference context. If the reference context itself contains inaccurate information, the detector will treat that inaccurate context as ground truth.
              </p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-slate-900">Token Span Boundary Granularity:</span>
              <p className="mt-0.5 text-slate-600">
                When a numeric claim or entity is contradictory (e.g. "69 million" instead of "67 million"), the model typically flags the entire surrounding sentence or clause as unsupported. This is by design, as the entire assertion is false.
              </p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-slate-900">CPU Inference Latency:</span>
              <p className="mt-0.5 text-slate-600">
                Running ModernBERT on CPU requires ~15 seconds on initial server startup and 200–500ms per verification request. While acceptable for interactive verification, GPU acceleration is recommended for high-throughput production.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
