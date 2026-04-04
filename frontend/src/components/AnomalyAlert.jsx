import React, { useState } from 'react';
import { AlertTriangle, X, Zap } from 'lucide-react';

const SEVERITY = {
  high:     { color: '#FF3B3B', bg: 'rgba(255,59,59,0.07)',   border: 'rgba(255,59,59,0.25)',   dot: '#FF3B3B' },
  critical: { color: '#FF3B3B', bg: 'rgba(255,59,59,0.07)',   border: 'rgba(255,59,59,0.25)',   dot: '#FF3B3B' },
  medium:   { color: '#FFB800', bg: 'rgba(255,184,0,0.07)',   border: 'rgba(255,184,0,0.22)',   dot: '#FFB800' },
  low:      { color: '#00E5FF', bg: 'rgba(0,229,255,0.06)',   border: 'rgba(0,229,255,0.20)',   dot: '#00E5FF' },
};

const getSev = (s) => SEVERITY[s?.toLowerCase()] || SEVERITY.low;

const AnomalyAlert = ({ anomalies }) => {
  const [flags, setFlags] = useState(anomalies || []);
  const [visible, setVisible] = useState(true);

  if (!flags.length || !visible) return null;

  const dismiss = (i) => {
    const next = flags.filter((_, idx) => idx !== i);
    setFlags(next);
    if (!next.length) setVisible(false);
  };

  const highCount = flags.filter(f => ['high','critical'].includes(f.severity?.toLowerCase())).length;

  return (
    <div className="animate-in fade-in slide-in-from-top-4 duration-700">
      {/* Section header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-danger/[0.08] border border-danger/20 flex items-center justify-center shadow-[0_0_16px_rgba(255,59,59,0.08)]">
            <AlertTriangle size={18} className="text-danger" />
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase tracking-[0.28em] text-danger font-bold block mb-0.5">
              System Warning
            </span>
            <h2 className="text-xl font-serif italic text-white">
              Data <span className="text-white/35">Anomalies</span>
            </h2>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-white/[0.03] border border-white/[0.08] rounded-xl">
          <Zap size={12} className="text-warning" />
          <span className="text-[10px] font-mono text-white/50">
            {flags.length} issue{flags.length !== 1 ? 's' : ''}
            {highCount > 0 && <span className="ml-1 text-danger">· {highCount} high</span>}
          </span>
        </div>
      </div>

      {/* Cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {flags.map((flag, i) => {
          const sev = getSev(flag.severity);
          return (
            <div
              key={i}
              className="relative rounded-2xl p-5 transition-all duration-400 hover:scale-[1.01] animate-in fade-in zoom-in-95 fill-mode-both group/card"
              style={{
                background: sev.bg,
                border: `1px solid ${sev.border}`,
                animationDelay: `${i * 60}ms`,
              }}
            >
              {/* Left accent bar */}
              <div
                className="absolute left-0 top-4 bottom-4 w-0.5 rounded-full"
                style={{ background: sev.color }}
              />

              {/* Dismiss */}
              <button
                onClick={() => dismiss(i)}
                className="absolute top-3 right-3 text-white/15 hover:text-white/60 transition-colors p-1 rounded-lg hover:bg-white/5"
              >
                <X size={12} />
              </button>

              {/* Tags */}
              <div className="flex flex-wrap gap-1.5 mb-3 pl-2">
                <span className="px-2 py-0.5 rounded-md bg-white/[0.06] border border-white/[0.08] text-[9px] font-mono font-bold text-white/60 uppercase tracking-widest">
                  {flag.column}
                </span>
                <span
                  className="px-2 py-0.5 rounded-md text-[9px] font-mono font-bold uppercase tracking-widest"
                  style={{ color: sev.color, background: `${sev.color}12`, border: `1px solid ${sev.color}22` }}
                >
                  {(flag.anomaly_type || '').replaceAll('_', ' ')}
                </span>
                {flag.value != null && (
                  <span className="px-2 py-0.5 rounded-md bg-white/[0.04] border border-white/[0.06] text-[9px] font-mono text-white/35">
                    {typeof flag.value === 'number'
                      ? flag.value.toLocaleString(undefined, { maximumFractionDigits: 2 })
                      : String(flag.value)}
                  </span>
                )}
              </div>

              {/* Explanation */}
              <p className="text-white/50 text-xs leading-relaxed font-serif italic pl-2">
                {flag.explanation || 'Anomaly detected in this column.'}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AnomalyAlert;
