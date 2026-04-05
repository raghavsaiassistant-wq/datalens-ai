/**
 * useFilteredInsights.js
 *
 * Watches the DataStore filters and triggers a backend AI insight regeneration
 * when the filter change crosses the shouldTriggerRegeneration threshold.
 *
 * Debounces 2000ms after the last filter change before calling the backend.
 */
import { useEffect, useRef } from 'react';
import axios from 'axios';
import { useDataStore } from '../store/dataStore.jsx';
import { shouldTriggerRegeneration } from '../utils/filterTrigger';

const API_BASE = import.meta.env.VITE_API_URL || 'https://datalens-ai.onrender.com';

/**
 * @param {string|null} sessionId — from useAnalysis()
 */
export function useFilteredInsights(sessionId) {
  const { state, dispatch } = useDataStore();
  const timerRef = useRef(null);

  useEffect(() => {
    // Prerequisites
    if (!state.rawData || !sessionId) return;

    const hash = JSON.stringify(state.filters);
    if (hash === state.lastFilterHash) return;

    const filteredCount  = state.filteredData?.length    || 0;
    const originalCount  = state.rawData?.profile?.rows  || 0;

    if (!shouldTriggerRegeneration(originalCount, filteredCount)) return;

    // Clear any pending timer
    if (timerRef.current) clearTimeout(timerRef.current);

    timerRef.current = setTimeout(async () => {
      dispatch({ type: 'SET_REGENERATING', payload: true });

      try {
        const res = await axios.post(`${API_BASE}/api/regenerate-insights`, {
          session_id:     sessionId,
          filter_context: {
            filtered_rows:  filteredCount,
            original_rows:  originalCount,
            active_filters: state.filters
          }
        });

        if (res.data.success && res.data.data?.regenerated) {
          dispatch({ type: 'SET_INSIGHTS',    payload: res.data.data.insights });
          if (res.data.data.date_metrics) {
            dispatch({ type: 'SET_DATE_METRICS', payload: res.data.data.date_metrics });
          }
        }
      } catch (err) {
        // Silent fail — don't break the UI if regeneration fails
        console.warn('InsightEngine regeneration failed:', err?.message);
      } finally {
        dispatch({ type: 'SET_REGENERATING', payload: false });
      }
    }, 2000);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [state.filters]); // eslint-disable-line react-hooks/exhaustive-deps
}
