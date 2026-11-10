import React, { useState, useEffect } from 'react';
import {
  History,
  Clock,
  Database,
  Eye,
  AlertTriangle,
  RotateCcw,
  Loader2,
  X,
} from 'lucide-react';
import { api } from '../services/api';
import type { VerificationHistoryItem } from '../types/api';
import { SpanHighlighter } from '../components/SpanHighlighter';

export const HistoryPage: React.FC = () => {
  const [history, setHistory] = useState<VerificationHistoryItem[]>([]);
  const [isPersistent, setIsPersistent] = useState(false);
  const [storageNotice, setStorageNotice] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected item for modal inspect
  const [selectedItem, setSelectedItem] = useState<VerificationHistoryItem | null>(null);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await api.getVerificationHistory(50);
      setHistory(data.verifications);
      setIsPersistent(data.is_persistent);
      setStorageNotice(data.storage_notice);
    } catch (err: any) {
      setError(err.message || 'Failed to load verification history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <History className="w-6 h-6 text-indigo-600" />
            <span>Verification Audit History</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Log of factual grounding verifications executed by the LettuceDetect engine.
          </p>
        </div>

        <button
          onClick={fetchHistory}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 shadow-2xs"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Storage Status Banner */}
      <div
        className={`p-4 rounded-xl border text-xs flex items-start gap-3 ${
          isPersistent
            ? 'bg-blue-50/70 border-blue-200 text-blue-900'
            : 'bg-amber-50/70 border-amber-200 text-amber-900'
        }`}
      >
        <Database className={`w-4 h-4 shrink-0 mt-0.5 ${isPersistent ? 'text-blue-600' : 'text-amber-600'}`} />
        <div className="space-y-0.5">
          <span className="font-bold">
            {isPersistent ? 'Persistence: Supabase PostgreSQL' : 'Persistence: Local Session Memory Only'}
          </span>
          <p className="leading-relaxed opacity-90">{storageNotice}</p>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* History Table Card */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900">
            Recorded Verifications ({history.length})
          </h2>
          <span className="text-xs text-slate-400">Strictly displays real verification records</span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-600" />
            <span>Fetching verification records...</span>
          </div>
        ) : history.length === 0 ? (
          <div className="p-16 text-center text-slate-400 text-xs space-y-2">
            <Clock className="w-8 h-8 mx-auto text-slate-300" />
            <p className="font-medium text-slate-600">No verifications in history yet.</p>
            <p className="text-[11px] text-slate-400 max-w-sm mx-auto">
              {isPersistent
                ? 'No past verifications found in Supabase database.'
                : 'Since Supabase is not configured, history is held in-memory for the running session and resets when the backend server is restarted.'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {history.map((item) => (
              <div
                key={item.id}
                className="px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/60 transition-colors"
              >
                <div className="space-y-1.5 min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                        item.summary.is_hallucinated
                          ? 'bg-red-100 text-red-800 border border-red-200'
                          : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                      }`}
                    >
                      {item.summary.verdict}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      #{item.id.slice(0, 8)}
                    </span>
                    {item.question && (
                      <span className="text-xs font-semibold text-slate-800 truncate max-w-md">
                        Q: {item.question}
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-slate-600 line-clamp-1 italic font-normal">
                    "{item.answer}"
                  </p>

                  <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400">
                    <span>Flagged Spans: {item.summary.span_count}</span>
                    <span>•</span>
                    <span>
                      Confidence:{' '}
                      {item.summary.max_confidence !== null
                        ? `${(item.summary.max_confidence * 100).toFixed(1)}%`
                        : 'N/A'}
                    </span>
                    <span>•</span>
                    <span>Latency: {item.execution_time_ms} ms</span>
                    <span>•</span>
                    <span>
                      {new Date(item.created_at).toLocaleDateString()}{' '}
                      {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>

                <button
                  onClick={() => setSelectedItem(item)}
                  className="self-end sm:self-auto inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-100 text-xs font-semibold transition-colors"
                >
                  <Eye className="w-3.5 h-3.5 text-slate-500" />
                  <span>Inspect</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detail Inspection Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                      selectedItem.summary.is_hallucinated
                        ? 'bg-red-100 text-red-800'
                        : 'bg-emerald-100 text-emerald-800'
                    }`}
                  >
                    {selectedItem.summary.verdict}
                  </span>
                  <h3 className="font-bold text-slate-900 text-base">
                    Verification #{selectedItem.id.slice(0, 8)}
                  </h3>
                </div>
                <span className="text-xs text-slate-400">
                  {new Date(selectedItem.created_at).toLocaleString()} • {selectedItem.model.split('/').pop()} • {selectedItem.execution_time_ms} ms
                </span>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="p-1 rounded-md text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-5 text-xs">
              {selectedItem.question && (
                <div>
                  <span className="font-bold text-slate-700 block mb-1">Question:</span>
                  <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-slate-800">
                    {selectedItem.question}
                  </div>
                </div>
              )}

              <div>
                <span className="font-bold text-slate-700 block mb-1">Answer with Spans:</span>
                <SpanHighlighter answer={selectedItem.answer} spans={selectedItem.spans} />
              </div>

              <div>
                <span className="font-bold text-slate-700 block mb-1">
                  Ground Truth Context Passages ({selectedItem.context.length}):
                </span>
                <div className="space-y-2 max-h-40 overflow-y-auto font-mono text-[11px]">
                  {selectedItem.context.map((ctx, idx) => (
                    <div key={idx} className="p-2.5 bg-slate-50 rounded border border-slate-200 text-slate-800">
                      {ctx}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setSelectedItem(null)}
                className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 rounded-lg text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
