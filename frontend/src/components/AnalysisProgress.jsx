import React, { useEffect, useState } from 'react';
import { 
  FileText, 
  Search, 
  BrainCircuit, 
  BarChart3, 
  Sparkles, 
  CheckCircle2,
  Loader2
} from 'lucide-react';

const STEPS = [
  { id: 1, label: "Reading your file...", icon: FileText },
  { id: 2, label: "Profiling your data...", icon: Search },
  { id: 3, label: "Sending to AI...", icon: BrainCircuit },
  { id: 4, label: "Building your dashboard...", icon: BarChart3 },
  { id: 5, label: "Finalizing insights...", icon: Sparkles },
  { id: 6, label: "Your analysis is ready!", icon: CheckCircle2 }
];

const AnalysisProgress = ({ progress, message }) => {
  const [timeLeft, setTimeLeft] = useState(15);

  useEffect(() => {
    if (progress < 6 && timeLeft > 0) {
      const timer = setInterval(() => setTimeLeft(prev => Math.max(0, prev - 1)), 1000);
      return () => clearInterval(timer);
    }
  }, [progress, timeLeft]);

  return (
    <div className="fixed inset-0 bg-[#0A0C10] z-50 flex items-center justify-center p-6 overflow-hidden font-sans">
      {/* Background Cinematic Particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-accent/10 rounded-full blur-[120px] animate-pulse"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent-blue/10 rounded-full blur-[120px] animate-pulse delay-700"></div>
        <div className="grid grid-cols-8 gap-4 opacity-[0.03] rotate-12 scale-150">
          {Array.from({ length: 64 }).map((_, i) => (
            <div key={i} className="h-20 w-20 border border-white rounded-lg"></div>
          ))}
        </div>
      </div>

      <div className="max-w-2xl w-full relative z-10">
        <div className="text-center mb-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <h2 className="text-4xl font-serif text-white mb-3 italic tracking-tight">
            Synthesizing <span className="text-accent italic">Intelligence</span>
          </h2>
          <p className="text-[#8E9AAF] font-mono text-sm uppercase tracking-widest flex items-center justify-center gap-2">
            {progress < 6 ? <Loader2 size={14} className="animate-spin" /> : null}
            {message || "Processing data patterns..."}
          </p>
        </div>

        {/* Progress Bar Container */}
        <div className="bg-white/5 border border-white/10 rounded-3xl p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden">
          {/* Main Bar */}
          <div className="h-2 w-full bg-white/5 rounded-full mb-12 overflow-hidden relative">
            <div 
              className="h-full bg-gradient-to-r from-accent via-accent-blue to-accent rounded-full transition-all duration-1000 ease-out shadow-[0_0_20px_rgba(118,185,0,0.4)]"
              style={{ width: `${(progress / 6) * 100}%` }}
            ></div>
          </div>

          {/* Steps Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-y-10 gap-x-4">
            {STEPS.map((step) => {
              const Icon = step.icon;
              const isCompleted = progress > step.id;
              const isActive = progress === step.id;
              const isPending = progress < step.id;

              return (
                <div 
                  key={step.id} 
                  className={`flex flex-col items-center gap-3 transition-all duration-500 ${
                    isActive ? "scale-110 opacity-100" : isCompleted ? "opacity-100" : "opacity-30"
                  }`}
                >
                  <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border-2 transition-all duration-500 ${
                    isCompleted ? "bg-accent/10 border-accent shadow-[0_0_15px_rgba(118,185,0,0.2)]" :
                    isActive ? "bg-white/5 border-white/40 animate-pulse" :
                    "bg-transparent border-white/10"
                  }`}>
                    {isCompleted ? (
                      <CheckCircle2 size={24} className="text-accent" />
                    ) : (
                      <Icon size={24} className={isActive ? "text-white" : "text-white/40"} />
                    )}
                  </div>
                  <span className={`text-[11px] font-mono uppercase tracking-tighter text-center max-w-[100px] leading-tight ${
                    isActive ? "text-white font-bold" : "text-white/40"
                  }`}>
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {progress < 6 && (
          <p className="text-center mt-8 text-[#8E9AAF] font-mono text-[10px] uppercase tracking-widest animate-pulse">
            Estimated time remaining: ~{timeLeft} seconds
          </p>
        )}
      </div>
    </div>
  );
};

export default AnalysisProgress;
