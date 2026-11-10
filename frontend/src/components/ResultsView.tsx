import React from 'react';
import type { VerificationResponse } from '../types/api';
import { SpanHighlighter } from './SpanHighlighter';
import {
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  FileText,
  RotateCcw,
  Info,
  Layers,
  HelpCircle,
  Cpu,
} from 'lucide-react';

interface ResultsViewProps {
  result: VerificationResponse;
  onReset: () => void;
}

export const ResultsView: React.FC<ResultsViewProps> = ({ result, onReset }) => {
  const isHallucinated = result.summary.is_hallucinated;
  const verdict = result.summary.verdict.toUpperCase();
  const maxConfPct =
    result.summary.max_confidence !== null
      ? `${(result.summary.max_confidence * 100).toFixed(1)}%`
      : 'N/A';

  // Determine styles and icons based on 4-way verdict
  let bannerClass = 'bg-emerald-50/70 border-emerald-200 text-emerald-950';
  let badgeClass = 'bg-emerald-200 text-emerald-800';
  let iconBgClass = 'bg-emerald-600 text-white';
  let VerdictIcon = ShieldCheck;
  let verdictTitle = 'All Claims Grounded and Supported';

  if (verdict === 'CONTRADICTED') {
    bannerClass = 'bg-red-50/70 border-red-200 text-red-950';
    badgeClass = 'bg-red-200 text-red-800';
    iconBgClass = 'bg-red-600 text-white';
    VerdictIcon = AlertOctagon;
    verdictTitle = 'Direct Contradiction Detected';
  } else if (verdict === 'UNSUPPORTED' || verdict === 'HALLUCINATED') {
    bannerClass = 'bg-amber-50/70 border-amber-200 text-amber-950';
    badgeClass = 'bg-amber-200 text-amber-800';
    iconBgClass = 'bg-amber-600 text-white';
    VerdictIcon = AlertTriangle;
    verdictTitle = 'Unsubstantiated / Fabricated Claims';
  } else if (verdict === 'INSUFFICIENT_EVIDENCE') {
    bannerClass = 'bg-slate-50 border-slate-300 text-slate-900';
    badgeClass = 'bg-slate-200 text-slate-800';
    iconBgClass = 'bg-slate-600 text-white';
    VerdictIcon = HelpCircle;
    verdictTitle = 'Insufficient Reference Evidence';
  }

  const contradicted = result.contradicted_claims || [];
  const unsupported = result.unsupported_claims || [];
  const supported = result.supported_claims || [];
  const breakdown = result.detector_breakdown;

  return (
    <div className="space-y-6">
      {/* Top Verdict Banner */}
      <div className={`rounded-2xl p-6 border shadow-xs transition-all ${bannerClass}`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div
              className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 shadow-xs ${iconBgClass}`}
            >
              <VerdictIcon className="w-7 h-7" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2.5">
                <span
                  className={`text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full ${badgeClass}`}
                >
                  Verdict: {result.summary.verdict}
                </span>
                <span className="text-xs text-slate-500 font-mono">
                  ID: {result.id.slice(0, 8)}
                </span>
              </div>
              <h2 className="text-xl font-extrabold tracking-tight">
                {verdictTitle}
              </h2>
              <p className="text-sm opacity-90 leading-relaxed">
                {result.summary.message}
              </p>
            </div>
          </div>

          <button
            onClick={onReset}
            className="self-start sm:self-auto inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-semibold shadow-2xs transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Verify Another</span>
          </button>
        </div>

        {/* Quick Metrics Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5 pt-4 border-t border-slate-200/60 text-xs">
          <div>
            <span className="text-slate-500 block">Flagged Spans:</span>
            <span className="font-bold text-slate-900 text-sm">
              {result.summary.span_count}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block">Peak Confidence:</span>
            <span className="font-bold text-slate-900 text-sm">
              {maxConfPct}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block">Total Latency:</span>
            <span className="font-bold text-slate-900 text-sm">
              {result.execution_time_ms} ms
            </span>
          </div>
          <div>
            <span className="text-slate-500 block">Detector Pipeline:</span>
            <span
              className="font-mono text-slate-800 text-[11px] truncate block"
              title={result.model}
            >
              {result.model.includes('+') ? 'Hybrid (ModernBERT + DeBERTa)' : result.model.split('/').pop()}
            </span>
          </div>
        </div>
      </div>

      {/* Answer Analysis with Exact Character Offsets */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <span>Answer Span Localization</span>
            <span className="text-[11px] font-normal text-slate-500">
              (Fine-grained character offsets from Hybrid Pipeline)
            </span>
          </h3>
          {isHallucinated && (
            <span className="text-xs text-red-600 font-medium flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Highlighted spans mark ungrounded or contradictory claims</span>
            </span>
          )}
        </div>

        <SpanHighlighter answer={result.answer} spans={result.spans} />
      </div>

      {/* Structured Claims Breakdown (Phase 9 Integration) */}
      {(contradicted.length > 0 || unsupported.length > 0 || supported.length > 0) && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-600" />
            <span>Semantic Claims Analysis</span>
          </h3>

          {/* Contradicted Claims */}
          {contradicted.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-bold text-red-800 uppercase tracking-wider flex items-center gap-1.5">
                <AlertOctagon className="w-3.5 h-3.5 text-red-600" />
                <span>Contradicted Claims ({contradicted.length})</span>
              </div>
              <div className="space-y-2">
                {contradicted.map((c, i) => (
                  <div
                    key={i}
                    className="p-3 bg-red-50/60 border border-red-200 rounded-lg text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-red-950">"{c.text}"</span>
                      <span className="px-2 py-0.5 rounded bg-red-100 text-red-800 text-[11px] font-bold border border-red-300 shrink-0">
                        Contradiction: {c.confidence ? `${(c.confidence * 100).toFixed(1)}%` : 'Flagged'}
                      </span>
                    </div>
                    {c.explanation && (
                      <p className="text-red-800/90 text-[11px]">{c.explanation}</p>
                    )}
                    <div className="text-slate-400 text-[10px] font-mono">
                      Offsets: [{c.start}:{c.end}] | Source: {c.source}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Unsupported Claims */}
          {unsupported.length > 0 && (
            <div className="space-y-2 pt-2">
              <div className="text-xs font-bold text-amber-800 uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                <span>Unsupported Claims ({unsupported.length})</span>
              </div>
              <div className="space-y-2">
                {unsupported.map((u, i) => (
                  <div
                    key={i}
                    className="p-3 bg-amber-50/60 border border-amber-200 rounded-lg text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-amber-950">"{u.text}"</span>
                      <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 text-[11px] font-bold border border-amber-300 shrink-0">
                        Confidence: {u.confidence ? `${(u.confidence * 100).toFixed(1)}%` : 'Flagged'}
                      </span>
                    </div>
                    {u.explanation && (
                      <p className="text-amber-800/90 text-[11px]">{u.explanation}</p>
                    )}
                    <div className="text-slate-400 text-[10px] font-mono">
                      Offsets: [{u.start}:{u.end}] | Source: {u.source}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Supported Claims */}
          {supported.length > 0 && (
            <div className="space-y-2 pt-2">
              <div className="text-xs font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span>Grounded & Supported Claims ({supported.length})</span>
              </div>
              <div className="space-y-2">
                {supported.map((s, i) => (
                  <div
                    key={i}
                    className="p-3 bg-emerald-50/50 border border-emerald-200 rounded-lg text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-emerald-950">"{s.text}"</span>
                      <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[11px] font-bold border border-emerald-300 shrink-0">
                        Entailment: {s.confidence ? `${(s.confidence * 100).toFixed(1)}%` : 'Supported'}
                      </span>
                    </div>
                    <div className="text-slate-400 text-[10px] font-mono">
                      Offsets: [{s.start}:{s.end}] | Source: {s.source}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Detector Breakdown Card */}
      {breakdown && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-3">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-purple-600" />
            <span>Hybrid Detector Architecture Breakdown</span>
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
              <div className="font-semibold text-slate-700">LettuceDetect ModernBERT</div>
              <div className="text-slate-500 text-[11px]">Token-Level Classifier</div>
              <div className="pt-1 flex justify-between text-slate-800">
                <span>Spans Flagged:</span>
                <span className="font-bold">{breakdown.lettucedetect_spans}</span>
              </div>
              <div className="flex justify-between text-slate-800">
                <span>Latency:</span>
                <span className="font-mono">{breakdown.lettucedetect_latency_ms ?? 0} ms</span>
              </div>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
              <div className="font-semibold text-slate-700">DeBERTa-v3 Cross-Encoder</div>
              <div className="text-slate-500 text-[11px]">NLI Semantic Verifier</div>
              <div className="pt-1 flex justify-between text-slate-800">
                <span>Contradictions:</span>
                <span className="font-bold">{breakdown.nli_contradictions}</span>
              </div>
              <div className="flex justify-between text-slate-800">
                <span>Max Contradiction:</span>
                <span className="font-bold">{(breakdown.nli_max_contradiction * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-slate-800">
                <span>Latency:</span>
                <span className="font-mono">{breakdown.nli_latency_ms ?? 0} ms</span>
              </div>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
              <div className="font-semibold text-slate-700">Fusion Decision</div>
              <div className="text-slate-500 text-[11px]">Transparent Pipeline</div>
              <div className="pt-1 flex justify-between text-slate-800">
                <span>Verdict:</span>
                <span className="font-bold uppercase text-indigo-700">{breakdown.fusion_verdict}</span>
              </div>
              <div className="flex justify-between text-slate-800">
                <span>Rule Applied:</span>
                <span className="font-mono text-[10px] text-slate-600">{breakdown.fusion_source}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reference Evidence Used */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-3">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <FileText className="w-4 h-4 text-blue-600" />
          <span>Reference Context (Ground Truth Evidence)</span>
        </h3>
        <p className="text-xs text-slate-500">
          The hybrid detector verified the answer strictly against the following provided reference text:
        </p>
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {result.context.map((ctx, idx) => (
            <div
              key={idx}
              className="p-3 bg-slate-50 border border-slate-200/80 rounded-lg text-xs text-slate-800 leading-relaxed font-mono"
            >
              <div className="text-[10px] text-slate-500 uppercase font-semibold mb-1">
                Passage {idx + 1}:
              </div>
              {ctx}
            </div>
          ))}
        </div>
      </div>

      {/* Scientific & Operational Disclaimer */}
      <div className="bg-slate-100/80 border border-slate-200 rounded-xl p-4 text-xs text-slate-600 space-y-1">
        <div className="flex items-center gap-1.5 font-bold text-slate-800">
          <Info className="w-4 h-4 text-blue-600" />
          <span>Factual Grounding Scope</span>
        </div>
        <p className="leading-relaxed">
          {isHallucinated
            ? 'A flagged span indicates that the claim directly contradicts or is not grounded in the reference passages provided above.'
            : 'A SUPPORTED verdict confirms that the answer is fully consistent with the reference context supplied. Note that this guarantees grounding against your reference document, but does not substitute for broader universal factual validation.'}
        </p>
      </div>
    </div>
  );
};
