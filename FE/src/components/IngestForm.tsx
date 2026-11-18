import React, { useState } from 'react';
import { FileText, Globe, Plus, Loader2, SlidersHorizontal, ChevronDown, ChevronUp } from './Icons';
import { SourceType, IngestItemRequest } from '../types';

interface IngestFormProps {
  onIngest: (payload: IngestItemRequest) => Promise<void>;
  loading: boolean;
}

export const IngestForm: React.FC<IngestFormProps> = ({ onIngest, loading }) => {
  const [activeTab, setActiveTab] = useState<SourceType>('note');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [chunkSize, setChunkSize] = useState<number>(500);
  const [chunkOverlap, setChunkOverlap] = useState<number>(80);
  const [showChunkSettings, setShowChunkSettings] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedContent = content.trim();
    if (!trimmedContent) {
      setError(activeTab === 'note' ? 'Please enter note content.' : 'Please enter a valid URL.');
      return;
    }

    if (activeTab === 'url') {
      try {
        const parsed = new URL(trimmedContent);
        if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
          setError('URL must begin with http:// or https://');
          return;
        }
      } catch {
        setError('Please enter a valid, well-formed web URL.');
        return;
      }
    }

    try {
      await onIngest({
        type: activeTab,
        content: trimmedContent,
        title: title.trim() || undefined,
        chunk_size: chunkSize,
        chunk_overlap: chunkOverlap,
      });

      // Reset form
      setContent('');
      setTitle('');
    } catch (err: any) {
      setError(err.message || 'Failed to ingest content.');
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-5 transition-all">
      {/* Title */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-slate-900 flex items-center space-x-2">
          <span>Ingest Knowledge</span>
          <span className="text-[11px] font-normal px-2 py-0.5 rounded bg-slate-100 text-slate-600">
            Auto-chunked
          </span>
        </h2>
      </div>

      {/* Tab Switcher */}
      <div className="grid grid-cols-2 gap-1.5 p-1 bg-slate-100 rounded-xl mb-4 text-xs font-medium">
        <button
          type="button"
          onClick={() => { setActiveTab('note'); setError(null); }}
          className={`flex items-center justify-center space-x-2 py-2 rounded-lg transition-all ${
            activeTab === 'note'
              ? 'bg-white text-blue-700 font-semibold shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Quick Note</span>
        </button>

        <button
          type="button"
          onClick={() => { setActiveTab('url'); setError(null); }}
          className={`flex items-center justify-center space-x-2 py-2 rounded-lg transition-all ${
            activeTab === 'url'
              ? 'bg-white text-blue-700 font-semibold shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Globe className="w-4 h-4" />
          <span>Web URL</span>
        </button>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-3.5">
        {/* Title Input */}
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            Title <span className="text-slate-400 font-normal">(Optional)</span>
          </label>
          <input
            type="text"
            placeholder={activeTab === 'note' ? "e.g. Apollo Program Notes" : "e.g. LangChain Documentation"}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={loading}
            className="w-full text-xs px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all placeholder:text-slate-400"
          />
        </div>

        {/* Content / URL Input */}
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            {activeTab === 'note' ? 'Note Content (Plain Text)' : 'Target Web URL'}
          </label>
          {activeTab === 'note' ? (
            <textarea
              rows={4}
              placeholder="Paste or write notes, concepts, summaries, or unstructured information here..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              disabled={loading}
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all placeholder:text-slate-400 font-sans resize-y"
            />
          ) : (
            <input
              type="url"
              placeholder="https://example.com/article"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              disabled={loading}
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all placeholder:text-slate-400"
            />
          )}
          {activeTab === 'url' && (
            <p className="text-[11px] text-slate-500 mt-1">
              Backend fetches HTML server-side, strips boilerplate, and chunks via Unstructured splitter.
            </p>
          )}
        </div>

        {/* Chunking Settings Accordion */}
        <div className="border border-slate-200/90 rounded-xl overflow-hidden bg-slate-50/50">
          <button
            type="button"
            onClick={() => setShowChunkSettings(!showChunkSettings)}
            className="w-full flex items-center justify-between px-3 py-2 text-xs text-slate-700 hover:bg-slate-100/70 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <SlidersHorizontal className="w-3.5 h-3.5 text-blue-600" />
              <span className="font-medium text-slate-800">Chunking Strategy:</span>
              <span className="px-1.5 py-0.5 rounded bg-blue-100/80 text-blue-700 font-mono text-[11px] font-semibold">
                {chunkSize} chars / {chunkOverlap} overlap
              </span>
            </div>
            {showChunkSettings ? <ChevronUp className="w-3.5 h-3.5 text-slate-400" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-400" />}
          </button>

          {showChunkSettings && (
            <div className="p-3 border-t border-slate-200 bg-white space-y-3">
              {/* Presets */}
              <div>
                <label className="block text-[11px] font-medium text-slate-500 mb-1.5 uppercase tracking-wider">
                  Quick Presets
                </label>
                <div className="grid grid-cols-3 gap-1.5">
                  {[
                    { label: 'Compact', size: 250, overlap: 40 },
                    { label: 'Standard', size: 500, overlap: 80 },
                    { label: 'Large', size: 1000, overlap: 150 },
                  ].map((p) => {
                    const active = chunkSize === p.size && chunkOverlap === p.overlap;
                    return (
                      <button
                        key={p.label}
                        type="button"
                        onClick={() => {
                          setChunkSize(p.size);
                          setChunkOverlap(p.overlap);
                        }}
                        className={`py-1.5 px-2 rounded-lg text-xs font-medium border transition-all text-center ${
                          active
                            ? 'bg-blue-50 border-blue-400 text-blue-700 font-semibold shadow-xs'
                            : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        <div>{p.label}</div>
                        <div className="text-[10px] text-slate-400">{p.size} / {p.overlap}</div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Sliders */}
              <div className="space-y-2.5 pt-1">
                <div>
                  <div className="flex justify-between text-xs text-slate-700 mb-1">
                    <span>Chunk Size:</span>
                    <span className="font-mono font-semibold text-blue-600">{chunkSize} characters</span>
                  </div>
                  <input
                    type="range"
                    min="100"
                    max="2000"
                    step="50"
                    value={chunkSize}
                    onChange={(e) => {
                      const val = parseInt(e.target.value, 10);
                      setChunkSize(val);
                      if (chunkOverlap >= val) {
                        setChunkOverlap(Math.floor(val / 4));
                      }
                    }}
                    className="w-full accent-blue-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-400 mt-0.5 font-mono">
                    <span>100 chars</span>
                    <span>500 (Default)</span>
                    <span>2000 chars</span>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs text-slate-700 mb-1">
                    <span>Chunk Overlap:</span>
                    <span className="font-mono font-semibold text-blue-600">
                      {chunkOverlap} characters ({Math.round((chunkOverlap / chunkSize) * 100)}%)
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max={Math.min(500, Math.floor(chunkSize * 0.5))}
                    step="10"
                    value={chunkOverlap}
                    onChange={(e) => setChunkOverlap(parseInt(e.target.value, 10))}
                    className="w-full accent-blue-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-400 mt-0.5 font-mono">
                    <span>0 chars</span>
                    <span>80 (Default)</span>
                    <span>{Math.min(500, Math.floor(chunkSize * 0.5))} chars</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Error message */}
        {error && (
          <div className="text-xs text-rose-600 bg-rose-50 border border-rose-200 rounded-lg p-2.5">
            {error}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading || !content.trim()}
          className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs shadow-sm hover:shadow transition-all disabled:opacity-50 disabled:pointer-events-none"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Processing & Chunking...</span>
            </>
          ) : (
            <>
              <Plus className="w-4 h-4" />
              <span>{activeTab === 'note' ? 'Save Note & Index Chunks' : 'Fetch & Index URL'}</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};
