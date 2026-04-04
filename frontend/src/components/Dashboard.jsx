import React from 'react';
import ChartRenderer from './ChartRenderer';
import { BarChart2, LayoutDashboard, Zap, TrendingUp } from 'lucide-react';

const CHART_TYPE_LABEL = {
  line: 'Time Series',
  bar: 'Bar Chart',
  scatter: 'Scatter Plot',
  pie: 'Distribution',
  histogram: 'Histogram',
  heatmap: 'Correlation',
};

const Dashboard = ({ charts }) => {
  if (!charts || charts.length === 0) {
    return (
      <div className="glass-card p-20 text-center border-dashed group">
        <div className="w-16 h-16 bg-white/[0.03] rounded-3xl flex items-center justify-center mx-auto mb-5 border border-white/[0.07] group-hover:bg-accent/[0.06] group-hover:border-accent/20 transition-all duration-500">
          <LayoutDashboard size={28} className="text-white/15 group-hover:text-accent/60 transition-colors" />
        </div>
        <h3 className="text-xl font-serif italic text-white mb-2">No Visualizable Data</h3>
        <p className="text-white/30 font-serif italic text-sm opacity-70">
          The current data structure does not support chart generation.
        </p>
      </div>
    );
  }

  const kpiCards = charts.filter(c => c.chart_type === 'kpi_card');
  const mainCharts = charts.filter(c => c.chart_type !== 'kpi_card');

  return (
    <div className="flex flex-col gap-8">

      {/* KPI Cards */}
      {kpiCards.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={14} className="text-accent" />
            <span className="text-[10px] font-mono uppercase tracking-[0.25em] text-accent/70 font-bold">
              Key Performance Indicators
            </span>
          </div>
          <div className={`grid gap-4 ${
            kpiCards.length === 1 ? 'grid-cols-1 max-w-xs' :
            kpiCards.length === 2 ? 'grid-cols-2 max-w-lg' :
            kpiCards.length === 3 ? 'grid-cols-3' :
            'grid-cols-2 md:grid-cols-4'
          }`}>
            {kpiCards.map((kpi, idx) => (
              <div
                key={`kpi-${idx}`}
                className="glass-card p-6 overflow-hidden relative group/kpi animate-in zoom-in-95 fade-in fill-mode-both"
                style={{ animationDelay: `${idx * 80}ms` }}
              >
                <div className="absolute top-0 right-0 w-28 h-28 bg-accent/[0.04] rounded-full blur-2xl group-hover/kpi:bg-accent/[0.08] transition-all duration-700 pointer-events-none" />
                <div className="relative z-10">
                  <ChartRenderer config={kpi} />
                  <div className="mt-3 flex items-center gap-1.5 opacity-0 group-hover/kpi:opacity-100 transition-opacity duration-400">
                    <Zap size={9} className="text-accent" />
                    <span className="text-[9px] font-mono text-accent uppercase tracking-widest">Live Metric</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Charts */}
      {mainCharts.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <BarChart2 size={14} className="text-accent-blue" />
            <span className="text-[10px] font-mono uppercase tracking-[0.25em] text-accent-blue/70 font-bold">
              Visualization Models
            </span>
          </div>
          <div className={`grid gap-6 ${mainCharts.length === 1 ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-2'}`}>
            {mainCharts.map((chart, idx) => (
              <div
                key={`chart-${idx}`}
                className="glass-card p-6 flex flex-col h-[480px] group/chart transition-all duration-500 hover:shadow-[0_16px_60px_rgba(0,0,0,0.4)] animate-in slide-in-from-bottom-6 fade-in fill-mode-both"
                style={{ animationDelay: `${idx * 100}ms` }}
              >
                {/* Chart header */}
                <div className="flex items-start justify-between mb-5 px-1">
                  <div>
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <BarChart2 size={11} className="text-accent/60" />
                      <span className="text-[9px] font-mono uppercase tracking-[0.25em] text-accent/50">
                        {CHART_TYPE_LABEL[chart.chart_type] || chart.chart_type}
                      </span>
                    </div>
                    <h3 className="text-lg font-serif italic text-white group-hover/chart:text-accent transition-colors duration-400 leading-tight">
                      {chart.title}
                    </h3>
                    {chart.insight_hint && (
                      <p className="text-[11px] text-white/30 mt-1 italic border-l border-white/10 pl-2 leading-snug">
                        {chart.insight_hint}
                      </p>
                    )}
                  </div>
                  <span className="text-[9px] font-mono font-bold uppercase tracking-widest px-2.5 py-1 bg-white/[0.02] rounded-full border border-white/[0.06] text-white/30 group-hover/chart:text-accent/60 group-hover/chart:border-accent/20 transition-all duration-400 shrink-0 ml-2">
                    {chart.chart_type}
                  </span>
                </div>

                {/* Chart area */}
                <div className="flex-grow w-full bg-white/[0.008] rounded-2xl border border-white/[0.04] overflow-hidden">
                  <ChartRenderer config={chart} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
