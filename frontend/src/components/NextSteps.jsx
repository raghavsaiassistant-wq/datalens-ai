import React from 'react';
import { Target, ChevronRight } from 'lucide-react';

const NextSteps = ({ steps }) => {
  if (!steps || steps.length === 0) return null;

  const getPriorityData = (p) => {
    switch(p?.toLowerCase()) {
      case 'immediate': return { color: '#FF3B3B', bg: 'bg-danger/10' };
      case 'short-term': return { color: '#FFB800', bg: 'bg-warning/10' };
      default: return { color: '#00F08F', bg: 'bg-success/10' };
    }
  };

  return (
    <div className="glass-card p-10 mb-12 relative overflow-hidden group">
      {/* Background Decor */}
      <div className="absolute top-0 left-0 w-full h-full bg-accent-blue/5 opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none"></div>
      
      <div className="flex items-center gap-3 mb-10 relative z-10">
        <div className="w-12 h-12 rounded-2xl bg-accent-blue/10 flex items-center justify-center border border-accent-blue/20">
          <Target className="text-accent-blue" size={24} />
        </div>
        <div>
          <span className="text-[10px] uppercase tracking-[0.3em] text-accent-blue font-bold block mb-0.5">Strategic Roadmap</span>
          <h2 className="text-3xl font-serif text-white italic">Recommended <span className="text-white/60">Actions</span></h2>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative z-10">
        {steps.map((step, i) => {
          const { color, bg } = getPriorityData(step.priority);
          return (
            <div 
              key={i} 
              className={`bg-white/[0.02] rounded-3xl p-8 border border-white/5 relative overflow-hidden group/item hover:border-white/20 transition-all duration-500 animate-in slide-in-from-bottom-6 fade-in fill-mode-both animate-stagger-${Math.min(i+1, 4)} shadow-xl`}
            >
              {/* Step Number Background */}
              <div className="absolute -top-4 -right-2 p-4 text-white/[0.03] font-serif italic text-9xl group-hover/item:text-white/[0.06] transition-colors pointer-events-none select-none">
                {i+1}
              </div>

              <div className="flex flex-col h-full">
                <div className="mb-4">
                  <span className={`text-[9px] uppercase font-mono font-bold tracking-[0.2em] px-3 py-1.5 rounded-full border border-white/5 ${bg} inline-block`} style={{ color }}>
                    {step.priority}
                  </span>
                </div>
                
                <h3 className="text-xl font-serif text-white mb-3 italic tracking-tight group-hover/item:text-accent-blue transition-colors relative z-10">
                  {step.action}
                </h3>
                
                <p className="text-sm text-[#8E9AAF] leading-relaxed font-light relative z-10 flex-grow">
                  {step.reason}
                </p>
                
                <div className="mt-6 flex items-center gap-2 text-[10px] font-mono text-white/20 uppercase tracking-widest group-hover/item:text-accent-blue/60 transition-colors">
                  <span>Implementation Guide</span>
                  <ChevronRight size={12} />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default NextSteps;
