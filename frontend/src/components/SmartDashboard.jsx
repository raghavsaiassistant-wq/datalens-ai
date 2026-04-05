/**
 * SmartDashboard.jsx
 *
 * v2.0 dashboard composition layer.
 * Renders FilterBar + InsightsPanel above the existing Dashboard component.
 * Hooks up cross-chart filtering via Plotly onClick dispatching to DataStore.
 *
 * Note: Chart configs (chart_type, axis labels, titles) come from rawData.charts
 * and are unchanged — only the visible data layer is filtered via filteredData.
 */
import React from 'react';
import { useDataStore } from '../store/dataStore';
import FilterBar from './FilterBar';
import InsightsPanel from './InsightsPanel';
import Dashboard from './Dashboard';

export default function SmartDashboard({ charts }) {
  const { state, dispatch } = useDataStore();
  const { rawData } = state;

  // Use chart configs from rawData if available, otherwise fall back to prop
  const chartConfigs = rawData?.charts || charts || [];

  // Cross-chart click handler — called by ChartRenderer onClick (if wired)
  // We attach it via a window-level event bus to avoid modifying ChartRenderer
  React.useEffect(() => {
    const handler = (e) => {
      const { col, value } = e.detail || {};
      if (col && value !== undefined) {
        dispatch({ type: 'APPLY_CHART_SELECTION', payload: { col, value } });
      }
    };
    window.addEventListener('datalens:chart-click', handler);
    return () => window.removeEventListener('datalens:chart-click', handler);
  }, [dispatch]);

  return (
    <div>
      <FilterBar />
      <InsightsPanel />
      <Dashboard charts={chartConfigs} />
    </div>
  );
}
