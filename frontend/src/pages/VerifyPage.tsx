import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  FileText,
  HelpCircle,
  Sparkles,
  AlertCircle,
  Loader2,
  Sliders,
} from 'lucide-react';
import { api } from '../services/api';
import type {
  VerificationRequest,
  VerificationResponse,
  DocumentMetadata,
} from '../types/api';
import { ResultsView } from '../components/ResultsView';

interface VerifyPageProps {
  initialData?: {
    question?: string;
    answer?: string;
    context?: string;
  };
}

export const VerifyPage: React.FC<VerifyPageProps> = ({ initialData }) => {
  const [question, setQuestion] = useState(initialData?.question || '');
  const [answer, setAnswer] = useState(initialData?.answer || '');
  const [context, setContext] = useState(initialData?.context || '');
  const [minConfidence, setMinConfidence] = useState(0.0);

  const [availableDocs, setAvailableDocs] = useState<DocumentMetadata[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('');

  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VerificationResponse | null>(null);

  // Load available documents for selection
  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const data = await api.listDocuments();
        setAvailableDocs(data.documents);
      } catch (err) {
        console.warn('Could not fetch documents:', err);
      }
    };
    fetchDocs();
  }, []);

  // Sync initialData if provided from dashboard navigation
  useEffect(() => {
    if (initialData) {
      if (initialData.question) setQuestion(initialData.question);
      if (initialData.answer) setAnswer(initialData.answer);
      if (initialData.context) setContext(initialData.context);
    }
  }, [initialData]);

  // Handle document dropdown selection
  const handleSelectDocument = async (docId: string) => {
    setSelectedDocId(docId);
    if (!docId) return;

    try {
      const docDetail = await api.getDocument(docId);
      setContext(docDetail.extracted_text);
    } catch (err: any) {
      setError(`Failed to load document text: ${err.message}`);
    }
  };

  // Preload France hallucinated demo
  const loadFranceHallucinatedDemo = () => {
    setContext(
      'France is a country in Europe. The capital of France is Paris. The population of France is 67 million.'
    );
    setQuestion('What is the capital of France and its population?');
    setAnswer(
      'The capital of France is Paris. The population of France is 69 million.'
    );
    setError(null);
    setResult(null);
  };

  // Preload France supported demo
  const loadFranceSupportedDemo = () => {
    setContext(
      'France is a country in Europe. The capital of France is Paris. The population of France is 67 million.'
    );
    setQuestion('What is the capital of France and its population?');
    setAnswer(
      'The capital of France is Paris. The population of France is 67 million.'
    );
    setError(null);
    setResult(null);
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!answer.trim()) {
      setError('Please provide an answer to verify.');
      return;
    }

    if (!context.trim()) {
      setError('Please provide reference context or select an uploaded document.');
      return;
    }

    setIsVerifying(true);
    try {
      const payload: VerificationRequest = {
        question: question.trim() ? question.trim() : null,
        answer: answer.trim(),
        context: [context.trim()],
        min_confidence: minConfidence > 0 ? minConfidence : 0.0,
      };

      const response = await api.verifyAnswer(payload);
      setResult(response);
    } catch (err: any) {
      setError(err.message || 'Verification failed. Please check backend connection.');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
  };

  // If a result is available, render the ResultsView
  if (result) {
    return <ResultsView result={result} onReset={handleReset} />;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-blue-600" />
            <span>Verify AI Generated Answer</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Check factual consistency against source passages using LettuceDetect ModernBERT.
          </p>
        </div>

        {/* Quick Demo Preload Buttons */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={loadFranceHallucinatedDemo}
            className="text-xs font-semibold px-2.5 py-1.5 rounded-md bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 transition-colors"
            title="Preload France population 69M claim (Hallucinated)"
          >
            Preload Flagged Demo
          </button>
          <button
            type="button"
            onClick={loadFranceSupportedDemo}
            className="text-xs font-semibold px-2.5 py-1.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition-colors"
            title="Preload France population 67M claim (Clean)"
          >
            Preload Clean Demo
          </button>
        </div>
      </div>

      {/* Error Alert Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm flex items-start gap-3 shadow-xs">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold">Verification Error</span>
            <p className="text-xs text-red-700 leading-relaxed">{error}</p>
          </div>
        </div>
      )}

      {/* Verification Form */}
      <form onSubmit={handleVerify} className="space-y-6">
        {/* Question Field */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
              <HelpCircle className="w-3.5 h-3.5 text-blue-600" />
              <span>Question or Prompt (Optional)</span>
            </label>
            <span className="text-[11px] text-slate-400">
              Leave blank for summary verification
            </span>
          </div>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. What is the capital of France and its population?"
            className="w-full text-sm px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 bg-slate-50/50"
          />
        </div>

        {/* Reference Context Field */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-blue-600" />
              <span>Ground Truth Reference Context</span>
              <span className="text-red-500">*</span>
            </label>

            {/* Document selector dropdown */}
            {availableDocs.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-slate-500">Insert from Doc:</span>
                <select
                  value={selectedDocId}
                  onChange={(e) => handleSelectDocument(e.target.value)}
                  className="text-xs px-2.5 py-1 rounded-md border border-slate-200 bg-white text-slate-700 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">-- Choose uploaded document --</option>
                  {availableDocs.map((doc) => (
                    <option key={doc.id} value={doc.id}>
                      {doc.filename} ({doc.chunk_count} chunks)
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <textarea
            value={context}
            onChange={(e) => setContext(e.target.value)}
            rows={4}
            required
            placeholder="Paste source text, article excerpt, or reference passages against which the answer will be grounded..."
            className="w-full text-sm px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 bg-slate-50/50 font-mono text-xs leading-relaxed"
          />
          <div className="flex justify-between text-[11px] text-slate-400">
            <span>Character count: {context.length}</span>
            <span>Used by ModernBERT as factual ground truth</span>
          </div>
        </div>

        {/* AI Answer Textarea */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              <span>AI-Generated Answer to Verify</span>
              <span className="text-red-500">*</span>
            </label>
            <span className="text-[11px] text-slate-400">
              Paste from ChatGPT, Gemini, Claude, or any LLM
            </span>
          </div>
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            rows={5}
            required
            placeholder="Paste the generated text here to verify for unsupported statements, contradictory numbers, or fabricated facts..."
            className="w-full text-sm px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 bg-slate-50/50 leading-relaxed"
          />
          <div className="flex justify-between text-[11px] text-slate-400">
            <span>Character count: {answer.length}</span>
            <span>No external LLM API key required</span>
          </div>
        </div>

        {/* Advanced Filter: Confidence Threshold */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-slate-500" />
            <div>
              <div className="text-xs font-bold text-slate-800">
                Minimum Confidence Threshold
              </div>
              <p className="text-[11px] text-slate-400">
                Filter out hallucinated spans below this probability (default 0.0 keeps all).
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="range"
              min="0.0"
              max="0.95"
              step="0.05"
              value={minConfidence}
              onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
              className="w-32 accent-blue-600 cursor-pointer"
            />
            <span className="text-xs font-mono font-bold text-slate-700 w-12 text-right">
              {(minConfidence * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={() => {
              setQuestion('');
              setAnswer('');
              setContext('');
              setError(null);
            }}
            className="px-4 py-2.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 text-sm font-semibold transition-colors"
          >
            Clear Fields
          </button>

          <button
            type="submit"
            disabled={isVerifying}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-blue-400 text-white font-semibold text-sm shadow-xs transition-colors cursor-pointer"
          >
            {isVerifying ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Analyzing with LettuceDetect...</span>
              </>
            ) : (
              <>
                <ShieldCheck className="w-4 h-4" />
                <span>Verify Answer</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
