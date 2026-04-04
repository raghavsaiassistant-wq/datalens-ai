import React, { useState, useEffect } from 'react';
import { Sparkles, Activity, ShieldCheck, ShieldAlert, Shield } from 'lucide-react';

const SummaryPanel = ({ summary, healthScore, profile }) => {
  const [displayedText, setDisplayedText] = useState("");
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!summary || index >= summary.length) return;
    const timeout = setTimeout(() => {
      setDisplayedText(prev => prev + summary[index]);
      setIndex(prev => prev + 1);
    }, 15);
    return () => clearTimeout(timeout);
  }, [index, summary]);

  const getHealthUI = (score) => {
    if (score >= 80) return { color: '#00F08F', icon: ShieldCheck, label: 'Stable' };
    if (score >= 60) return { color: '#FFB800', icon: Shield, label: 'Warning' };
    return { color: '#FF3B3B', icon: ShieldAlert, label: 'Critical' };
  };

  const healthUI = getHealthUI(healthScore);
  const HealthIcon = healthUI.icon;

  return (
    <div className="glass-card p-8 h-full flex flex-col relative overflow-hidden group">
      {/* Decorative Gradient Glow */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-accent/5 rounded-full blur-[100px] -translate-y-1/2 translate-x-1/3 group-hover:bg-accent/10 transition-colors duration-1000"></div>
      
      <div className="flex justify-between items-start mb-10 relative z-10">
        <div className="space-y-1">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="text-accent" size={20} />
            <span className="text-[10px] uppercase tracking-[0.3em] text-accent font-bold">Intelligence Report</span>
          </div>
          <h2 className="text-3xl font-serif text-white italic">Executive <span className="text-white/60">Summary</span></h2>
        </div>
        
        <div className="flex flex-col items-center group/score">
          <div className="relative w-20 h-20 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90 drop-shadow-[0_0_8px_rgba(0,0,0,0.5)]" viewBox="0 0 36 36">
              <circle
                cx="18" cy="18" r="16"
                fill="none"
                stroke="rgba(255,255,255,0.05)"
                strokeWidth="2.5"
              />
              <circle
                cx="18" cy="18" r="16"
                fill="none"
                stroke={healthUI.color}
                strokeWidth="2.5"
                strokeDasharray={`${healthScore}, 100`}
                strokeLinecap="round"
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-lg font-mono font-bold text-white transition-transform group-hover/score:scale-110 duration-500">{healthScore}</span>
            </div>
          </div>
          <div className="flex items-center gap-1 mt-2">
            <HealthIcon size={10} style={{ color: healthUI.color }} />
            <span className="text-[9px] uppercase tracking-widest text-secondary font-mono">{healthUI.label}</span>
          </div>
        </div>
      </div>
      
      <div className="flex-grow relative z-10">
        <div className="min-h-[120px]">
          <p className="text-white/90 leading-relaxed text-lg font-serif italic">
            {displayedText}
            {summary && index < summary.length && <span className="inline-block w-2 h-5 bg-accent ml-1 animate-pulse mb-[-4px]"></span>}
          </p>
        </div>
      </div>

      <div className="mt-10 pt-6 border-t border-white/5 flex flex-wrap gap-4 justify-between text-[10px] text-secondary relative z-10 font-mono uppercase tracking-wider">
        <div className="flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-full border border-white/5">
          <Activity size={12} className="text-accent" />
          <span className="truncate max-w-[150px]">{profile?.file_name || 'raw_source.dat'}</span>
        </div>
        <div className="flex items-center gap-4 text-white/40">
          <span>{profile?.rows?.toLocaleString() || '0'} ROWS</span>
          <span className="w-1 h-1 bg-white/20 rounded-full"></span>
          <span>{profile?.cols || '0'} COLS</span>
          <span className="w-1 h-1 bg-white/20 rounded-full"></span>
          <span className="text-accent/60">{profile?.source_type || 'Generic'}</span>
        </div>
      </div>
    </div>
  );
};

export default SummaryPanel;
