import React from 'react';
import { Search } from 'lucide-react';

const LoadingState = ({ step }) => {
  return (
    <div className="fixed inset-0 bg-primary z-50 flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full bg-card border border-white/10 rounded-2xl p-8 text-center glass-card relative overflow-hidden">
        {/* Glow effect */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-accent/20 rounded-full blur-3xl animate-pulse"></div>
        
        <div className="relative z-10">
          <div className="w-16 h-16 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-[0_0_30px_rgba(118,185,0,0.15)]">
            <Search className="text-accent animate-pulse" size={32} />
          </div>
          
          <h2 className="text-2xl font-bold text-white mb-2 tracking-tight">Analyzing Data</h2>
          <p className="text-accent font-medium mb-8 h-6">{step}</p>
          
          <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-accent to-accent-blue rounded-full animate-[progress_2s_ease-in-out_infinite] w-1/3"></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingState;
