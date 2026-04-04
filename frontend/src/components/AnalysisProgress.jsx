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
    <div className="fixed inset-0 bg-[#060810] z-50 flex items-center justify-center p-6 overflow-hidden">

      {/* Ambient glows */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-15%] left-[-10%] w-[55%] h-[55%] bg-accent/[0.07] rounded-full blur-[150px] animate-pulse" />
        <div className="absolute bottom-[-15%] right-[-10%] w-[50%] h-[50%] bg-accent-blue/[0.06] rounded-full blur-[140px] animate-pulse" style={{ animationDelay: '1s' }} />
        {/* Grid */}
        <div
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,0.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.6) 1px, transparent 1px)',
            backgroundSize: '50px 50px',
          }}
        />
      </div>

      <div className="max-w-xl w-full relative z-10">

        {/* Title */}
        <div className="text-center mb-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-[#4a7a00] flex items-center justify-center shadow-[0_0_16px_rgba(118,185,0,0.4)]">
              <span className="font-serif italic text-white text-base font-bold leading-none">L</span>
            </div>
            <span className="font-mono text-[11px] uppercase tracking-[0.3em] text-white/30">DataLens AI</span>
          </div>
          <h2 className="text-3xl md:text-4xl font-serif italic text-white tracking-tight mb-3">
            Synthesizing <span className="text-accent">Intelligence</span>
          </h2>
          <div className="flex items-center justify-center gap-2 text-white/35 font-mono text-xs uppercase tracking-widest">
            {progress < 6 && <Loader2 size={12} className="animate-spin text-accent" />}
            <span>{message || 'Processing data patterns…'}</span>
          </div>
        </div>

        {/* Card */}
        <div className="bg-white/[0.025] border border-white/[0.07] rounded-3xl p-7 backdrop-blur-xl shadow-2xl">

          {/* Progress bar */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2.5">
              <span className="text-[10px] font-mono text-white/30 uppercase tracking-widest">Progress</span>
              <span className="text-[10px] font-mono text-accent font-bold">{pct}%</span>
            </div>
            <div className="h-1.5 w-full bg-white/[0.05] rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700 ease-out shadow-[0_0_12px_rgba(118,185,0,0.5)]"
                style={{
                  width: `${pct}%`,
                  background: 'linear-gradient(90deg, #76B900, #a0d400, #00E5FF)',
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
                      ? 'bg-accent/[0.08] border border-accent/25 scale-105'
                      : done
                        ? 'bg-white/[0.02] border border-white/[0.05]'
                        : 'opacity-25'
                  }`}
                >
                  <div className={`
                    w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-500
                    ${done ? 'bg-accent/15 border border-accent/30 shadow-[0_0_12px_rgba(118,185,0,0.15)]'
                      : active ? 'bg-white/[0.06] border border-white/20 animate-pulse'
                      : 'bg-transparent border border-white/10'}
                  `}>
                    {done
                      ? <CheckCircle2 size={20} className="text-accent" />
                      : active
                        ? <Icon size={20} className="text-white" />
                        : <Icon size={20} className="text-white/30" />
                    }
                  </div>
                  <div className="text-center">
                    <p className={`text-[10px] font-mono font-bold uppercase tracking-tighter ${active ? 'text-white' : done ? 'text-white/60' : 'text-white/25'}`}>
                      {step.label}
                    </p>
                    <p className={`text-[9px] font-mono leading-tight mt-0.5 ${active ? 'text-accent/70' : 'text-white/20'}`}>
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
          <p className="text-center mt-6 text-white/20 font-mono text-[10px] uppercase tracking-widest animate-pulse">
            {elapsed}s elapsed · NVIDIA NIM AI processing
          </p>
        )}

        {/* Creator attribution */}
        <p className="text-center mt-4 text-white/10 font-mono text-[9px] uppercase tracking-[0.3em]">
          Created by Raghav Modi · DataLens AI
        </p>
      </div>
    </div>
  );
};

export default AnalysisProgress;
