import React, { useEffect, useState } from 'react';
import {
  FileText, Search, BrainCircuit, BarChart3, Sparkles, CheckCircle2, Loader2
} from 'lucide-react';

const STEPS = [
  { id: 1, label: 'Reading file', sub: 'Parsing & encoding detection', icon: FileText },
  { id: 2, label: 'Profiling data', sub: 'Types, nulls & statistics', icon: Search },
  { id: 3, label: 'AI processing', sub: 'Anomalies & chart selection', icon: BrainCircuit },
  { id: 4, label: 'Building charts', sub: 'Dashboard visualizations', icon: BarChart3 },
  { id: 5, label: 'Synthesizing', sub: 'Executive summary & findings', icon: Sparkles },
  { id: 6, label: 'Complete', sub: 'Dashboard ready', icon: CheckCircle2 },
];

const AnalysisProgress = ({ progress, message, startTime }) => {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (progress >= 6 || !startTime) return;
    const t = setInterval(() => setElapsed(Math.floor((Date.now() - startTime) / 1000)), 1000);
    return () => clearInterval(t);
  }, [progress, startTime]);

  const pct = Math.round((progress / 6) * 100);

  return (
    <div className="fixed inset-0 bg-[#F5F5F7] z-50 flex items-center justify-center p-6 overflow-hidden">

      <div className="max-w-xl w-full">

        {/* Title */}
        <div className="text-center mb-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-[#4a7a00] flex items-center justify-center shadow-[0_2px_8px_rgba(118,185,0,0.3)]">
              <span className="font-serif italic text-white text-base font-bold leading-none">L</span>
            </div>
            <span className="font-mono text-[11px] uppercase tracking-[0.3em] text-[#8E8E93]">DataLens AI</span>
          </div>
          <h2 className="text-3xl md:text-4xl font-serif italic text-[#1D1D1F] tracking-tight mb-3">
            Synthesizing <span className="text-accent">Intelligence</span>
          </h2>
          <div className="flex items-center justify-center gap-2 text-[#6E6E73] font-mono text-xs uppercase tracking-widest">
            {progress < 6 && <Loader2 size={12} className="animate-spin text-accent" />}
            <span>{message || 'Processing data patterns…'}</span>
          </div>
        </div>

        {/* Card */}
        <div className="bg-white border border-black/[0.08] rounded-3xl p-7 shadow-[0_4px_32px_rgba(0,0,0,0.08)]">

          {/* Progress bar */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2.5">
              <span className="text-[10px] font-mono text-[#8E8E93] uppercase tracking-widest">Progress</span>
              <span className="text-[10px] font-mono text-accent font-bold">{pct}%</span>
            </div>
            <div className="h-1.5 w-full bg-[#F5F5F7] rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700 ease-out"
                style={{
                  width: `${pct}%`,
                  background: 'linear-gradient(90deg, #76B900, #4a7a00, #0071E3)',
                  boxShadow: '0 0 8px rgba(118,185,0,0.4)',
                }}
              />
            </div>
          </div>

          {/* Steps */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {STEPS.map((step) => {
              const Icon = step.icon;
              const done = progress > step.id;
              const active = progress === step.id;
              const pending = progress < step.id;

              return (
                <div
                  key={step.id}
                  className={`flex flex-col items-center gap-2.5 p-3.5 rounded-2xl transition-all duration-500 ${
                    active
                      ? 'bg-accent/[0.06] border border-accent/20 scale-105 shadow-[0_2px_12px_rgba(118,185,0,0.10)]'
                      : done
                        ? 'bg-[#F5F5F7] border border-black/[0.06]'
                        : 'opacity-35'
                  }`}
                >
                  <div className={`
                    w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-500
                    ${done ? 'bg-accent/10 border border-accent/25'
                      : active ? 'bg-white border border-black/[0.10] shadow-sm animate-pulse'
                      : 'bg-transparent border border-black/[0.08]'}
                  `}>
                    {done
                      ? <CheckCircle2 size={20} className="text-accent" />
                      : active
                        ? <Icon size={20} className="text-[#1D1D1F]" />
                        : <Icon size={20} className="text-[#8E8E93]" />
                    }
                  </div>
                  <div className="text-center">
                    <p className={`text-[10px] font-mono font-bold uppercase tracking-tighter ${active ? 'text-[#1D1D1F]' : done ? 'text-[#6E6E73]' : 'text-[#8E8E93]'}`}>
                      {step.label}
                    </p>
                    <p className={`text-[9px] font-mono leading-tight mt-0.5 ${active ? 'text-accent' : 'text-[#8E8E93]'}`}>
                      {step.sub}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Elapsed */}
        {progress < 6 && (
          <p className="text-center mt-6 text-[#8E8E93] font-mono text-[10px] uppercase tracking-widest animate-pulse">
            {elapsed}s elapsed · NVIDIA NIM AI processing
          </p>
        )}

        {/* Creator attribution */}
        <p className="text-center mt-4 text-[#8E8E93] font-mono text-[9px] uppercase tracking-[0.3em]">
          Created by Raghav Modi · DataLens AI
        </p>
      </div>
    </div>
  );
};

export default AnalysisProgress;
