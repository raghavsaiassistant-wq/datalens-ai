import React from 'react';
import { Target, Flame, Clock, Leaf } from 'lucide-react';

const PRIORITY = {
  immediate:    { color: '#FF3B30', bg: 'rgba(255,59,48,0.06)',   icon: Flame,  label: 'Immediate' },
  'short-term': { color: '#FF9500', bg: 'rgba(255,149,0,0.06)',   icon: Clock,  label: 'Short-term' },
  'long-term':  { color: '#34C759', bg: 'rgba(52,199,89,0.06)',   icon: Leaf,   label: 'Long-term' },
};

const getPriority = (p) => PRIORITY[p?.toLowerCase()] || PRIORITY['long-term'];

const NextSteps = ({ steps }) => {
  if (!steps || steps.length === 0) return null;

  return (
    <div className="glass-card p-8 md:p-10 relative overflow-hidden group">
      {/* Header */}
      <div className="flex items-center gap-3 mb-10 relative z-10">
        <div className="w-11 h-11 rounded-2xl bg-accent-blue/[0.08] border border-accent-blue/[0.18] flex items-center justify-center">
          <Target size={20} className="text-accent-blue" />
        </div>
        <div>
          <span className="text-[10px] font-mono uppercase tracking-[0.28em] text-accent-blue font-bold block mb-0.5">
            Strategic Roadmap
          </span>
          <h2 className="text-2xl font-serif italic text-[#1D1D1F]">
            Recommended <span className="text-[#8E8E93]">Actions</span>
          </h2>
        </div>
      </div>

      {/* Steps */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
        {steps.map((step, i) => {
          const p = getPriority(step.priority);
          const PIcon = p.icon;

          return (
            <div
              key={i}
              className="relative rounded-3xl p-7 border border-black/[0.06] bg-[#F5F5F7] hover:border-black/[0.12] hover:bg-white hover:shadow-[0_6px_28px_rgba(0,0,0,0.08)] transition-all duration-500 overflow-hidden group/step animate-in slide-in-from-bottom-4 fade-in fill-mode-both"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              {/* Step number background */}
              <div className="absolute -top-6 -right-4 text-[80px] font-serif italic font-bold text-black/[0.04] group-hover/step:text-black/[0.07] transition-colors select-none pointer-events-none leading-none">
                {i + 1}
              </div>

              {/* Priority badge */}
              <div
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[9px] font-mono font-bold uppercase tracking-[0.2em] mb-5"
                style={{ color: p.color, background: p.bg, border: `1px solid ${p.color}25` }}
              >
                <PIcon size={9} />
                {p.label}
              </div>

              {/* Action */}
              <h3 className="text-[#1D1D1F] text-lg font-serif italic mb-3 leading-snug group-hover/step:text-accent-blue transition-colors duration-400 relative z-10">
                {step.action}
              </h3>

              {/* Reason */}
              <p className="text-[#6E6E73] text-xs leading-relaxed font-light relative z-10">
                {step.reason}
              </p>

              {/* Bottom accent line */}
              <div
                className="absolute bottom-0 left-6 right-6 h-px opacity-0 group-hover/step:opacity-100 transition-opacity duration-500"
                style={{ background: `linear-gradient(90deg, transparent, ${p.color}40, transparent)` }}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default NextSteps;
