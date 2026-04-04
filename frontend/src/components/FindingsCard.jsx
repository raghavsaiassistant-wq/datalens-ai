import React from 'react';
import { Lightbulb, ArrowUpRight } from 'lucide-react';

const FindingsCard = ({ findings }) => {
  if (!findings || findings.length === 0) return null;

  const getImpactData = (impact) => {
    const low = impact?.toLowerCase();
    if (low === 'high') return { color: '#FF3B3B', bg: 'bg-danger/10' };
    if (low === 'medium') return { color: '#FFB800', bg: 'bg-warning/10' };
    return { color: '#00E5FF', bg: 'bg-accent-blue/10' };
  };

  return (
    <div className="glass-card p-8 h-full flex flex-col group">
      <div className="flex items-center gap-2 mb-8 relative">
        <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center border border-accent/20">
          <Lightbulb className="text-accent" size={20} />
        </div>
        <div>
          <span className="text-[10px] uppercase tracking-[0.3em] text-accent font-bold block mb-0.5">Critical Insights</span>
          <h2 className="text-2xl font-serif text-white italic">Key <span className="text-white/60">Findings</span></h2>
        </div>
      </div>
      
      <div className="flex flex-col gap-5 flex-grow">
        {findings.map((finding, i) => {
          const { color, bg } = getImpactData(finding.impact);
          return (
            <div 
              key={i} 
              className={`p-5 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-white/10 transition-all duration-500 animate-in slide-in-from-right-4 fade-in fill-mode-both animate-stagger-${Math.min(i+1, 4)} group/item`}
            >
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full`} style={{ backgroundColor: color }}></span>
                  <h3 className="font-semibold text-white text-md tracking-tight group-hover/item:text-accent transition-colors">{finding.headline}</h3>
                </div>
                <div className={`px-2 py-0.5 rounded-lg ${bg} border border-white/5 flex items-center gap-1`}>
                  <span className="text-[9px] uppercase tracking-widest font-mono font-bold" style={{ color }}>
                    {finding.impact}
                  </span>
                </div>
              </div>
              <p className="text-sm text-secondary leading-relaxed font-light pl-3.5 border-l border-white/10 italic">
                {finding.detail}
              </p>
              <div className="mt-3 flex justify-end opacity-0 group-hover/item:opacity-100 transition-opacity">
                <ArrowUpRight size={14} className="text-white/20" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default FindingsCard;
