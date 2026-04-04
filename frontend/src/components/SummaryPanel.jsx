import React, { useState, useEffect } from 'react';
import { Sparkles, Activity, ShieldCheck, ShieldAlert, Shield, Database } from 'lucide-react';

const SummaryPanel = ({ summary, healthScore, profile }) => {
  const [displayedText, setDisplayedText] = useState('');
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!summary || index >= summary.length) return;
    const t = setTimeout(() => {
      setDisplayedText(prev => prev + summary[index]);
      setIndex(prev => prev + 1);
    }, 14);
    return () => clearTimeout(t);
  }, [index, summary]);

  const getHealthUI = (s) => {
    if (s >= 80) return { color: '#34C759', ringColor: 'rgba(52,199,89,0.12)', icon: ShieldCheck, label: 'Excellent' };
    if (s >= 60) return { color: '#FF9500', ringColor: 'rgba(255,149,0,0.12)', icon: Shield, label: 'Fair' };
    return { color: '#FF3B30', ringColor: 'rgba(255,59,48,0.12)', icon: ShieldAlert, label: 'Poor' };
  };

  const h = getHealthUI(healthScore ?? 0);
  const HealthIcon = h.icon;
  const safePct = Math.min(100, Math.max(0, healthScore ?? 0));
  const circumference = 100.5;
  const dash = (safePct / 100) * circumference;

  return (
    <div className="glass-card p-8 h-full flex flex-col relative overflow-hidden group">
      {/* Subtle tint */}
      <div
        className="absolute top-0 right-0 w-72 h-72 rounded-full blur-[80px] -translate-y-1/2 translate-x-1/3 opacity-50 transition-opacity duration-1000 group-hover:opacity-80 pointer-events-none"
        style={{ background: h.ringColor }}
      />

      {/* Header row */}
      <div className="flex items-start justify-between mb-8 relative z-10">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Sparkles size={15} className="text-accent" />
            <span className="text-[10px] font-mono uppercase tracking-[0.28em] text-accent font-bold">
              Intelligence Report
            </span>
          </div>
          <h2 className="text-2xl md:text-3xl font-serif italic text-[#1D1D1F] tracking-tight">
            Executive <span className="text-[#8E8E93]">Summary</span>
          </h2>
        </div>

        {/* Health score ring */}
        <div className="flex flex-col items-center group/score shrink-0">
          <div className="relative w-[72px] h-[72px] flex items-center justify-center">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
              <circle cx="18" cy="18" r="16" fill="none" stroke="rgba(0,0,0,0.07)" strokeWidth="2.5" />
              <circle
                cx="18" cy="18" r="16"
                fill="none"
                stroke={h.color}
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeDasharray={`${dash} ${circumference}`}
                className="transition-all duration-1200 ease-out"
                style={{ filter: `drop-shadow(0 0 4px ${h.color}66)` }}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-base font-mono font-bold text-[#1D1D1F] group-hover/score:scale-110 transition-transform duration-300">
                {safePct}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-1 mt-1.5">
            <HealthIcon size={10} style={{ color: h.color }} />
            <span className="text-[9px] font-mono uppercase tracking-widest" style={{ color: h.color }}>
              {h.label}
            </span>
          </div>
        </div>
      </div>

      {/* Summary text */}
      <div className="flex-grow relative z-10">
        <div className="min-h-[100px]">
          <p className="text-[#1D1D1F] text-[17px] leading-[1.75] font-serif italic">
            {displayedText}
            {summary && index < summary.length && (
              <span className="inline-block w-[2px] h-[18px] bg-accent ml-1 animate-pulse align-text-bottom" />
            )}
          </p>
        </div>
      </div>

      {/* Stats footer */}
      <div className="mt-8 pt-5 border-t border-black/[0.06] flex flex-wrap items-center justify-between gap-3 relative z-10">
        <div className="flex items-center gap-2 bg-[#F5F5F7] px-3 py-1.5 rounded-full border border-black/[0.06]">
          <Activity size={11} className="text-accent" />
          <span className="text-[10px] font-mono text-[#6E6E73] truncate max-w-[130px]">
            {profile?.file_name || 'dataset'}
          </span>
        </div>
        <div className="flex items-center gap-3 text-[10px] font-mono text-[#8E8E93]">
          <div className="flex items-center gap-1">
            <Database size={10} />
            <span>{profile?.rows?.toLocaleString() ?? '0'} rows</span>
          </div>
          <span className="w-1 h-1 bg-black/15 rounded-full" />
          <span>{profile?.cols ?? '0'} cols</span>
          <span className="w-1 h-1 bg-black/15 rounded-full" />
          <span className="text-accent uppercase">{profile?.source_type ?? 'data'}</span>
        </div>
      </div>
    </div>
  );
};

export default SummaryPanel;
