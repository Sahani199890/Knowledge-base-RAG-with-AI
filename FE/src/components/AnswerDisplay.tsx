import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, Quote, ExternalLink, ChevronDown, ChevronUp, FileText, Globe, Check, Copy } from './Icons';
import { QueryResponse } from '../types';

interface AnswerDisplayProps {
  result: QueryResponse | null;
  loading: boolean;
}

const CodeSnippet: React.FC<{ lang: string; code: string }> = ({ lang, code }) => {
  const [copied, setCopied] = useState(false);

  const handleCopyCode = () => {
    navigator.clipboard.writeText(code.trim());
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="my-3 rounded-xl overflow-hidden border border-slate-800 bg-slate-950 shadow-sm text-left">
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-slate-900 border-b border-slate-800 text-[11px] text-slate-400">
        <span className="font-mono uppercase tracking-wider text-emerald-400 font-semibold">{lang || 'code'}</span>
        <button
          type="button"
          onClick={handleCopyCode}
          className="flex items-center space-x-1 text-slate-300 hover:text-white transition-colors py-0.5 px-2 rounded hover:bg-slate-800 text-[11px]"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          <span>{copied ? 'Copied' : 'Copy Code'}</span>
        </button>
      </div>
      <pre className="p-3.5 text-xs font-mono text-emerald-300 overflow-x-auto leading-relaxed whitespace-pre">
        <code>{code.trim()}</code>
      </pre>
    </div>
  );
};

const MarkdownRenderer: React.FC<{ content: string }> = ({ content }) => {
  // Normalize Chinese brackets 【Source X】 to [Source X] for clean consistency
  const normalized = content.replace(/【Source\s*(\d+)】/g, '[Source $1]');

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: ({ children }) => (
          <h1 className="text-base sm:text-lg font-bold text-slate-900 mt-4 mb-2 pb-1 border-b border-slate-200/80">
            {children}
          </h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-sm sm:text-base font-bold text-slate-900 mt-3.5 mb-1.5 text-slate-900">
            {children}
          </h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-xs sm:text-sm font-semibold text-slate-900 mt-3 mb-1 text-blue-900">
            {children}
          </h3>
        ),
        h4: ({ children }) => (
          <h4 className="text-xs font-semibold text-slate-800 mt-2 mb-1">
            {children}
          </h4>
        ),
        p: ({ children }) => (
          <p className="mb-2.5 leading-relaxed text-slate-800 last:mb-0">
            {children}
          </p>
        ),
        strong: ({ children }) => (
          <strong className="font-semibold text-slate-950">
            {children}
          </strong>
        ),
        em: ({ children }) => (
          <em className="italic text-slate-700">
            {children}
          </em>
        ),
        ul: ({ children }) => (
          <ul className="list-disc list-outside pl-5 space-y-1 mb-2.5 text-slate-800">
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal list-outside pl-5 space-y-1 mb-2.5 text-slate-800">
            {children}
          </ol>
        ),
        li: ({ children }) => (
          <li className="leading-relaxed pl-0.5">
            {children}
          </li>
        ),
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-blue-500 bg-blue-50/60 pl-3.5 py-1.5 my-2.5 text-slate-700 italic rounded-r-lg">
            {children}
          </blockquote>
        ),
        table: ({ children }) => (
          <div className="overflow-x-auto my-3 rounded-xl border border-slate-200 bg-white shadow-xs">
            <table className="w-full text-xs text-left border-collapse">
              {children}
            </table>
          </div>
        ),
        thead: ({ children }) => (
          <thead className="bg-slate-100/90 text-slate-700 font-semibold border-b border-slate-200 uppercase text-[10px] tracking-wider">
            {children}
          </thead>
        ),
        tbody: ({ children }) => (
          <tbody className="divide-y divide-slate-100 bg-white">
            {children}
          </tbody>
        ),
        tr: ({ children }) => (
          <tr className="hover:bg-slate-50/70 transition-colors">
            {children}
          </tr>
        ),
        th: ({ children }) => (
          <th className="px-3.5 py-2.5 font-semibold text-slate-800 border-r border-slate-200/80 last:border-r-0">
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="px-3.5 py-2 border-r border-slate-100 last:border-r-0 text-slate-700 align-top">
            {children}
          </td>
        ),
        code({ node, inline, className, children, ...props }: any) {
          const match = /language-(\w+)/.exec(className || '');
          const codeString = String(children).replace(/\n$/, '');
          
          if (!inline && (match || codeString.includes('\n'))) {
            return (
              <CodeSnippet
                lang={match ? match[1] : 'code'}
                code={codeString}
              />
            );
          }
          return (
            <code
              className="px-1.5 py-0.5 rounded-md bg-blue-100/80 text-blue-900 font-mono text-[11px] font-medium border border-blue-200/50"
              {...props}
            >
              {children}
            </code>
          );
        },
      }}
    >
      {normalized}
    </ReactMarkdown>
  );
};

