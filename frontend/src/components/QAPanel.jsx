import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, ChevronUp, ChevronDown, Sparkles, Terminal, Cpu, X } from 'lucide-react';

const SUGGESTIONS = [
  'What are the top revenue drivers?',
  'Summarize the key statistical anomalies',
  'Which column has the highest variance?',
  'What data quality issues exist?',
];

const QAPanel = ({ onAskQuestion, disabled }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  useEffect(() => {
    if (isOpen && !disabled) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [isOpen, disabled]);

  const send = async (text) => {
    const q = (text || query).trim();
    if (!q || disabled || isTyping) return;
    setQuery('');
    if (!isOpen) setIsOpen(true);
    setMessages(prev => [...prev, { role: 'user', content: q }]);
    setIsTyping(true);
    try {
      const answer = await onAskQuestion(q);
      setMessages(prev => [...prev, { role: 'ai', content: answer }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'ai', content: err.message, error: true }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSubmit = (e) => { if (e) e.preventDefault(); send(); };

  return (
    <div
      className={`fixed bottom-0 right-0 md:right-6 w-full md:w-[440px] z-50 transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)] ${
        isOpen ? 'h-[580px]' : 'h-14'
      }`}
    >
      <div className="h-full flex flex-col rounded-t-3xl md:rounded-t-2xl border border-black/[0.10] border-b-0 overflow-hidden bg-white shadow-[0_-8px_40px_rgba(0,0,0,0.10)]">

        {/* ── Header bar ── */}
        <div
          className={`flex items-center justify-between px-5 py-3.5 cursor-pointer select-none transition-colors border-b ${
            isOpen ? 'border-black/[0.07]' : 'border-transparent'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-[#F5F5F7]'}`}
          onClick={() => !disabled && setIsOpen(o => !o)}
        >
          <div className="flex items-center gap-3">
            <div className={`p-1.5 rounded-lg transition-colors ${isOpen ? 'bg-accent/10' : 'bg-[#F5F5F7]'}`}>
              <Terminal size={15} className={isOpen ? 'text-accent' : 'text-[#8E8E93]'} />
            </div>
            <div>
              <span className="font-serif italic text-[#1D1D1F] text-base">
                Neural <span className="text-[#8E8E93]">Interface</span>
              </span>
              {!isOpen && (
                <span className="text-[9px] font-mono text-accent uppercase tracking-widest ml-2 animate-pulse">
                  · ready
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isOpen && messages.length > 0 && (
              <button
                onClick={(e) => { e.stopPropagation(); setMessages([]); }}
                className="text-[#8E8E93] hover:text-[#1D1D1F] transition-colors p-1 rounded"
                title="Clear chat"
              >
                <X size={12} />
              </button>
            )}
            <button className="text-[#8E8E93] hover:text-[#1D1D1F] transition-colors">
              {isOpen ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
            </button>
          </div>
        </div>

        {/* ── Chat body ── */}
        {isOpen && (
          <div className="flex-grow flex flex-col overflow-hidden bg-white">
            <div className="flex-grow overflow-y-auto px-5 py-4 flex flex-col gap-4 custom-scrollbar bg-[#F5F5F7]">

              {messages.length === 0 ? (
                /* Welcome state */
                <div className="h-full flex flex-col items-center justify-center text-center py-8 animate-in fade-in zoom-in-95 duration-500">
                  <div className="relative mb-5">
                    <div className="w-14 h-14 bg-accent/[0.08] rounded-2xl flex items-center justify-center border border-accent/[0.18]">
                      <Cpu size={26} className="text-accent/70" />
                    </div>
                    <div className="absolute inset-0 bg-accent/10 rounded-2xl blur-xl" />
                  </div>
                  <p className="text-[#1D1D1F] font-serif italic mb-1">Ask anything about your data</p>
                  <p className="text-[#8E8E93] text-xs font-mono mb-6">Powered by Llama 3.1 8B via NVIDIA NIM</p>
                  <div className="flex flex-col gap-2 w-full">
                    {SUGGESTIONS.map((s, i) => (
                      <button
                        key={i}
                        onClick={() => send(s)}
                        className="text-left px-4 py-2.5 bg-white border border-black/[0.07] rounded-xl hover:border-accent/30 hover:bg-accent/[0.03] transition-all text-[11px] font-mono text-[#6E6E73] hover:text-[#1D1D1F] group shadow-sm"
                      >
                        <span className="text-accent/50 group-hover:text-accent mr-2">/</span>
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <>
                  {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div
                        className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm ${
                          msg.role === 'user'
                            ? 'bg-[#1D1D1F] text-white font-medium rounded-tr-sm shadow-[0_2px_12px_rgba(0,0,0,0.15)]'
                            : msg.error
                              ? 'bg-red-50 border border-red-200 text-red-600 rounded-tl-sm font-mono text-xs'
                              : 'bg-white border border-black/[0.08] text-[#1D1D1F] rounded-tl-sm shadow-sm'
                        }`}
                      >
                        {msg.role === 'ai' && !msg.error && (
                          <div className="flex items-center gap-1.5 mb-2 pb-2 border-b border-black/[0.07]">
                            <Sparkles size={11} className="text-accent/70" />
                            <span className="text-[9px] font-mono text-accent uppercase tracking-widest">AI Analysis</span>
                          </div>
                        )}
                        <p className={`leading-relaxed whitespace-pre-wrap text-[13px] ${msg.role === 'ai' && !msg.error ? 'font-serif italic text-[#1D1D1F]' : ''}`}>
                          {msg.content}
                        </p>
                      </div>
                    </div>
                  ))}

                  {isTyping && (
                    <div className="flex justify-start">
                      <div className="bg-white border border-black/[0.08] rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-3 shadow-sm">
                        <Cpu size={13} className="text-accent/70 animate-spin-slow" />
                        <div className="flex gap-1">
                          {[0, 150, 300].map(d => (
                            <span
                              key={d}
                              className="w-1.5 h-1.5 rounded-full bg-accent/40 animate-bounce"
                              style={{ animationDelay: `${d}ms` }}
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={bottomRef} />
                </>
              )}
            </div>

            {/* ── Input ── */}
            <div className="px-4 pb-4 pt-3 border-t border-black/[0.07] bg-white">
              <form onSubmit={handleSubmit} className="relative">
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder="Ask about your data…"
                  disabled={isTyping || disabled}
                  className="w-full bg-[#F5F5F7] border border-black/[0.08] focus:border-accent/40 rounded-xl py-3 pl-4 pr-12 text-sm text-[#1D1D1F] placeholder-[#8E8E93] focus:outline-none focus:bg-white transition-all font-mono disabled:opacity-40"
                />
                <button
                  type="submit"
                  disabled={!query.trim() || isTyping || disabled}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-lg bg-[#1D1D1F] text-white active:scale-95 disabled:opacity-0 disabled:pointer-events-none transition-all shadow"
                >
                  <Send size={14} />
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default QAPanel;
