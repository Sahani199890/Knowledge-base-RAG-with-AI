import React, { useState } from 'react';
import { FileText, Globe, Trash2, Search, ExternalLink, Calendar, Layers, ChevronDown, ChevronUp } from './Icons';
import { KnowledgeItem } from '../types';

interface ItemListProps {
  items: KnowledgeItem[];
  loading: boolean;
  onDelete: (id: string) => Promise<void>;
}

export const ItemList: React.FC<ItemListProps> = ({ items, loading, onDelete }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const filteredItems = (items || []).filter((item) => {
    if (!item) return false;
    const q = (searchTerm || '').toLowerCase();
    const title = (item.title || '').toLowerCase();
    const content = (item.content || '').toLowerCase();
    const url = (item.url || '').toLowerCase();
    return title.includes(q) || content.includes(q) || url.includes(q);
  });

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this item and its vector chunks?')) {
      return;
    }
    setDeletingId(id);
    try {
      await onDelete(id);
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-5 flex flex-col h-full">
      {/* Header & Search */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="text-base font-semibold text-slate-900 flex items-center space-x-2">
            <span>Saved Knowledge Items</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">
              {items.length}
            </span>
          </h2>
          <p className="text-xs text-slate-500">Indexed notes and server-fetched URLs</p>
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-56">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search saved items..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full text-xs pl-8 pr-3 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 placeholder:text-slate-400"
          />
        </div>
      </div>

      {/* Items Container */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1 max-h-[500px]">
        {loading && items.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">Loading saved items...</div>
        ) : filteredItems.length === 0 ? (
          <div className="py-12 text-center border-2 border-dashed border-slate-100 rounded-xl">
            <FileText className="w-8 h-8 mx-auto text-slate-300 mb-2" />
            <p className="text-xs font-medium text-slate-500">
              {searchTerm ? 'No items match your search' : 'No saved items yet'}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {searchTerm ? 'Try a different keyword' : 'Add a note or URL on the left to begin building your knowledge inbox.'}
            </p>
          </div>
        ) : (
          filteredItems.map((item) => {
            const isExpanded = expandedId === item.id;
            const isDeleting = deletingId === item.id;

            return (
              <div
                key={item.id}
                onClick={() => setExpandedId(isExpanded ? null : item.id)}
                className={`group border rounded-xl p-3.5 transition-all cursor-pointer ${
                  isExpanded
                    ? 'border-blue-300 bg-blue-50/20 shadow-sm'
                    : 'border-slate-200/90 hover:border-slate-300 hover:bg-slate-50/50'
                }`}
              >
                {/* Top Row: Type Badge + Title + Actions */}
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start space-x-2.5 min-w-0">
                    <span
                      className={`p-1.5 rounded-lg shrink-0 ${
                        item.type === 'url'
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-indigo-100 text-indigo-700'
                      }`}
                    >
                      {item.type === 'url' ? <Globe className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
                    </span>

                    <div className="min-w-0">
                      <h3 className="text-xs font-semibold text-slate-900 truncate group-hover:text-blue-600 transition-colors">
                        {item.title}
                      </h3>

                      {item.url && (
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center space-x-1 text-[11px] text-blue-600 hover:underline truncate max-w-xs mt-0.5"
                        >
                          <span className="truncate">{item.url}</span>
                          <ExternalLink className="w-3 h-3 shrink-0" />
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Delete Button */}
                  <div className="flex items-center space-x-1 shrink-0">
                    <button
                      type="button"
                      onClick={(e) => handleDelete(item.id, e)}
                      disabled={isDeleting}
                      title="Delete item and vector chunks"
                      className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Metadata & Preview snippet */}
                <div className="mt-2.5">
                  <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
                    {item.content}
                  </p>

                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t border-slate-200/70 text-xs text-slate-700 whitespace-pre-wrap font-sans bg-white p-3 rounded-lg border border-slate-100">
                      <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                        Full Content ({item.content.length} characters)
                      </p>
                      {item.content}
                    </div>
                  )}

                  {/* Bottom Stats: Chunks & Date */}
                  <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-slate-100 text-[11px] text-slate-400">
                    <div className="flex items-center space-x-3">
                      <span className="inline-flex items-center space-x-1 text-slate-600 font-medium">
                        <Layers className="w-3 h-3 text-blue-500" />
                        <span>{item.chunk_count} {item.chunk_count === 1 ? 'chunk' : 'chunks'}</span>
                      </span>

                      <span className="inline-flex items-center space-x-1">
                        <Calendar className="w-3 h-3 text-slate-400" />
                        <span>{formatDate(item.created_at)}</span>
                      </span>
                    </div>

                    <div className="text-slate-400 hover:text-slate-600 flex items-center space-x-1">
                      <span>{isExpanded ? 'Collapse' : 'Expand'}</span>
                      {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