export const AnswerDisplay: React.FC<AnswerDisplayProps> = ({ result, loading }) => {
  const [copied, setCopied] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Record<number, boolean>>({ 1: true });

  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 text-center animate-pulse">
        <div className="flex items-center justify-center space-x-2 text-blue-600 mb-3">
          <Bot className="w-5 h-5 animate-bounce" />
          <span className="text-xs font-semibold uppercase tracking-wider">Generating RAG Answer</span>
        </div>
        <div className="h-4 bg-slate-100 rounded w-3/4 mx-auto mb-2.5"></div>
        <div className="h-4 bg-slate-100 rounded w-5/6 mx-auto mb-2.5"></div>
        <div className="h-4 bg-slate-100 rounded w-2/3 mx-auto"></div>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(result.answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const toggleSource = (sourceNum: number) => {
    setExpandedSources((prev) => ({
      ...prev,
      [sourceNum]: !prev[sourceNum],
    }));
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 space-y-5 transition-all">
      {/* Answer Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-blue-600 text-white shadow-sm">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">AI Generated Answer</h3>
            <span className="text-[11px] text-slate-500 font-medium">Model: {result.llm_used}</span>
          </div>
        </div>

        {/* Copy button */}
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-800 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          title="Copy answer to clipboard"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
          <span>{copied ? 'Copied!' : 'Copy'}</span>
        </button>
      </div>

      {/* Answer Body */}
      <div className="text-xs sm:text-sm text-slate-800 leading-relaxed font-sans bg-blue-50/30 p-4 rounded-xl border border-blue-100/60">
        <MarkdownRenderer content={result.answer} />
      </div>

      {/* Cited Sources Section */}
      <div className="pt-2">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-xs font-semibold text-slate-900 flex items-center space-x-1.5">
            <Quote className="w-3.5 h-3.5 text-blue-600" />
            <span>Cited Sources & Evidence Chunks</span>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">
              {result.sources.length}
            </span>
          </h4>
        </div>

        {result.sources.length === 0 ? (
          <p className="text-xs text-slate-400 italic">No specific source chunks retrieved.</p>
        ) : (
          <div className="space-y-2.5">
            {result.sources.map((source) => {
              const isExpanded = !!expandedSources[source.source_num];

              return (
                <div
                  key={source.chunk_id}
                  className="border border-slate-200/90 rounded-xl overflow-hidden transition-all bg-slate-50/40"
                >
                  {/* Source Summary Bar */}
                  <div
                    onClick={() => toggleSource(source.source_num)}
                    className="p-3 flex items-center justify-between gap-2 cursor-pointer hover:bg-slate-100/70 transition-colors"
                  >
                    <div className="flex items-center space-x-2.5 min-w-0">
                      {/* Source badge */}
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-blue-600 text-white shrink-0">
                        [Source {source.source_num}]
                      </span>

                      {/* Icon */}
                      <span className="text-slate-500 shrink-0">
                        {source.source_type === 'url' ? (
                          <Globe className="w-3.5 h-3.5 text-emerald-600" />
                        ) : (
                          <FileText className="w-3.5 h-3.5 text-indigo-600" />
                        )}
                      </span>

                      {/* Title */}
                      <span className="text-xs font-semibold text-slate-800 truncate">
                        {source.title}
                      </span>
                    </div>

                    <div className="flex items-center space-x-3 shrink-0">
                      {/* Similarity Score Pill */}
                      <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                        {source.similarity_score}% match
                      </span>

                      {/* Expand Toggle */}
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {/* Verbatim Chunk Snippet */}
                  {isExpanded && (
                    <div className="px-3.5 pb-3 pt-1 border-t border-slate-200/60 bg-white">
                      <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1.5">
                        <span>Chunk #{source.chunk_index} extracted by Unstructured Splitter</span>
                        {source.url && (
                          <a
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center space-x-1 text-blue-600 hover:underline"
                          >
                            <span>Open Link</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>

                      <blockquote className="text-xs text-slate-700 font-mono bg-slate-50 p-2.5 rounded-lg border border-slate-200/60 leading-relaxed whitespace-pre-wrap">
                        {source.snippet}
                      </blockquote>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
