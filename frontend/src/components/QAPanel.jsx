import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, ChevronUp, ChevronDown, Sparkles, User } from 'lucide-react';

const SUGGESTIONS = [
  "What is the total revenue?",
  "Which region performs best?",
  "What are the main anomalies?",
  "Summarize the key trends"
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
    
    // Auto-open if closed and user clicks a pill programmatically
    if (!isOpen) setIsOpen(true);

    try {
      const answer = await onAskQuestion(text);
      setMessages(prev => [...prev, { role: 'ai', content: answer }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'ai', content: "Sorry, I couldn't process that: " + err.message, error: true }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className={`fixed bottom-0 right-0 md:right-8 w-full md:w-[450px] transition-all duration-300 z-50 ${isOpen ? 'h-[500px]' : 'h-14'}`}>
      <div className="glass-card shadow-2xl h-full flex flex-col rounded-t-2xl md:rounded-b-none border-b-0 overflow-hidden bg-primary/95 backdrop-blur-xl">
        
        {/* Header Bar */}
        <div 
          className={`px-4 py-3 cursor-pointer flex justify-between items-center bg-white/5 border-b border-white/10 ${disabled ? 'opacity-50' : 'hover:bg-white/10'}`}
          onClick={() => !disabled && setIsOpen(!isOpen)}
        >
          <div className="flex items-center gap-2">
            <MessageSquare size={18} className="text-accent" />
            <h3 className="font-semibold text-white">Ask DataLens AI</h3>
          </div>
          <button disabled={disabled} className="text-secondary hover:text-white transition-colors">
            {isOpen ? <ChevronDown size={20}/> : <ChevronUp size={20}/>}
          </button>
        </div>

        {/* Chat Body */}
        {isOpen && (
          <div className="flex-grow flex flex-col h-full overflow-hidden">
            <div className="flex-grow overflow-y-auto p-4 flex flex-col gap-4">
              
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 animate-in fade-in duration-500">
                  <div className="w-16 h-16 bg-accent/10 rounded-full flex items-center justify-center mb-4">
                    <Sparkles className="text-accent" size={28} />
                  </div>
                  <p className="text-sm text-secondary mb-6 leading-relaxed">
                    I've analyzed your data. Ask me anything about trends, anomalies, or specific metrics!
                  </p>
                  <div className="flex flex-col gap-2 w-full">
                    {SUGGESTIONS.map((s, i) => (
                      <button 
                        key={i}
                        onClick={() => handleSubmit(null, s)}
                        className="text-xs text-left px-3 py-2 border border-white/10 rounded-lg hover:border-accent/50 hover:bg-accent/5 transition-all text-white/80"
                      >
                        "{s}"
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <>
                  {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm flex gap-3 ${
                        msg.role === 'user' 
                          ? 'bg-gradient-to-br from-[#76B900] to-[#5a9000] text-white shadow-lg rounded-tr-sm' 
                          : msg.error 
                            ? 'bg-danger/20 border border-danger/50 text-white rounded-tl-sm'
                            : 'bg-white/10 border border-white/5 text-white/90 rounded-tl-sm'
                      }`}>
                        {msg.role === 'ai' && !msg.error && <Sparkles size={16} className="text-accent shrink-0 mt-0.5" />}
                        {msg.role === 'user' && <User size={16} className="text-white/70 shrink-0 mt-0.5" />}
                        <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    </div>
                  ))}
                  
                  {isTyping && (
                    <div className="flex justify-start">
                      <div className="bg-white/5 border border-white/5 rounded-2xl px-4 py-3 rounded-tl-sm flex items-center gap-2">
                        <Sparkles size={16} className="text-accent animate-pulse" />
                        <div className="flex gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-secondary animate-bounce" style={{animationDelay: '0ms'}}></span>
                          <span className="w-2 h-2 rounded-full bg-secondary animate-bounce" style={{animationDelay: '150ms'}}></span>
                          <span className="w-2 h-2 rounded-full bg-secondary animate-bounce" style={{animationDelay: '300ms'}}></span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </>
              )}

            </div>

            {/* Input Bar */}
            <div className="p-3 bg-primary border-t border-white/10">
              <form onSubmit={(e) => handleSubmit(e)} className="relative">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask anything about your data..."
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-4 pr-12 text-sm text-white placeholder-secondary focus:outline-none focus:border-accent/50 focus:bg-white/10 transition-all"
                  disabled={isTyping}
                />
                <button 
                  type="submit" 
                  disabled={!query.trim() || isTyping}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-lg bg-accent text-primary disabled:opacity-50 disabled:bg-white/10 disabled:text-secondary transition-colors"
                >
                  <Send size={14} className="ml-0.5" />
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
