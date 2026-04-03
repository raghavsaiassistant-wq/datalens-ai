import React from 'react';
import { Sparkles, Activity } from 'lucide-react';

const SummaryPanel = ({ summary, healthScore, profile }) => {
  const getHealthColor = (score) => {
    if (score >= 80) return '#10B981';
    if (score >= 60) return '#F59E0B';
    return '#EF4444';
  };

  const healthColor = getHealthColor(healthScore);

  return (
    <div className="glass-card gradient-border p-6 h-full flex flex-col relative overflow-hidden">
      <div className="absolute top-0 right-0 w-64 h-64 bg-accent/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3"></div>
      
      <div className="flex justify-between items-start mb-6 relative z-10">
        <div className="flex items-center gap-2">
          <Sparkles className="text-accent" size={24} />
          <h2 className="text-xl font-semibold text-white">Executive Summary</h2>
        </div>
        
        <div className="flex flex-col items-center">
          <div className="relative w-16 h-16 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="rgba(255,255,255,0.1)"
                strokeWidth="3"
              />
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke={healthColor}
                strokeWidth="3"
                strokeDasharray={`${healthScore}, 100`}
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-sm font-bold text-white">{healthScore}</span>
            </div>
          </div>
          <span className="text-[10px] uppercase tracking-wider text-secondary mt-1 font-semibold">Health Score</span>
        </div>
      </div>
      
      <div className="flex-grow relative z-10">
        <p className="text-white/90 leading-relaxed text-md font-light">
          {summary}
        </p>
      </div>

      <div className="mt-8 pt-4 border-t border-white/10 flex justify-between text-xs text-secondary relative z-10 font-medium">
        <span className="truncate max-w-[50%] flex items-center gap-1">
          <Activity size={14}/> {profile?.file_name}
        </span>
        <span>{profile?.rows?.toLocaleString()} rows × {profile?.cols} cols ({profile?.source_type})</span>
      </div>
    </div>
  );
};

export default SummaryPanel;
