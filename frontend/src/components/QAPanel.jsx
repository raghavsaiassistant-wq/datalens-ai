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
      <div className="h-full flex flex-col rounded-t-3xl md:rounded-t-2xl border border-white/[0.08] border-b-0 overflow-hidden bg-[#060810]/95 backdrop-blur-2xl shadow-[0_-20px_80px_rgba(0,0,0,0.5)]">

        {/* ── Header bar ── */}
        <div
          className={`flex items-center justify-between px-5 py-3.5 cursor-pointer select-none transition-colors border-b ${
            isOpen ? 'border-white/[0.06]' : 'border-transparent'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-white/[0.02]'}`}
          onClick={() => !disabled && setIsOpen(o => !o)}
        >
          <div className="flex items-center gap-3">
            <div className={`p-1.5 rounded-lg transition-colors ${isOpen ? 'bg-accent/10' : 'bg-white/[0.04]'}`}>
              <Terminal size={15} className={isOpen ? 'text-accent' : 'text-white/35'} />
            </div>
            <div>
              <span className="font-serif italic text-white text-base">
                Neural <span className="text-white/30">Interface</span>
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
                className="text-white/15 hover:text-white/50 transition-colors p-1 rounded"
                title="Clear chat"
              >
                <X size={12} />
              </button>
            )}
            <button className="text-white/20 hover:text-white/60 transition-colors">
              {isOpen ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
            </button>
          </div>
        </div>

        {/* ── Chat body ── */}
        {isOpen && (
          <div className="flex-grow flex flex-col overflow-hidden">
            <div className="flex-grow overflow-y-auto px-5 py-4 flex flex-col gap-4 custom-scrollbar">

              {messages.length === 0 ? (
                /* Welcome state */
                <div className="h-full flex flex-col items-center justify-center text-center py-8 animate-in fade-in zoom-in-95 duration-500">
                  <div className="relative mb-5">
                    <div className="w-14 h-14 bg-accent/[0.06] rounded-2xl flex items-center justify-center border border-accent/[0.12]">
                      <Cpu size={26} className="text-accent/60" />
                    </div>
                    <div className="absolute inset-0 bg-accent/10 rounded-2xl blur-xl" />
                  </div>
                  <p className="text-white/60 font-serif italic mb-1">Ask anything about your data</p>
                  <p className="text-white/25 text-xs font-mono mb-6">Powered by Llama 3.1 8B via NVIDIA NIM</p>
                  <div className="flex flex-col gap-2 w-full">
                    {SUGGESTIONS.map((s, i) => (
                      <button
                        key={i}
                        onClick={() => send(s)}
                        className="text-left px-4 py-2.5 bg-white/[0.02] border border-white/[0.06] rounded-xl hover:border-accent/30 hover:bg-accent/[0.04] transition-all text-[11px] font-mono text-white/35 hover:text-white/70 group"
                      >
                        <span className="text-accent/30 group-hover:text-accent mr-2">/</span>
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
                            ? 'bg-accent text-[#060810] font-medium rounded-tr-sm shadow-[0_4px_20px_rgba(118,185,0,0.12)]'
                            : msg.error
                              ? 'bg-red-500/[0.08] border border-red-500/20 text-red-300 rounded-tl-sm font-mono text-xs'
                              : 'bg-white/[0.03] border border-white/[0.07] text-white/85 rounded-tl-sm'
                        }`}
                      >
                        {msg.role === 'ai' && !msg.error && (
                          <div className="flex items-center gap-1.5 mb-2 pb-2 border-b border-white/[0.06]">
                            <Sparkles size={11} className="text-accent/60" />
                            <span className="text-[9px] font-mono text-accent/50 uppercase tracking-widest">AI Analysis</span>
                          </div>
                        )}
                        <p className={`leading-relaxed whitespace-pre-wrap text-[13px] ${msg.role === 'ai' && !msg.error ? 'font-serif italic' : ''}`}>
                          {msg.content}
                        </p>
                      </div>
                    </div>
                  ))}

                  {isTyping && (
                    <div className="flex justify-start">
                      <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-3">
                        <Cpu size={13} className="text-accent/60 animate-spin-slow" />
                        <div className="flex gap-1">
                          {[0, 150, 300].map(d => (
                            <span
                              key={d}
                              className="w-1.5 h-1.5 rounded-full bg-accent/35 animate-bounce"
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
            <div className="px-4 pb-4 pt-3 border-t border-white/[0.05]">
              <form onSubmit={handleSubmit} className="relative">
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder="Ask about your data…"
                  disabled={isTyping || disabled}
                  className="w-full bg-white/[0.02] border border-white/[0.08] focus:border-accent/30 rounded-xl py-3 pl-4 pr-12 text-sm text-white placeholder-white/20 focus:outline-none focus:bg-accent/[0.03] transition-all font-mono disabled:opacity-40"
                />
                <button
                  type="submit"
                  disabled={!query.trim() || isTyping || disabled}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-lg bg-accent text-[#060810] active:scale-95 disabled:opacity-0 disabled:pointer-events-none transition-all shadow-lg"
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
