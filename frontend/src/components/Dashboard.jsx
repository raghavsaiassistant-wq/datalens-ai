import React from 'react';
import ChartRenderer from './ChartRenderer';
import { Download, BarChart2 } from 'lucide-react';

const Dashboard = ({ charts }) => {
  if (!charts || charts.length === 0) {
    return (
      <div className="glass-card p-12 text-center text-secondary border-dashed">
        <p>No actionable charts could be generated from this data.</p>
      </div>
    );
  }

  // Separate KPI cards from regular charts
  const kpiCards = charts.filter(c => c.chart_type === 'kpi_card');
  const standardCharts = charts.filter(c => c.chart_type !== 'kpi_card');

  return (
    <div className="mb-8 flex flex-col gap-8">
      {/* KPI Cards Row */}
      {kpiCards.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {kpiCards.map((kpi, idx) => (
            <div key={`kpi-${idx}`} className="glass-card overflow-hidden relative group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-accent/5 rounded-full blur-2xl group-hover:bg-accent/10 transition-colors pointer-events-none"></div>
              <ChartRenderer config={kpi} />
            </div>
          ))}
        </div>
      )}

      {/* Main Charts Grid */}
      {standardCharts.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {standardCharts.map((chart, idx) => (
            <div key={`chart-${idx}`} className="glass-card p-4 flex flex-col h-[450px]">
              {/* Header */}
              <div className="flex justify-between items-start mb-4 px-2">
                <div>
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <BarChart2 className="text-accent" size={18} />
                    {chart.title}
                  </h3>
                  <p className="text-sm text-secondary mt-1">{chart.insight_hint}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-1 bg-white/5 rounded border border-white/5 text-white/60">
                    {chart.chart_type.replace('_', ' ')}
                  </span>
                </div>
              </div>
              
              {/* Chart Render Area */}
              <div className="flex-grow w-full relative">
                <ChartRenderer config={chart} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
