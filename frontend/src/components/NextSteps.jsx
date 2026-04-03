import React from 'react';
import { Target } from 'lucide-react';

const NextSteps = ({ steps }) => {
  if (!steps || steps.length === 0) return null;

  const getPriorityColor = (p) => {
    switch(p?.toLowerCase()) {
      case 'immediate': return 'bg-danger text-white';
      case 'short-term': return 'bg-warning text-white';
      default: return 'bg-success text-white';
    }
  };

  return (
    <div className="glass-card p-6 mb-8">
      <div className="flex items-center gap-2 mb-6">
        <Target className="text-accent-blue" size={24} />
        <h2 className="text-xl font-semibold text-white">Recommended Actions</h2>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {steps.map((step, i) => (
          <div key={i} className="bg-white/5 rounded-xl p-5 border border-white/5 relative overflow-hidden group hover:border-white/20 transition-all">
            <div className="absolute top-0 right-0 p-4 text-white/5 font-black text-6xl group-hover:text-white/10 transition-colors pointer-events-none select-none">
              {i+1}
            </div>
            <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-1 rounded mb-3 inline-block ${getPriorityColor(step.priority)}`}>
              {step.priority}
            </span>
            <h3 className="text-lg font-semibold text-white mb-2 relative z-10">{step.action}</h3>
            <p className="text-sm text-secondary relative z-10">{step.reason}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NextSteps;
