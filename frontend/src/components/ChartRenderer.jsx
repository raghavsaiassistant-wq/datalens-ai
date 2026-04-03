import React from 'react';
import Plot from 'react-plotly.js';
import { buildPlotlyLayout, buildPlotlyConfig, formatNumber } from '../utils/chartHelpers';

const ChartRenderer = ({ config }) => {
  const { chart_type, title, x_col, y_col, data } = config;
  
  if (chart_type === 'kpi_card') {
    const val = data && data.length > 0 ? data[0].y : 0;
    return (
      <div className="flex flex-col items-center justify-center p-6 h-full text-center">
        <h3 className="text-secondary text-base mb-2">{title}</h3>
        <p className="text-4xl font-bold text-white tracking-tight">{formatNumber(val)}</p>
      </div>
    );
  }

  const layout = buildPlotlyLayout("");
  const pltConfig = buildPlotlyConfig();
  
  const xData = data.map(d => d.x);
  const yData = data.map(d => d.y);
  const color = '#76B900';

  let trace = {};

  if (chart_type === 'line') {
    trace = { x: xData, y: yData, type: 'scatter', mode: 'lines+markers', marker: { color }, line: { color } };
  } else if (chart_type === 'bar') {
    trace = { x: xData, y: yData, type: 'bar', marker: { color } };
  } else if (chart_type === 'scatter') {
    trace = { x: xData, y: yData, type: 'scatter', mode: 'markers', marker: { color, size: 8 } };
  } else if (chart_type === 'pie') {
    trace = { labels: xData, values: yData, type: 'pie', marker: { colors: [color, '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444'] }, hole: 0.4 };
  } else if (chart_type === 'histogram') {
    trace = { x: xData, y: yData, type: 'bar', marker: { color } };
  } else if (chart_type === 'heatmap') {
    // Basic heatmap representation
    const zData = data.map(d => d.value);
    trace = { x: xData, y: yData, z: zData, type: 'heatmap', colorscale: 'Viridis' };
  }

  return (
    <div className="w-full h-full min-h-[300px]">
      <Plot
        data={[trace]}
        layout={{ ...layout, autosize: true }}
        config={pltConfig}
        useResizeHandler={true}
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
};

export default ChartRenderer;
