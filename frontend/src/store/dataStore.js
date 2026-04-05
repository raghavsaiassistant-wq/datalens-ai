/**
 * dataStore.js
 *
 * Global client-side data store for DataLens AI v2.0.
 * Uses React Context + useReducer — no Redux/Zustand dependency.
 *
 * Manages:
 *  - rawData:      full analysisResult from useAnalysis
 *  - filteredData: subset of serialized_data.records after filter application
 *  - filters:      dateRange, per-column dimensions, chartSelection
 *  - insights:     InsightEngine L3 output from /api/regenerate-insights
 *  - dateMetrics:  DateIntelligence output
 *  - isRegenerating: true while waiting for /api/regenerate-insights
 */
import React, { createContext, useContext, useReducer } from 'react';

// ─── Initial State ────────────────────────────────────────────────────── //

const initialState = {
  rawData:         null,
  filteredData:    [],
  filters: {
    dateRange:       { start: null, end: null },
    dimensions:      {},   // { colName: selectedValue | null }
    chartSelection:  null  // { col, value } from cross-chart click
  },
  insights:        null,
  dateMetrics:     null,
  isRegenerating:  false,
  lastFilterHash:  null
};

// ─── Reducer ─────────────────────────────────────────────────────────── //

function dataReducer(state, action) {
  switch (action.type) {

    case 'SET_RAW_DATA': {
      const rawData = action.payload;
      if (!rawData) return { ...initialState };

      // Detect categorical columns for dimension filters (cardinality 2–20)
      const columnTypes = rawData.profile?.column_types || {};
      const records     = rawData.serialized_data?.records || [];

      const dimensionCols = Object.entries(columnTypes)
        .filter(([, t]) => t === 'categorical')
        .map(([col]) => col)
        .filter(col => {
          const unique = new Set(records.map(r => r[col])).size;
          return unique >= 2 && unique <= 20;
        });

      const dimensionFilters = Object.fromEntries(dimensionCols.map(c => [c, null]));

      // Detect date column
      const dateCol = Object.entries(columnTypes).find(([, t]) => t === 'datetime')?.[0] || null;

      return {
        ...initialState,
        rawData,
        filteredData: records,
        filters: {
          dateRange:      { start: null, end: null },
          dimensions:     dimensionFilters,
          chartSelection: null
        },
        insights:    rawData.insights    || null,
        dateMetrics: rawData.date_metrics || null,
        lastFilterHash: null,
        _dateCol: dateCol,
        _dimensionCols: dimensionCols,
      };
    }

    case 'APPLY_FILTERS': {
      const newFilters = {
        ...state.filters,
        ...action.payload,
        dimensions: { ...state.filters.dimensions, ...(action.payload.dimensions || {}) }
      };
      const filteredData = applyFilters(
        state.rawData?.serialized_data?.records || [],
        newFilters,
        state._dateCol
      );
      return {
        ...state,
        filters: newFilters,
        filteredData,
        lastFilterHash: JSON.stringify(newFilters)
      };
    }

    case 'APPLY_CHART_SELECTION': {
      const { col, value } = action.payload;
      const chartSelection = col && value != null ? { col, value } : null;
      const newFilters = { ...state.filters, chartSelection };
      const filteredData = applyFilters(
        state.rawData?.serialized_data?.records || [],
        newFilters,
        state._dateCol
      );
      return {
        ...state,
        filters:         newFilters,
        filteredData,
        lastFilterHash:  JSON.stringify(newFilters)
      };
    }

    case 'SET_INSIGHTS':
      return { ...state, insights: action.payload };

    case 'SET_DATE_METRICS':
      return { ...state, dateMetrics: action.payload };

    case 'SET_REGENERATING':
      return { ...state, isRegenerating: action.payload };

    case 'RESET':
      return { ...initialState };

    default:
      return state;
  }
}

// ─── Filter Logic ─────────────────────────────────────────────────────── //

function applyFilters(records, filters, dateCol) {
  if (!records || records.length === 0) return [];

  return records.filter(row => {
    // Date range filter
    if (dateCol && (filters.dateRange.start || filters.dateRange.end)) {
      const rowDate = new Date(row[dateCol]);
      if (filters.dateRange.start && rowDate < new Date(filters.dateRange.start)) return false;
      if (filters.dateRange.end   && rowDate > new Date(filters.dateRange.end + 'T23:59:59')) return false;
    }

    // Dimension filters
    for (const [col, val] of Object.entries(filters.dimensions)) {
      if (val !== null && val !== undefined && val !== '') {
        if (String(row[col]) !== String(val)) return false;
      }
    }

    // Cross-chart selection
    if (filters.chartSelection) {
      const { col, value } = filters.chartSelection;
      if (col in row && String(row[col]) !== String(value)) return false;
    }

    return true;
  });
}

// ─── Context ──────────────────────────────────────────────────────────── //

export const DataStoreContext = createContext(null);

export function DataStoreProvider({ children }) {
  const [state, dispatch] = useReducer(dataReducer, initialState);
  return (
    <DataStoreContext.Provider value={{ state, dispatch }}>
      {children}
    </DataStoreContext.Provider>
  );
}

export function useDataStore() {
  const ctx = useContext(DataStoreContext);
  if (!ctx) throw new Error('useDataStore must be used inside DataStoreProvider');
  return ctx;
}
