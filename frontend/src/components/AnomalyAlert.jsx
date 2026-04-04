import React, { useState } from 'react';
import { AlertTriangle, X, ShieldAlert, Zap } from 'lucide-react';

const AnomalyAlert = ({ anomalies }) => {
  const [flags, setFlags] = useState(anomalies || []);
  const [isVisible, setIsVisible] = useState(true);

  if (!flags || flags.length === 0 || !isVisible) return null;

  const dismiss = (index) => {
    const newFlags = flags.filter((_, i) => i !== index);
    setFlags(newFlags);
    if (newFlags.length === 0) setIsVisible(false);
  };

  const getSeverityData = (s) => {
    const low = s?.toLowerCase();
    if (low === 'high' || low === 'critical') return { color: '#FF3B3B', bg: 'bg-danger/10' };
    if (low === 'medium') return { color: '#FFB800', bg: 'bg-warning/10' };
    return { color: '#00E5FF', bg: 'bg-accent-blue/10' };
  };

  return (
    <div className="mb-12 animate-in fade-in slide-in-from-top-6 duration-700">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-danger/10 flex items-center justify-center border border-danger/20 shadow-[0_0_20px_rgba(255,59,59,0.1)]">
            <AlertTriangle className="text-danger" size={24} />
          </div>
          <div>
            <span className="text-[10px] uppercase tracking-[0.3em] text-danger font-bold block mb-0.5 animate-pulse">System Warning</span>
            <h2 className="text-3xl font-serif text-white italic">Data <span className="text-white/40">Anomalies</span></h2>
          </div>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl">
          <Zap size={14} className="text-warning" />
          <span className="text-xs font-mono text-white uppercase tracking-widest">{flags.length} Potential Issues</span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {flags.map((flag, i) => {
          const { color, bg } = getSeverityData(flag.severity);
          return (
            <div 
              key={i}
              className={`glass-card p-6 relative flex items-start gap-4 border-l-2 transition-all duration-500 hover:scale-[1.02] shadow-xl group/alert animate-in fade-in zoom-in-95 fill-mode-both animate-stagger-${Math.min(i+1, 4)}`}
              style={{ borderLeftColor: color }}
            >
              <button 
                onClick={() => dismiss(i)}
                className="absolute top-3 right-3 text-white/10 hover:text-white transition-colors p-1"
              >
                <X size={14} />
              </button>
              
              <div className="flex-grow">
                <div className="flex flex-wrap gap-2 mb-3 items-center">
                  <div className="px-2 py-1 rounded bg-white/10 border border-white/5 text-[9px] font-mono font-bold text-white uppercase tracking-widest">
                    {flag.column}
                  </div>
                  <div className={`px-2 py-1 rounded ${bg} border border-white/5 text-[9px] font-mono font-bold uppercase tracking-widest`} style={{ color }}>
                    {flag.anomaly_type.replace('_', ' ')}
                  </div>
                </div>
                <p className="text-sm text-[#8E9AAF] leading-relaxed font-serif italic border-l border-white/5 pl-3">
                  {flag.explanation}
                </p>
                <div className="mt-4 flex items-center gap-2 opacity-0 group-hover/alert:opacity-100 transition-opacity">
                  <ShieldAlert size={12} className="text-white/20" />
                  <span className="text-[9px] text-white/20 font-mono uppercase tracking-widest">Statistical Outlier Protocol</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AnomalyAlert;
