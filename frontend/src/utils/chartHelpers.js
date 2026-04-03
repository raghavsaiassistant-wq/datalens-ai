export const formatNumber = (n) => {
  if (n === null || n === undefined) return '-';
  if (typeof n !== 'number') return n;
  if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(1) + 'K';
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
};

export const formatPercent = (n) => {
  if (n === null || typeof n !== 'number') return '-';
  return (n * 100).toFixed(1) + '%';
};

export const getImpactColor = (impact) => {
  switch (impact?.toLowerCase()) {
    case 'high': return '#EF4444'; // danger red
    case 'medium': return '#F59E0B'; // warning yellow
    case 'low': return '#10B981'; // success green
    default: return '#94A3B8'; // text secondary
  }
};

export const getSeverityColor = (severity) => {
  return getImpactColor(severity);
};

export const buildPlotlyLayout = (title) => {
  return {
    title: { text: title, font: { color: '#FFFFFF', size: 16 } },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94A3B8', family: "'Inter', sans-serif" },
    margin: { t: 40, r: 20, l: 50, b: 50 },
    xaxis: { showgrid: true, gridcolor: 'rgba(255,255,255,0.1)', zeroline: false },
    yaxis: { showgrid: true, gridcolor: 'rgba(255,255,255,0.1)', zeroline: false },
    hoverlabel: { bgcolor: '#0A0F1E', bordercolor: '#76B900', font: { color: '#FFF' } }
  };
};

export const buildPlotlyConfig = () => {
  return {
    responsive: true,
    displayModeBar: false, // Cleaner UI, custom export handled separately if needed
  };
};
