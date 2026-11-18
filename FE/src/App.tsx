import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Header } from './components/Header';
import { IngestForm } from './components/IngestForm';
import { ItemList } from './components/ItemList';
import { QueryInterface } from './components/QueryInterface';
import { AnswerDisplay } from './components/AnswerDisplay';
import { checkHealth, fetchItems, ingestContent, deleteItem, submitQuery } from './api';
import { KnowledgeItem, QueryResponse, SystemHealth, IngestItemRequest } from './types';
import { AlertCircle, CheckCircle2, X } from './components/Icons';

export const App: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);

  const [loadingItems, setLoadingItems] = useState(true);
  const [loadingIngest, setLoadingIngest] = useState(false);
  const [loadingQuery, setLoadingQuery] = useState(false);

  // Toast notification with memory leak prevention
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const toastTimerRef = useRef<number | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      if (toastTimerRef.current) {
        clearTimeout(toastTimerRef.current);
      }
    };
  }, []);

  const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    if (toastTimerRef.current) {
      clearTimeout(toastTimerRef.current);
    }
    setToast({ message, type });
    toastTimerRef.current = window.setTimeout(() => {
      if (isMountedRef.current) {
        setToast(null);
      }
    }, 4000);
  }, []);

  const loadData = useCallback(async () => {
    // 1. Fetch health independently for immediate status detection (<10ms)
    checkHealth()
      .then((h) => {
        if (isMountedRef.current) setHealth(h);
      })
      .catch(() => {
        if (isMountedRef.current) {
          // Keep previous health if items are present
          setHealth((prev) => (prev ? prev : null));
        }
      });

    // 2. Fetch items independently
    fetchItems()
      .then((itms) => {
        if (isMountedRef.current) {
          setItems(itms);
          // If items succeeded, backend is definitely online
          setHealth((prev) => prev || {
            status: 'healthy',
            app: 'Turium AI Knowledge Inbox',
            total_items: itms.length,
            total_chunks: itms.reduce((acc, itm) => acc + (itm.chunk_count || 0), 0),
            embedding_provider: 'Semantic Embedder',
            splitter_type: 'unstructured_recursive'
          });
        }
      })
      .catch((err) => {
        console.warn('Could not fetch items:', err.message);
      })
      .finally(() => {
        if (isMountedRef.current) {
          setLoadingItems(false);
        }
      });
  }, []);

  useEffect(() => {
    loadData();
    // Refresh health and items every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleIngest = async (payload: IngestItemRequest) => {
    setLoadingIngest(true);
    try {
      const result = await ingestContent(payload);
      showToast(`Successfully saved and chunked into ${result.chunk_count} parts!`);
      await loadData();
    } catch (err: any) {
      showToast(err.message || 'Ingestion failed.', 'error');
      throw err;
    } finally {
      setLoadingIngest(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteItem(id);
      showToast('Item and vector chunks deleted.');
      await loadData();
      // If deleted item was cited in active query, clear query
      if (queryResult?.sources.some((s) => s.item_id === id)) {
        setQueryResult(null);
      }
    } catch (err: any) {
      showToast(err.message || 'Failed to delete item.', 'error');
    }
  };

  const handleQuery = async (question: string, topK: number) => {
    setLoadingQuery(true);
    try {
      const result = await submitQuery(question, topK);
      setQueryResult(result);
    } catch (err: any) {
      showToast(err.message || 'Query failed.', 'error');
    } finally {
      setLoadingQuery(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
      {/* Header */}
      <Header health={health} loading={loadingItems} />

      {/* Toast Notification */}
      {toast && (
        <div className="fixed bottom-5 right-5 z-50 flex items-center space-x-2 px-4 py-3 rounded-xl shadow-lg border text-xs font-medium animate-in fade-in slide-in-from-bottom-5 duration-200 bg-white border-slate-200">
          {toast.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          )}
          <span className="text-slate-800">{toast.message}</span>
          <button
            onClick={() => setToast(null)}
            className="p-1 text-slate-400 hover:text-slate-600 rounded-lg ml-2"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Main Content Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left Column: Ingestion & Knowledge Library (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            <IngestForm onIngest={handleIngest} loading={loadingIngest} />
            <ItemList items={items} loading={loadingItems} onDelete={handleDelete} />
          </div>

          {/* Right Column: Q&A / Semantic Search RAG Inbox (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            <QueryInterface
              onQuery={handleQuery}
              loading={loadingQuery}
              disabled={items.length === 0}
            />

            <AnswerDisplay result={queryResult} loading={loadingQuery} />

            {/* Empty state guidance when no query has been run yet */}
            {!queryResult && !loadingQuery && (
              <div className="bg-white rounded-2xl border border-slate-200/80 p-8 text-center shadow-sm">
                <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
                  <span className="text-2xl">🧠</span>
                </div>
                <h3 className="text-sm font-semibold text-slate-800">Ready to Answer</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                  Ask questions across all notes and server-fetched web pages. The RAG pipeline will retrieve the most relevant semantic chunks and cite exact sources.
                </p>
                <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-3 gap-2 text-left">
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <p className="text-[11px] font-semibold text-slate-700">1. Ingest</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">Save notes or URLs. Chunks extracted via Unstructured splitter.</p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <p className="text-[11px] font-semibold text-slate-700">2. Retrieve</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">Top-k semantic search using cosine similarity.</p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <p className="text-[11px] font-semibold text-slate-700">3. Synthesize</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">LLM generates answers with strict evidence citations.</p>
                  </div>
                </div>
              </div>
            )}
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200/80 bg-white py-4 mt-12 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Turium AI &bull; Minimal AI Knowledge Inbox</span>
          <span className="text-slate-400 font-mono text-[11px]">
            Stack: React TS + FastAPI + LangChain + Unstructured Text Splitter + SQLite Vector Store
          </span>
        </div>
      </footer>
    </div>
  );
};

export default App;
