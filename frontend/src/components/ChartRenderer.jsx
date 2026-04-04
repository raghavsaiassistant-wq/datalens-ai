import React from 'react';
import Plot from 'react-plotly.js';
import { buildPlotlyLayout, buildPlotlyConfig, formatNumber } from '../utils/chartHelpers';

const ChartRenderer = ({ config }) => {
  const { chart_type, title, data } = config;
  
  if (chart_type === 'kpi_card') {
    const val = data && data.length > 0 ? data[0].y : 0;
    return (
      <div className="flex flex-col items-center justify-center p-4 h-full text-center">
        <h3 className="text-[#8E9AAF] text-[10px] font-mono uppercase tracking-widest mb-3 opacity-60">{title}</h3>
        <p className="text-4xl font-mono font-bold text-white tracking-tighter drop-shadow-sm">{formatNumber(val)}</p>
      </div>
    );
  }

  const layout = buildPlotlyLayout("");
  const pltConfig = buildPlotlyConfig();
  
  const xData = data.map(d => d.x);
  const yData = data.map(d => d.y);
  
  // Nordic Dark Palette
  const accent = '#76B900'; // NVIDIA Green
  const accentBlue = '#00E5FF'; // Electric Cyan
  const colors = [accent, accentBlue, '#FFFFFF', '#1E293B', '#475569'];

  let trace = {
    marker: { color: accent, line: { color: 'rgba(255,255,255,0.05)', width: 0.5 } },
    line: { color: accent, width: 3, shape: 'spline' }
  };

  if (chart_type === 'line') {
    trace = { ...trace, x: xData, y: yData, type: 'scatter', mode: 'lines' };
  } else if (chart_type === 'bar') {
    trace = { ...trace, x: xData, y: yData, type: 'bar' };
  } else if (chart_type === 'scatter') {
    trace = { ...trace, x: xData, y: yData, type: 'scatter', mode: 'markers', marker: { color: accentBlue, size: 10, opacity: 0.7 } };
  } else if (chart_type === 'pie') {
    trace = { labels: xData, values: yData, type: 'pie', marker: { colors }, hole: 0.6, textinfo: 'label+percent', textfont: { family: 'IBM Plex Mono', size: 10, color: '#fff' } };
  } else if (chart_type === 'histogram') {
    trace = { ...trace, x: xData, y: yData, type: 'bar' };
  }

  return (
    <div className="w-full h-full min-h-[300px] animate-in fade-in duration-1000">
      <Plot
        data={[trace]}
        layout={{ 
          ...layout, 
          autosize: true,
          paper_bgcolor: 'rgba(0,0,0,0)',
          plot_bgcolor: 'rgba(0,0,0,0)',
          font: { family: 'IBM Plex Mono', color: '#8E9AAF', size: 10 }
        }}
        config={pltConfig}
        useResizeHandler={true}
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
};

export default ChartRenderer;
