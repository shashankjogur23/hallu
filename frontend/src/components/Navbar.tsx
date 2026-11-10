import React, { useEffect, useState } from 'react';
import { ShieldCheck, Cpu, Database, AlertCircle, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import type { HealthResponse } from '../types/api';

interface NavbarProps {
  onToggleSidebar?: () => void;
}

export const Navbar: React.FC<NavbarProps> = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async () => {
    setIsChecking(true);
    try {
      const data = await api.getHealth();
      setHealth(data);
      setError(null);
    } catch (err: any) {
      setHealth(null);
      setError(err.message || 'Offline');
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    checkHealth();
    // Poll every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-xs border-b border-slate-200 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-linear-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-xs">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-900 text-lg tracking-tight">HalluGuard</span>
            <span className="text-[11px] font-semibold uppercase px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
              v1.0
            </span>
          </div>
          <p className="text-xs text-slate-500 font-medium hidden sm:block">
            Hallucination Detection Framework for Generative AI
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Detector Engine Status */}
        {health?.detector_loaded ? (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <Cpu className="w-3.5 h-3.5 text-emerald-600" />
            <span className="hidden md:inline">ModernBERT Ready (CPU)</span>
            <span className="md:hidden">Model Ready</span>
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-red-50 border border-red-200 text-red-800 text-xs font-medium">
            <AlertCircle className="w-3.5 h-3.5 text-red-600" />
            <span className="hidden md:inline">Backend Offline</span>
            <span className="md:hidden">Offline</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-amber-50 border border-amber-200 text-amber-800 text-xs font-medium">
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
            <span>Connecting...</span>
          </div>
        )}

        {/* Database Status */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-50 border border-slate-200 text-slate-700 text-xs font-medium">
          <Database className="w-3.5 h-3.5 text-slate-500" />
          <span>{health?.supabase_configured ? 'Supabase Active' : 'Session Memory'}</span>
        </div>

        {/* Refresh Status Button */}
        <button
          onClick={checkHealth}
          disabled={isChecking}
          title="Refresh Backend Status"
          className="p-1.5 rounded-md text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${isChecking ? 'animate-spin text-blue-600' : ''}`} />
        </button>
      </div>
    </header>
  );
};
