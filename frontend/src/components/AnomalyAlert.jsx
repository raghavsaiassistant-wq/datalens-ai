import React, { useState } from 'react';
import { AlertTriangle, X, Zap } from 'lucide-react';

const SEVERITY = {
  high:     { color: '#FF3B30', bg: 'rgba(255,59,48,0.06)',  border: 'rgba(255,59,48,0.20)' },
  critical: { color: '#FF3B30', bg: 'rgba(255,59,48,0.06)',  border: 'rgba(255,59,48,0.20)' },
  medium:   { color: '#FF9500', bg: 'rgba(255,149,0,0.06)',  border: 'rgba(255,149,0,0.18)' },
  low:      { color: '#0071E3', bg: 'rgba(0,113,227,0.05)',  border: 'rgba(0,113,227,0.16)' },
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
          <div className="w-10 h-10 rounded-xl bg-red-50 border border-red-200 flex items-center justify-center shadow-[0_2px_8px_rgba(255,59,48,0.08)]">
            <AlertTriangle size={18} className="text-danger" />
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase tracking-[0.28em] text-danger font-bold block mb-0.5">
              System Warning
            </span>
            <h2 className="text-xl font-serif italic text-[#1D1D1F]">
              Data <span className="text-[#8E8E93]">Anomalies</span>
            </h2>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-white border border-black/[0.08] rounded-xl shadow-sm">
          <Zap size={12} className="text-warning" />
          <span className="text-[10px] font-mono text-[#6E6E73]">
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
              className="relative rounded-2xl p-5 transition-all duration-400 hover:shadow-[0_4px_20px_rgba(0,0,0,0.10)] animate-in fade-in zoom-in-95 fill-mode-both group/card bg-white"
              style={{
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
                className="absolute top-3 right-3 text-[#8E8E93] hover:text-[#1D1D1F] transition-colors p-1 rounded-lg hover:bg-[#F5F5F7]"
              >
                <X size={12} />
              </button>

              {/* Tags */}
              <div className="flex flex-wrap gap-1.5 mb-3 pl-2">
                <span className="px-2 py-0.5 rounded-md bg-[#F5F5F7] border border-black/[0.08] text-[9px] font-mono font-bold text-[#3A3A3C] uppercase tracking-widest">
                  {flag.column}
                </span>
                <span
                  className="px-2 py-0.5 rounded-md text-[9px] font-mono font-bold uppercase tracking-widest"
                  style={{ color: sev.color, background: sev.bg, border: `1px solid ${sev.color}20` }}
                >
                  {(flag.anomaly_type || '').replaceAll('_', ' ')}
                </span>
                {flag.value != null && (
                  <span className="px-2 py-0.5 rounded-md bg-[#F5F5F7] border border-black/[0.07] text-[9px] font-mono text-[#6E6E73]">
                    {typeof flag.value === 'number'
                      ? flag.value.toLocaleString(undefined, { maximumFractionDigits: 2 })
                      : String(flag.value)}
                  </span>
                )}
              </div>

              {/* Explanation */}
              <p className="text-[#6E6E73] text-xs leading-relaxed font-serif italic pl-2">
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
