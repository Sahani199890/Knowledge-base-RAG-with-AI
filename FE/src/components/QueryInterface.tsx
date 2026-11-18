import React, { useState } from 'react';
import { Search, Sparkles, Loader2, SlidersHorizontal, CornerDownLeft } from './Icons';

interface QueryInterfaceProps {
  onQuery: (question: string, topK: number) => Promise<void>;
  loading: boolean;
  disabled: boolean;
}

const EXAMPLE_PROMPTS = [
  "What are the main topics in my saved notes?",
  "Explain the key concepts and ideas mentioned.",
  "What is the significance of the saved content?",
];

export const QueryInterface: React.FC<QueryInterfaceProps> = ({ onQuery, loading, disabled }) => {
  const [question, setQuestion] = useState('');
  const [topK, setTopK] = useState(3);
  const [showOptions, setShowOptions] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanQ = question.trim();
    if (!cleanQ || loading || disabled) return;
    onQuery(cleanQ, topK);
  };

  const handleSuggestionClick = (prompt: string) => {
    setQuestion(prompt);
    onQuery(prompt, topK);
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-5 transition-all">
      {/* Title */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-blue-100 text-blue-700">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">Ask Your Knowledge Inbox</h2>
            <p className="text-xs text-slate-500">Semantic search + RAG generation over retrieved chunks</p>
          </div>
        </div>

        {/* Options toggle */}
        <button
          type="button"
          onClick={() => setShowOptions(!showOptions)}
          className="flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-800 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          title="Retrieval settings"
        >
          <SlidersHorizontal className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">k={topK}</span>
        </button>
      </div>

      {/* Options Panel (Collapsible) */}
      {showOptions && (
        <div className="mb-3 p-3 bg-slate-50 border border-slate-200/80 rounded-xl text-xs flex items-center justify-between">
          <label className="text-slate-700 font-medium">Top-K Chunks to Retrieve:</label>
          <div className="flex items-center space-x-2">
            {[2, 3, 5, 8].map((num) => (
              <button
                key={num}
                type="button"
                onClick={() => setTopK(num)}
                className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-all ${
                  topK === num
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
                }`}
              >
                {num}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Query Form */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center">
          <input
            type="text"
            placeholder={
              disabled
                ? "Add at least one note or URL first to query your inbox..."
                : "Ask any question about your saved notes or URLs..."
            }
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={disabled || loading}
            className="w-full text-xs sm:text-sm pl-4 pr-24 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all placeholder:text-slate-400 bg-slate-50/50 focus:bg-white"
          />

          <button
            type="submit"
            disabled={disabled || loading || !question.trim()}
            className="absolute right-2 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium flex items-center space-x-1.5 shadow-sm transition-all disabled:opacity-40 disabled:pointer-events-none"
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span className="hidden sm:inline">Searching...</span>
              </>
            ) : (
              <>
                <Search className="w-3.5 h-3.5" />
                <span>Ask</span>
                <CornerDownLeft className="w-3 h-3 text-blue-200 hidden sm:inline" />
              </>
            )}
          </button>
        </div>
      </form>

      {/* Suggestion Chips */}
      {!disabled && (
        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] text-slate-400 mr-1">Suggestions:</span>
          {EXAMPLE_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              type="button"
              disabled={loading}
              onClick={() => handleSuggestionClick(prompt)}
              className="text-[11px] px-2.5 py-1 rounded-full bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-600 border border-slate-200/60 transition-all"
            >
              {prompt}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
