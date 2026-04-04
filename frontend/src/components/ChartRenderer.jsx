import React from 'react';
import Plot from 'react-plotly.js';
import { buildPlotlyLayout, buildPlotlyConfig, formatNumber } from '../utils/chartHelpers';

const ACCENT = '#76B900';
const CYAN   = '#00E5FF';
const PALETTE = [ACCENT, CYAN, '#A78BFA', '#FB923C', '#F472B6', '#34D399', '#FFFFFF', '#FBBF24'];

const ChartRenderer = ({ config }) => {
  const { chart_type, title, data } = config;

  /* KPI Card */
  if (chart_type === 'kpi_card') {
    const val = data?.[0]?.y ?? 0;
    return (
      <div className="flex flex-col items-center justify-center p-4 h-full text-center">
        <h3 className="text-[10px] font-mono uppercase tracking-[0.28em] text-white/30 mb-3 leading-snug px-2">{title}</h3>
        <p
          className="text-4xl font-mono font-bold tracking-tighter"
          style={{ color: ACCENT, textShadow: `0 0 20px ${ACCENT}40` }}
        >
          {formatNumber(val)}
        </p>
      </div>
    );
  }

  /* Empty guard */
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-white/20 text-xs font-mono">
        No data available
      </div>
    );
  }

  const layout = {
    ...buildPlotlyLayout(''),
    autosize: true,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: "'IBM Plex Mono', monospace", color: '#8E9AAF', size: 10 },
    margin: { t: 20, r: 16, l: 50, b: 44 },
    xaxis: {
      showgrid: true, gridcolor: 'rgba(255,255,255,0.05)', zeroline: false,
      tickfont: { size: 9 }, linecolor: 'rgba(255,255,255,0.06)',
    },
    yaxis: {
      showgrid: true, gridcolor: 'rgba(255,255,255,0.05)', zeroline: false,
      tickfont: { size: 9 }, linecolor: 'rgba(255,255,255,0.06)',
    },
    hoverlabel: { bgcolor: '#0A0C10', bordercolor: ACCENT, font: { color: '#fff', size: 11 } },
    legend: { font: { color: '#8E9AAF', size: 9 }, bgcolor: 'rgba(0,0,0,0)' },
    showlegend: false,
  };

  const pltConfig = buildPlotlyConfig();

  const xData = data.map(d => d.x);
  const yData = data.map(d => d.y);

  let trace = {};

  if (chart_type === 'line') {
    trace = {
      x: xData, y: yData, type: 'scatter', mode: 'lines',
      line: { color: ACCENT, width: 2.5, shape: 'spline', smoothing: 0.8 },
      fill: 'tozeroy',
      fillcolor: `${ACCENT}12`,
    };
  } else if (chart_type === 'bar') {
    trace = {
      x: xData, y: yData, type: 'bar',
      marker: {
        color: yData.map((_, i) => i === 0 ? ACCENT : `${ACCENT}80`),
        line: { color: 'rgba(0,0,0,0)', width: 0 },
      },
    };
  } else if (chart_type === 'scatter') {
    trace = {
      x: xData, y: yData, type: 'scatter', mode: 'markers',
      marker: { color: CYAN, size: 7, opacity: 0.65, line: { color: `${CYAN}40`, width: 1 } },
    };
  } else if (chart_type === 'pie') {
    trace = {
      labels: xData, values: yData, type: 'pie',
      marker: { colors: PALETTE },
      hole: 0.58,
      textinfo: 'label+percent',
      textfont: { family: "'IBM Plex Mono', monospace", size: 9, color: '#fff' },
      outsidetextfont: { size: 9 },
    };
    layout.margin = { t: 10, r: 10, l: 10, b: 10 };
    layout.showlegend = true;
  } else if (chart_type === 'histogram') {
    trace = {
      x: xData, y: yData, type: 'bar',
      marker: {
        color: PALETTE.map((c, i) => `${c}${i === 0 ? '' : '70'}`)[0],
        line: { color: 'rgba(0,0,0,0)', width: 0 },
      },
    };
  } else if (chart_type === 'heatmap') {
    const colLabels = [...new Set(data.map(d => d.x))];
    const rowLabels = [...new Set(data.map(d => d.y))];
    const zMatrix = rowLabels.map(row =>
      colLabels.map(col => {
        const cell = data.find(d => d.x === col && d.y === row);
        return cell ? cell.value : 0;
      })
    );
    trace = {
      x: colLabels, y: rowLabels, z: zMatrix, type: 'heatmap',
      colorscale: [
        [0, '#0A1628'],
        [0.25, '#0d2b1a'],
        [0.5, '#1a4a1f'],
        [0.75, '#4a8000'],
        [1, ACCENT],
      ],
      showscale: true,
      hoverongaps: false,
      text: zMatrix.map(row => row.map(v => (typeof v === 'number' ? v.toFixed(2) : v))),
      texttemplate: '%{text}',
      textfont: { size: 8, color: '#fff' },
      colorbar: {
        tickfont: { color: '#8E9AAF', size: 8 },
        thickness: 10,
        len: 0.8,
      },
    };
    layout.margin = { t: 20, r: 60, l: 80, b: 80 };
    layout.xaxis = { ...layout.xaxis, tickangle: -35, tickfont: { size: 8 } };
    layout.yaxis = { ...layout.yaxis, tickfont: { size: 8 } };
  } else {
    /* Unknown chart type fallback */
    trace = { x: xData, y: yData, type: 'bar', marker: { color: ACCENT } };
  }

  return (
    <div className="w-full h-full min-h-[280px] animate-in fade-in duration-700">
      <Plot
        data={[trace]}
        layout={layout}
        config={pltConfig}
        useResizeHandler
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
};

export default ChartRenderer;
