import React from 'react';
import { Lightbulb, TrendingUp, TrendingDown, Minus } from 'lucide-react';

const IMPACT = {
  high:   { color: '#FF3B3B', bg: 'rgba(255,59,59,0.08)',   label: 'High',   icon: TrendingUp },
  medium: { color: '#FFB800', bg: 'rgba(255,184,0,0.08)',   label: 'Medium', icon: Minus },
  low:    { color: '#00E5FF', bg: 'rgba(0,229,255,0.08)',   label: 'Low',    icon: TrendingDown },
};

const FindingsCard = ({ findings }) => {
  if (!findings || findings.length === 0) return null;

  return (
    <div className="glass-card p-8 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 mb-7">
        <div className="w-9 h-9 rounded-xl bg-accent/[0.08] border border-accent/[0.18] flex items-center justify-center shrink-0">
          <Lightbulb size={16} className="text-accent" />
        </div>
        <div>
          <span className="text-[10px] font-mono uppercase tracking-[0.28em] text-accent font-bold block mb-0.5">
            Critical Insights
          </span>
          <h2 className="text-xl font-serif italic text-white">
            Key <span className="text-white/35">Findings</span>
          </h2>
        </div>
      </div>

      {/* Finding cards */}
      <div className="flex flex-col gap-4 flex-grow">
        {findings.map((f, i) => {
          const impact = f.impact?.toLowerCase();
          const cfg = IMPACT[impact] || IMPACT.low;
          const ImpactIcon = cfg.icon;

          return (
            <div
              key={i}
              className="group/item flex items-start gap-4 p-5 rounded-2xl bg-white/[0.015] border border-white/[0.06] hover:border-white/15 hover:bg-white/[0.03] transition-all duration-400 animate-in slide-in-from-right-4 fade-in fill-mode-both"
              style={{ animationDelay: `${i * 80}ms` }}
            >
              {/* Impact indicator */}
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mt-0.5"
                style={{ background: cfg.bg, border: `1px solid ${cfg.color}25` }}
              >
                <ImpactIcon size={15} style={{ color: cfg.color }} />
              </div>

              <div className="flex-grow min-w-0">
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <h3 className="text-white/90 text-sm font-semibold tracking-tight group-hover/item:text-accent transition-colors leading-snug">
                    {f.headline}
                  </h3>
                  <span
                    className="text-[9px] font-mono font-bold uppercase tracking-widest px-2 py-0.5 rounded-full shrink-0"
                    style={{ color: cfg.color, background: cfg.bg }}
                  >
                    {cfg.label}
                  </span>
                </div>
                <p className="text-white/40 text-xs leading-relaxed font-light border-l-2 pl-3" style={{ borderColor: `${cfg.color}30` }}>
                  {f.detail}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default FindingsCard;
