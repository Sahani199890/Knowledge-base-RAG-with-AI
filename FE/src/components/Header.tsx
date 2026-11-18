import React from 'react';
import { Cpu, Layers } from './Icons';
import { SystemHealth } from '../types';

interface HeaderProps {
  health: SystemHealth | null;
  loading?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ health }) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
        
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-700 via-indigo-600 to-sky-500 flex items-center justify-center shadow-md shadow-blue-500/20 text-white font-bold text-lg tracking-wider">
            T
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">Turium AI</h1>
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-blue-100 text-blue-700">
                Knowledge Inbox
              </span>
            </div>
            <p className="text-xs text-slate-500">RAG Pipeline with LangChain & Unstructured Text Splitter</p>
          </div>
        </div>

        {/* Telemetry Pills */}
        <div className="flex items-center space-x-3 text-xs">
          {/* Model / Embedding Info */}
          {health && (
            <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-slate-700">
              <Cpu className="w-3.5 h-3.5 text-indigo-600" />
              <span className="font-medium truncate max-w-[190px]" title={health.embedding_provider}>
                {health.embedding_provider}
              </span>
            </div>
          )}

          {/* Chunks Count */}
          {health && (
            <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-slate-700">
              <Layers className="w-3.5 h-3.5 text-blue-600" />
              <span>
                <strong className="text-slate-900 font-semibold">{health.total_chunks}</strong> chunks
              </span>
            </div>
          )}
        </div>

      </div>
    </header>
  );
};
