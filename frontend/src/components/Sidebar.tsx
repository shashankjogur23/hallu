import React from 'react';
import {
  LayoutDashboard,
  CheckCircle,
  FileText,
  History,
  Info,
  ExternalLink,
} from 'lucide-react';

export type PageId = 'dashboard' | 'verify' | 'documents' | 'history' | 'about';

interface SidebarProps {
  currentPage: PageId;
  onSelectPage: (page: PageId) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentPage, onSelectPage }) => {
  const navItems: { id: PageId; label: string; icon: React.ReactNode; badge?: string }[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: <LayoutDashboard className="w-4 h-4" />,
    },
    {
      id: 'verify',
      label: 'Verify Answer',
      icon: <CheckCircle className="w-4 h-4" />,
      badge: 'Core',
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: <FileText className="w-4 h-4" />,
    },
    {
      id: 'history',
      label: 'Verification History',
      icon: <History className="w-4 h-4" />,
    },
    {
      id: 'about',
      label: 'About & Model',
      icon: <Info className="w-4 h-4" />,
    },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col justify-between shrink-0 border-r border-slate-800">
      <div className="p-4 space-y-6">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-3">
            Navigation
          </span>
          <nav className="mt-2 space-y-1">
            {navItems.map((item) => {
              const active = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectPage(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    active
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className={active ? 'text-white' : 'text-slate-400'}>
                      {item.icon}
                    </span>
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                        active
                          ? 'bg-blue-700 text-white'
                          : 'bg-blue-950/70 text-blue-300 border border-blue-800/60'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Engine Specification Card */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-3.5 text-xs space-y-2">
          <div className="font-semibold text-slate-200 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-blue-400" />
            Detector Architecture
          </div>
          <p className="text-slate-400 leading-relaxed text-[11px]">
            Powered by KRLabsOrg LettuceDetect ModernBERT fine-tuned for token-level factual grounding verifications.
          </p>
          <div className="pt-1 text-[11px] text-slate-400 border-t border-slate-700/50 flex justify-between">
            <span>Inference:</span>
            <span className="text-slate-200 font-mono">CPU (Local)</span>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800 text-[11px] text-slate-400 space-y-2">
        <div className="flex items-center justify-between">
          <span>Docs & Swagger</span>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1 text-blue-400 hover:text-blue-300 transition-colors"
          >
            <span>/docs</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
        <p className="text-slate-500 text-[10px]">
          HalluGuard Final-Year Project
        </p>
      </div>
    </aside>
  );
};

