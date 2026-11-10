import React, { useState, useEffect } from 'react';
import {
  FileText,
  Upload,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Loader2,
  FileUp,
  Database,
  ArrowRight,
  Eye,
  X,
} from 'lucide-react';
import { api } from '../services/api';
import type { DocumentMetadata, DocumentDetail } from '../types/api';

interface DocumentsPageProps {
  onUseDocumentInVerify: (text: string) => void;
}

export const DocumentsPage: React.FC<DocumentsPageProps> = ({ onUseDocumentInVerify }) => {
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [isPersistent, setIsPersistent] = useState(false);
  const [storageNotice, setStorageNotice] = useState('');
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Detail Modal
  const [inspectDoc, setInspectDoc] = useState<DocumentDetail | null>(null);
  const [deleteDocConfirm, setDeleteDocConfirm] = useState<{ id: string; filename: string } | null>(null);

  const fetchDocuments = async () => {
    try {
      const data = await api.listDocuments();
      setDocuments(data.documents);
      setIsPersistent(data.is_persistent);
      setStorageNotice(data.storage_notice);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch documents.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    setSuccessMsg(null);

    // Validate extension
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'pdf' && ext !== 'txt') {
      setError(`Unsupported file type '.${ext}'. Please upload a PDF (.pdf) or Plain Text (.txt) file.`);
      e.target.value = '';
      return;
    }

    setUploading(true);
    try {
      const doc = await api.uploadDocument(file);
      setSuccessMsg(`Successfully ingested '${doc.filename}' (${doc.chunk_count} chunks extracted).`);
      await fetchDocuments();
    } catch (err: any) {
      setError(err.message || 'Failed to upload document.');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = (id: string, filename: string) => {
    setDeleteDocConfirm({ id, filename });
  };

  const executeDelete = async () => {
    if (!deleteDocConfirm) return;
    const { id, filename } = deleteDocConfirm;

    try {
      await api.deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
      setSuccessMsg(`Removed '${filename}'.`);
      if (inspectDoc?.id === id) setInspectDoc(null);
    } catch (err: any) {
      setError(`Failed to delete document: ${err.message}`);
    } finally {
      setDeleteDocConfirm(null);
    }
  };

  const handleInspect = async (id: string) => {
    try {
      const detail = await api.getDocument(id);
      setInspectDoc(detail);
    } catch (err: any) {
      setError(`Failed to load document text: ${err.message}`);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <FileText className="w-6 h-6 text-purple-600" />
          <span>Reference Document Management</span>
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Ingest PDFs and TXT files for automated text extraction and reference context verification.
        </p>
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
            {isPersistent ? 'Storage Engine: Supabase PostgreSQL' : 'Storage Engine: In-Memory (Session Mode)'}
          </span>
          <p className="leading-relaxed opacity-90">{storageNotice}</p>
        </div>
      </div>

      {/* Alert Messages */}
      {error && (
        <div className="p-3.5 rounded-lg bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {successMsg && (
        <div className="p-3.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Upload Zone Card */}
      <div className="bg-white border-2 border-dashed border-slate-300 hover:border-blue-400 rounded-2xl p-8 text-center transition-colors">
        <div className="max-w-md mx-auto space-y-3">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
            {uploading ? (
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            ) : (
              <Upload className="w-6 h-6" />
            )}
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800">
              {uploading ? 'Processing document with PyMuPDF...' : 'Upload Reference Document'}
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Supports <span className="font-semibold text-slate-700">PDF (.pdf)</span> or{' '}
              <span className="font-semibold text-slate-700">Plain Text (.txt)</span>
            </p>
          </div>

          <label className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition-colors cursor-pointer shadow-xs">
            <FileUp className="w-4 h-4" />
            <span>Select File from Computer</span>
            <input
              type="file"
              accept=".pdf,.txt,text/plain,application/pdf"
              disabled={uploading}
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Document List Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <span>Ingested Documents ({documents.length})</span>
          </h2>
          <span className="text-xs text-slate-400">Available as verification ground truth</span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
            <span>Loading document library...</span>
          </div>
        ) : documents.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs space-y-2">
            <FileText className="w-8 h-8 mx-auto text-slate-300" />
            <p>No documents uploaded yet.</p>
            <p className="text-[11px] text-slate-400">
              Upload a PDF report or TXT knowledge source to use as ground truth reference context.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/60 transition-colors"
              >
                <div className="flex items-start gap-3 min-w-0">
                  <div className="p-2.5 rounded-lg bg-slate-100 text-slate-600 shrink-0 mt-0.5">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-900 text-sm truncate max-w-sm">
                        {doc.filename}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                          doc.file_type.includes('pdf')
                            ? 'bg-red-50 text-red-700 border border-red-200'
                            : 'bg-blue-50 text-blue-700 border border-blue-200'
                        }`}
                      >
                        {doc.file_type.includes('pdf') ? 'PDF' : 'TXT'}
                      </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                      <span>Size: {formatFileSize(doc.file_size)}</span>
                      <span>•</span>
                      <span>Chunks: {doc.chunk_count}</span>
                      <span>•</span>
                      <span>
                        Uploaded: {new Date(doc.created_at).toLocaleDateString()}{' '}
                        {new Date(doc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-auto">
                  <button
                    onClick={() => handleInspect(doc.id)}
                    className="p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                    title="View extracted text & chunks"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>View</span>
                  </button>
                  <button
                    onClick={async () => {
                      const detail = await api.getDocument(doc.id);
                      onUseDocumentInVerify(detail.extracted_text);
                    }}
                    className="px-3 py-2 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 text-xs font-semibold flex items-center gap-1 transition-colors"
                  >
                    <span>Use in Verify</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => handleDelete(doc.id, doc.filename)}
                    className="p-2 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                    title="Delete document"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Inspect Document Modal */}
      {inspectDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-900 text-base">
                  {inspectDoc.filename}
                </h3>
                <span className="text-xs text-slate-500">
                  {inspectDoc.chunk_count} chunk(s) | {formatFileSize(inspectDoc.file_size)}
                </span>
              </div>
              <button
                onClick={() => setInspectDoc(null)}
                className="p-1 rounded-md text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 text-xs font-mono">
              <div>
                <div className="text-xs font-bold text-slate-700 uppercase font-sans mb-1">
                  Extracted Full Text:
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 max-h-48 overflow-y-auto whitespace-pre-wrap">
                  {inspectDoc.extracted_text}
                </div>
              </div>

              <div>
                <div className="text-xs font-bold text-slate-700 uppercase font-sans mb-1">
                  Generated Chunks ({inspectDoc.chunks.length}):
                </div>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {inspectDoc.chunks.map((chunk) => (
                    <div
                      key={chunk.chunk_index}
                      className="p-2.5 bg-slate-50 rounded border border-slate-200"
                    >
                      <div className="text-[10px] text-slate-400 font-sans mb-0.5">
                        Chunk #{chunk.chunk_index} (Offsets: {chunk.char_start} - {chunk.char_end})
                      </div>
                      <p className="text-slate-800 whitespace-pre-wrap">{chunk.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex justify-end gap-2">
              <button
                onClick={() => {
                  onUseDocumentInVerify(inspectDoc.extracted_text);
                  setInspectDoc(null);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-500"
              >
                Insert into Verify Page
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal (In-DOM replacement for window.confirm) */}
      {deleteDocConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-sm w-full p-6 space-y-4">
            <div className="flex items-center gap-3 text-red-600">
              <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                <Trash2 className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Remove Document?</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Are you sure you want to remove{' '}
              <span className="font-semibold text-slate-900">'{deleteDocConfirm.filename}'</span>? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setDeleteDocConfirm(null)}
                className="px-3.5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={executeDelete}
                className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-xs font-semibold transition-colors cursor-pointer"
              >
                Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
