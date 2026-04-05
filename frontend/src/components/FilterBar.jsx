import React, { useState, useRef, useCallback } from 'react';
import { SlidersHorizontal, X, RefreshCw, Calendar, ChevronDown } from 'lucide-react';
import { useDataStore } from '../store/dataStore.jsx';
import { shouldTriggerRegeneration } from '../utils/filterTrigger';

export default function FilterBar() {
  const { state, dispatch } = useDataStore();
  const debounceRef = useRef(null);

  const { filters, filteredData, rawData, isRegenerating } = state;
  const originalRowCount = rawData?.profile?.rows || rawData?.serialized_data?.sample_size || 0;
  const filteredRowCount = filteredData?.length || 0;
  const filteredPct = originalRowCount > 0
    ? Math.round((1 - filteredRowCount / originalRowCount) * 100)
    : 0;

  const willRegenerate = shouldTriggerRegeneration(originalRowCount, filteredRowCount);

  // Dimension columns with their unique values
  const dimensionCols = Object.keys(filters.dimensions || {});
  const uniqueValues = useCallback((col) => {
    if (!rawData?.serialized_data?.records) return [];
    const vals = [...new Set(rawData.serialized_data.records.map(r => r[col]))].filter(v => v != null);
    return vals.sort();
  }, [rawData]);

  // Date range handlers (debounced 300ms)
  const handleDateChange = (field, value) => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      dispatch({
        type: 'APPLY_FILTERS',
        payload: { dateRange: { ...filters.dateRange, [field]: value || null } }
      });
    }, 300);
  };

  // Dimension change (immediate)
  const handleDimensionChange = (col, value) => {
    dispatch({
      type: 'APPLY_FILTERS',
      payload: { dimensions: { [col]: value || null } }
    });
  };

  // Remove a specific filter tag
  const removeFilter = (type, key) => {
    if (type === 'date') {
      dispatch({ type: 'APPLY_FILTERS', payload: { dateRange: { start: null, end: null } } });
    } else if (type === 'dimension') {
      dispatch({ type: 'APPLY_FILTERS', payload: { dimensions: { [key]: null } } });
    } else if (type === 'chart') {
      dispatch({ type: 'APPLY_CHART_SELECTION', payload: { col: null, value: null } });
    }
  };

  // Clear all filters
  const clearAll = () => {
    const emptyDimensions = Object.fromEntries(dimensionCols.map(c => [c, null]));
    dispatch({
      type: 'APPLY_FILTERS',
      payload: { dateRange: { start: null, end: null }, dimensions: emptyDimensions, chartSelection: null }
    });
    dispatch({ type: 'APPLY_CHART_SELECTION', payload: { col: null, value: null } });
  };

  // Detect if any filter is active
  const hasDateFilter = filters.dateRange.start || filters.dateRange.end;
  const activeDimensions = Object.entries(filters.dimensions || {}).filter(([, v]) => v !== null && v !== undefined && v !== '');
  const hasChartFilter = !!filters.chartSelection;
  const hasAnyFilter = hasDateFilter || activeDimensions.length > 0 || hasChartFilter;

  // Don't render if no data
  if (!rawData) return null;

  const dateCol = rawData?.date_metrics?.date_col || null;
  const hasDimensions = dimensionCols.length > 0;

  return (
    <div className="bg-white rounded-2xl border border-black/[0.07] shadow-[0_2px_12px_rgba(0,0,0,0.06)] px-6 py-4 mb-6">
      {/* ── Header row ── */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <SlidersHorizontal size={14} className="text-[#8E8E93]" />
          <span className="text-[11px] font-mono uppercase tracking-widest text-[#3A3A3C] font-bold">
            Data Filters
          </span>
          {isRegenerating && (
            <span className="flex items-center gap-1.5 ml-2 text-[10px] font-mono text-[#FF6B00]">
              <RefreshCw size={11} className="animate-spin" />
              Updating insights...
            </span>
          )}
          {willRegenerate && !isRegenerating && hasAnyFilter && (
            <span className="ml-2 px-2 py-0.5 rounded-full bg-[#FF6B00]/10 text-[10px] font-mono text-[#FF6B00]">
              AI insights will update
            </span>
          )}
        </div>
        {hasAnyFilter && (
          <button
            onClick={clearAll}
            className="text-[10px] font-mono text-[#8E8E93] hover:text-[#1D1D1F] transition-colors uppercase tracking-wider"
          >
            Clear all
          </button>
        )}
      </div>

      {/* ── Filter controls ── */}
      <div className="flex flex-wrap gap-3 items-end">

        {/* Date range */}
        {dateCol && (
          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1.5">
              <Calendar size={12} className="text-[#8E8E93]" />
              <span className="text-[10px] font-mono text-[#8E8E93] uppercase tracking-wider">Date</span>
            </div>
            <input
              type="date"
              defaultValue=""
              onChange={e => handleDateChange('start', e.target.value)}
              className="px-3 py-1.5 rounded-lg border border-black/[0.10] bg-[#F5F5F7] text-[11px] font-mono text-[#1D1D1F] focus:outline-none focus:border-[#FF6B00]/50 focus:bg-white transition-colors"
            />
            <span className="text-[10px] text-[#8E8E93] font-mono">to</span>
            <input
              type="date"
              defaultValue=""
              onChange={e => handleDateChange('end', e.target.value)}
              className="px-3 py-1.5 rounded-lg border border-black/[0.10] bg-[#F5F5F7] text-[11px] font-mono text-[#1D1D1F] focus:outline-none focus:border-[#FF6B00]/50 focus:bg-white transition-colors"
            />
          </div>
        )}

        {/* Dimension dropdowns */}
        {hasDimensions && dimensionCols.map(col => (
          <div key={col} className="relative">
            <select
              value={filters.dimensions[col] || ''}
              onChange={e => handleDimensionChange(col, e.target.value)}
              className="appearance-none pl-3 pr-8 py-1.5 rounded-lg border border-black/[0.10] bg-[#F5F5F7] text-[11px] font-mono text-[#1D1D1F] focus:outline-none focus:border-[#FF6B00]/50 focus:bg-white transition-colors cursor-pointer"
            >
              <option value="">All {col}</option>
              {uniqueValues(col).map(v => (
                <option key={v} value={v}>{String(v)}</option>
              ))}
            </select>
            <ChevronDown size={11} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8E8E93] pointer-events-none" />
          </div>
        ))}
      </div>

      {/* ── Active filter tags + stats ── */}
      {(hasAnyFilter || filteredRowCount !== originalRowCount) && (
        <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-black/[0.05]">

          {/* Stats strip */}
          <span className="text-[10px] font-mono text-[#8E8E93]">
            Showing <span className="text-[#1D1D1F] font-bold">{filteredRowCount.toLocaleString()}</span> of{' '}
            <span className="text-[#1D1D1F]">{originalRowCount.toLocaleString()}</span> rows
            {filteredPct > 0 && (
              <span className="ml-1 text-[#FF6B00]">· {filteredPct}% filtered</span>
            )}
          </span>

          {/* Active tags */}
          {hasDateFilter && (
            <FilterTag
              label={`Date: ${filters.dateRange.start || '…'} → ${filters.dateRange.end || '…'}`}
              onRemove={() => removeFilter('date')}
            />
          )}
          {activeDimensions.map(([col, val]) => (
            <FilterTag
              key={col}
              label={`${col}: ${val}`}
              onRemove={() => removeFilter('dimension', col)}
            />
          ))}
          {hasChartFilter && (
            <FilterTag
              label={`${filters.chartSelection.col}: ${filters.chartSelection.value}`}
              onRemove={() => removeFilter('chart')}
            />
          )}
        </div>
      )}
    </div>
  );
}

function FilterTag({ label, onRemove }) {
  return (
    <span className="flex items-center gap-1 px-2.5 py-1 bg-[#FF6B00]/10 border border-[#FF6B00]/20 rounded-full text-[10px] font-mono text-[#FF6B00]">
      {label}
      <button onClick={onRemove} className="ml-0.5 hover:opacity-70 transition-opacity">
        <X size={10} />
      </button>
    </span>
  );
}
