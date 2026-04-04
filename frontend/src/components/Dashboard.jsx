import React from 'react';
import ChartRenderer from './ChartRenderer';
import { BarChart2, LayoutDashboard, Zap } from 'lucide-react';

const Dashboard = ({ charts }) => {
  if (!charts || charts.length === 0) {
    return (
      <div className="glass-card p-24 text-center border-dashed group">
        <div className="w-20 h-20 bg-white/5 rounded-3xl flex items-center justify-center mx-auto mb-6 border border-white/10 group-hover:bg-accent/10 transition-colors duration-500">
          <LayoutDashboard className="text-white/20 group-hover:text-accent transition-colors" size={32} />
        </div>
        <h3 className="text-2xl font-serif text-white italic mb-2">Non-visualizable Data</h3>
        <p className="text-[#8E9AAF] font-serif italic opacity-60">The current data structure does not support standardized visualization protocols.</p>
      </div>
    );
  }

  const kpiCards = charts.filter(c => c.chart_type === 'kpi_card');
  const standardCharts = charts.filter(c => c.chart_type !== 'kpi_card');

  return (
    <div className="mb-12 flex flex-col gap-12">
      {/* KPI Cards Row */}
      {kpiCards.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {kpiCards.map((kpi, idx) => (
            <div 
              key={`kpi-${idx}`} 
              className={`glass-card p-6 overflow-hidden relative group animate-in zoom-in-95 fade-in fill-mode-both animate-stagger-${Math.min(idx+1, 4)} shadow-xl`}
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-accent/5 rounded-full blur-2xl group-hover:bg-accent/10 transition-all duration-1000 pointer-events-none"></div>
              <div className="relative z-10">
                <ChartRenderer config={kpi} />
                <div className="mt-4 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                  <Zap size={10} className="text-accent" />
                  <span className="text-[9px] font-mono text-accent uppercase tracking-widest font-bold">Real-time Metric</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Main Charts Grid */}
      {standardCharts.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          {standardCharts.map((chart, idx) => (
            <div 
              key={`chart-${idx}`} 
              className={`glass-card p-8 flex flex-col h-[520px] group transition-all duration-700 hover:shadow-[0_20px_80px_rgba(0,0,0,0.4)] animate-in slide-in-from-bottom-8 fade-in fill-mode-both animate-stagger-${Math.min(idx+1, 4)}`}
            >
              {/* Header */}
              <div className="flex justify-between items-start mb-8 px-2 relative z-20">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 mb-1">
                    <BarChart2 className="text-accent" size={16} />
                    <span className="text-[10px] uppercase tracking-[0.3em] text-accent font-bold">Visualization Model</span>
                  </div>
                  <h3 className="text-2xl font-serif text-white italic group-hover:text-accent transition-colors duration-500">
                    {chart.title}
                  </h3>
                  <p className="text-xs text-[#8E9AAF] italic opacity-70 border-l border-white/10 pl-3 leading-relaxed">
                    {chart.insight_hint}
                  </p>
                </div>
                <div className="shrink-0">
                  <span className="text-[9px] font-mono font-bold uppercase tracking-widest px-3 py-1.5 bg-white/[0.03] rounded-full border border-white/10 text-white/40 group-hover:text-accent group-hover:border-accent/40 transition-all duration-500">
                    {chart.chart_type.replaceAll('_', ' ')}
                  </span>
                </div>
              </div>
              
              {/* Chart Render Area */}
              <div className="flex-grow w-full relative z-10 overflow-hidden rounded-2xl bg-white/[0.01] border border-white/5">
                <ChartRenderer config={chart} />
              </div>
              
              {/* Footer deco */}
              <div className="mt-6 flex justify-between items-center px-2 opacity-0 group-hover:opacity-100 transition-opacity duration-700">
                <span className="text-[9px] font-mono text-white/10 tracking-[0.4em] uppercase">Architecture v1.0</span>
                <div className="flex gap-1">
                  <div className="w-1 h-1 rounded-full bg-accent animate-pulse"></div>
                  <div className="w-1 h-1 rounded-full bg-accent animate-pulse delay-700"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
