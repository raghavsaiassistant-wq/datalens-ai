import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, ChevronUp, ChevronDown, Sparkles, User, Terminal, Cpu } from 'lucide-react';

const SUGGESTIONS = [
  "Identify top revenue drivers",
  "Summarize statistical anomalies",
  "Predict next month's trend",
  "Explain data health variance"
];

const QAPanel = ({ onAskQuestion, disabled }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSubmit = async (e, forcedQuery = null) => {
    if (e) e.preventDefault();
    const text = forcedQuery || query;
    if (!text.trim() || disabled) return;

    setQuery('');
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setIsTyping(true);
    
    if (!isOpen) setIsOpen(true);

    try {
      const answer = await onAskQuestion(text);
      setMessages(prev => [...prev, { role: 'ai', content: answer }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'ai', content: "Protocol failure: " + err.message, error: true }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className={`fixed bottom-0 right-0 md:right-8 w-full md:w-[480px] transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)] z-50 ${isOpen ? 'h-[600px]' : 'h-16'}`}>
      <div className="glass-card shadow-[0_20px_80px_rgba(0,0,0,0.4)] h-full flex flex-col rounded-t-3xl md:rounded-b-none border-b-0 overflow-hidden bg-[#0A0C10]/95 backdrop-blur-2xl">
        
        {/* Header Bar */}
        <div 
          className={`px-6 py-4 cursor-pointer flex justify-between items-center transition-all duration-300 ${disabled ? 'opacity-50' : 'hover:bg-white/[0.03]'}`}
          onClick={() => !disabled && setIsOpen(!isOpen)}
        >
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg transition-colors ${isOpen ? 'bg-accent/10' : 'bg-white/5'}`}>
              <Terminal size={18} className={isOpen ? 'text-accent' : 'text-white/40'} />
            </div>
            <div>
              <h3 className="font-serif italic text-white text-lg">Neural <span className="text-white/40">Interface</span></h3>
              {!isOpen && <span className="text-[9px] font-mono text-accent uppercase tracking-widest animate-pulse">Ready for query</span>}
            </div>
          </div>
          <button disabled={disabled} className="text-white/20 hover:text-white transition-colors">
            {isOpen ? <ChevronDown size={20}/> : <ChevronUp size={20}/>}
          </button>
        </div>

        {/* Chat Body */}
        {isOpen && (
          <div className="flex-grow flex flex-col h-full overflow-hidden">
            <div className="flex-grow overflow-y-auto p-6 flex flex-col gap-6 custom-scrollbar">
              
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 animate-in fade-in zoom-in-95 duration-700">
                  <div className="w-20 h-20 bg-accent/5 rounded-3xl flex items-center justify-center mb-6 border border-accent/10 relative">
                    <div className="absolute inset-0 bg-accent/20 rounded-3xl blur-xl animate-pulse"></div>
                    <Cpu className="text-accent relative z-10" size={32} />
                  </div>
                  <h4 className="text-2xl font-serif text-white mb-3 italic">Intelligence <span className="text-white/40">Active</span></h4>
                  <p className="text-sm text-[#8E9AAF] mb-8 leading-relaxed font-light italic">
                    Query the semantic data model for deep architectural insights or trend syntheses.
                  </p>
                  <div className="flex flex-col gap-2.5 w-full">
                    {SUGGESTIONS.map((s, i) => (
                      <button 
                        key={i}
                        onClick={() => handleSubmit(null, s)}
                        className="text-[11px] font-mono text-left px-4 py-3 bg-white/[0.02] border border-white/5 rounded-xl hover:border-accent/40 hover:bg-accent/5 transition-all text-white/50 hover:text-white uppercase tracking-widest group"
                      >
                        <span className="text-accent/40 group-hover:text-accent mr-2">/</span> {s}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <>
                  {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[90%] rounded-2xl px-5 py-4 text-sm relative group/msg ${
                        msg.role === 'user' 
                          ? 'bg-accent text-[#0A0C10] font-medium rounded-tr-sm shadow-[0_10px_30px_rgba(118,185,0,0.1)]' 
                          : msg.error 
                            ? 'bg-danger/10 border border-danger/30 text-white rounded-tl-sm'
                            : 'bg-white/[0.03] border border-white/10 text-white/90 rounded-tl-sm'
                      }`}>
                        <div className="flex items-start gap-3">
                          {msg.role === 'ai' && <Sparkles size={16} className="text-accent shrink-0 mt-0.5" />}
                          <div className={`leading-relaxed whitespace-pre-wrap ${msg.role === 'ai' ? 'font-serif italic text-[15px]' : 'font-sans'}`}>
                            {msg.content}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {isTyping && (
                    <div className="flex justify-start">
                      <div className="bg-white/[0.02] border border-white/10 rounded-2xl px-5 py-4 rounded-tl-sm flex items-center gap-3">
                        <Cpu size={16} className="text-accent animate-spin-slow" />
                        <div className="flex gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-accent/40 animate-bounce" style={{animationDelay: '0ms'}}></span>
                          <span className="w-1.5 h-1.5 rounded-full bg-accent/40 animate-bounce" style={{animationDelay: '150ms'}}></span>
                          <span className="w-1.5 h-1.5 rounded-full bg-accent/40 animate-bounce" style={{animationDelay: '300ms'}}></span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </>
              )}

            </div>

            {/* Input Bar */}
            <div className="p-4 bg-[#0A0C10] border-t border-white/5">
              <form onSubmit={(e) => handleSubmit(e)} className="relative group/input">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Initiate semantic query..."
                  className="w-full bg-white/[0.02] border border-white/10 rounded-2xl py-4 pl-5 pr-14 text-sm text-white placeholder-white/20 focus:outline-none focus:border-accent/40 focus:bg-accent/5 transition-all font-mono"
                  disabled={isTyping}
                />
                <button 
                  type="submit" 
                  disabled={!query.trim() || isTyping}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 flex items-center justify-center rounded-xl bg-accent text-[#0A0C10] active:scale-95 disabled:opacity-0 disabled:pointer-events-none transition-all duration-500 shadow-xl"
                >
                  <Send size={18} />
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
