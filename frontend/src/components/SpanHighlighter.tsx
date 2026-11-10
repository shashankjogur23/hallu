import React from 'react';
import type { HallucinationSpan } from '../types/api';
import { AlertOctagon, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface SpanHighlighterProps {
  answer: string;
  spans: HallucinationSpan[];
}

export const SpanHighlighter: React.FC<SpanHighlighterProps> = ({ answer, spans }) => {
  if (!spans || spans.length === 0) {
    return (
      <div className="bg-emerald-50/60 border border-emerald-200 rounded-lg p-5">
        <div className="flex items-center gap-2 text-emerald-800 text-sm font-semibold mb-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>No Hallucinated or Contradictory Spans Detected</span>
        </div>
        <p className="text-slate-800 text-base leading-relaxed font-normal whitespace-pre-wrap">
          {answer}
        </p>
      </div>
    );
  }

  // Sort spans by start offset ascending
  const sortedSpans = [...spans].sort((a, b) => a.start - b.start);

  const segments: React.ReactNode[] = [];
  let lastIndex = 0;

  sortedSpans.forEach((span, idx) => {
    // Bounds checking
    const spanStart = Math.max(0, Math.min(span.start, answer.length));
    const spanEnd = Math.max(spanStart, Math.min(span.end, answer.length));

    // Text before the span
    if (spanStart > lastIndex) {
      segments.push(
        <span key={`text-${lastIndex}`}>
          {answer.slice(lastIndex, spanStart)}
        </span>
      );
    }

    // Determine category styling
    const isContradiction = span.category?.toLowerCase() === 'contradiction';
    const highlightClass = isContradiction ? 'span-contradicted' : 'span-unsupported';
    const badgeClass = isContradiction
      ? 'text-red-700 bg-red-100/90 border-red-300'
      : 'text-amber-800 bg-amber-100/90 border-amber-300';

    const spanText = answer.slice(spanStart, spanEnd);
    const confidencePct =
      span.confidence !== null && span.confidence !== undefined
        ? `${(span.confidence * 100).toFixed(1)}%`
        : 'N/A';

    segments.push(
      <span
        key={`span-${idx}`}
        className={`relative inline-block mx-0.5 ${highlightClass} group cursor-help`}
        title={`Flagged as ${span.category || 'hallucination'} (Confidence: ${confidencePct})`}
      >
        <span>{spanText}</span>
        <span
          className={`inline-flex items-center gap-0.5 ml-1 px-1.5 py-0.2 text-[10px] font-semibold rounded border ${badgeClass}`}
        >
          {isContradiction ? (
            <AlertOctagon className="w-2.5 h-2.5 inline text-red-600" />
          ) : (
            <AlertTriangle className="w-2.5 h-2.5 inline text-amber-600" />
          )}
          <span>{isContradiction ? 'Contradiction' : 'Unsupported'} ({confidencePct})</span>
        </span>
      </span>
    );

    lastIndex = spanEnd;
  });

  // Remaining text after last span
  if (lastIndex < answer.length) {
    segments.push(
      <span key={`text-${lastIndex}`}>
        {answer.slice(lastIndex)}
      </span>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
      <div className="text-slate-800 text-base leading-relaxed whitespace-pre-wrap">
        {segments}
      </div>
    </div>
  );
};
