import React from 'react';
import { TrendingUp, TrendingDown, Minus, Brain, Calendar, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { useDataStore } from '../store/dataStore.jsx';
import { buildDynamicDateMetrics } from '../utils/dateMetrics';

// ─── Urgency config ───────────────────────────────────────────────────── //
const URGENCY_CONFIG = {
  high:   { label: 'High',   bg: 'rgba(239,68,68,0.10)',   color: '#EF4444', icon: AlertTriangle },
  medium: { label: 'Medium', bg: 'rgba(245,158,11,0.10)',  color: '#F59E0B', icon: Clock },
  low:    { label: 'Low',    bg: 'rgba(34,197,94,0.10)',   color: '#22C55E', icon: CheckCircle },
};

// ─── Trend arrow ─────────────────────────────────────────────────────── //
function TrendIndicator({ value, label }) {
  if (value === null || value === undefined) return null;
  const positive = value >= 0;
  const Icon = positive ? TrendingUp : TrendingDown;
  const color = positive ? '#22C55E' : '#EF4444';
  return (
    <div className="flex items-center gap-1">
      <Icon size={12} style={{ color }} />
      <span className="text-[11px] font-mono font-bold" style={{ color }}>
        {positive ? '+' : ''}{value.toFixed(1)}%
      </span>
      {label && <span className="text-[10px] font-mono text-[#8E8E93]">{label}</span>}
    </div>
  );
}

// ─── Skeleton card ────────────────────────────────────────────────────── //
function SkeletonCard() {
  return (
    <div className="bg-[#F5F5F7] rounded-xl p-4 animate-pulse">
      <div className="h-3 bg-black/10 rounded w-2/3 mb-3" />
      <div className="h-2 bg-black/10 rounded w-full mb-2" />
      <div className="h-2 bg-black/10 rounded w-4/5 mb-4" />
      <div className="h-2 bg-black/10 rounded w-1/3" />
    </div>
  );
}

// ─── Date intelligence strip ─────────────────────────────────────────── //
function DateMetricsStrip({ dateMetrics, filteredData }) {
  const dynamic = buildDynamicDateMetrics(filteredData, dateMetrics);
  if (!dynamic || !dynamic.metrics) return null;

  const cols = Object.keys(dynamic.metrics).slice(0, 3);
  if (cols.length === 0) return null;

  return (
    <div className="mt-4 pt-4 border-t border-black/[0.05]">
      <div className="flex items-center gap-1.5 mb-3">
        <Calendar size={12} className="text-[#8E8E93]" />
        <span className="text-[10px] font-mono uppercase tracking-widest text-[#8E8E93]">
          Date Intelligence · {dynamic.granularity || 'period'} data ·{' '}
          {dynamic.date_range?.start?.slice(0, 10)} → {dynamic.date_range?.end?.slice(0, 10)}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {cols.map(col => {
          const m = dynamic.metrics[col];
          const direction = m.trend_direction || (m.trend_slope > 0 ? 'up' : m.trend_slope < 0 ? 'down' : 'flat');
          const TrendIcon = direction === 'up' ? TrendingUp : direction === 'down' ? TrendingDown : Minus;
          const trendColor = direction === 'up' ? '#22C55E' : direction === 'down' ? '#EF4444' : '#8E8E93';

          return (
            <div key={col} className="bg-[#F5F5F7] rounded-xl p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-bold text-[#1D1D1F] uppercase tracking-wider truncate">
                  {col}
                </span>
                <TrendIcon size={12} style={{ color: trendColor }} />
              </div>

              <div className="flex flex-wrap gap-x-3 gap-y-1">
                {m.mom_pct !== null && m.mom_pct !== undefined && (
                  <TrendIndicator value={m.mom_pct} label="MoM" />
                )}
                {m.yoy_pct !== null && m.yoy_pct !== undefined && (
                  <TrendIndicator value={m.yoy_pct} label="YoY" />
                )}
              </div>

              {(m.best_period || m.worst_period) && (
                <div className="flex gap-3 mt-2">
                  {m.best_period && (
                    <span className="text-[9px] font-mono text-[#22C55E]">
                      ▲ {m.best_period}
                    </span>
                  )}
                  {m.worst_period && (
                    <span className="text-[9px] font-mono text-[#EF4444]">
                      ▼ {m.worst_period}
                    </span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────── //
export default function InsightsPanel() {
  const { state } = useDataStore();
  const { insights, dateMetrics, isRegenerating, rawData, filteredData } = state;

  if (!rawData) return null;

  const l3 = insights?.l3_insights || [];
  const hasInsights = l3.length > 0;
  const hasDateMetrics = dateMetrics && Object.keys(dateMetrics.metrics || {}).length > 0;

  if (!hasInsights && !hasDateMetrics && !isRegenerating) return null;

  return (
    <div className="bg-white rounded-2xl border border-black/[0.07] shadow-[0_2px_12px_rgba(0,0,0,0.06)] px-6 py-5 mb-6">
      {/* ── Panel header ── */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Brain size={15} className="text-[#FF6B00]" />
          <span className="text-[11px] font-mono uppercase tracking-widest text-[#1D1D1F] font-bold">
            Board Intelligence
          </span>
          <span className="text-[10px] font-mono text-[#8E8E93] border border-black/10 rounded-full px-2 py-0.5">
            Level 3
          </span>
        </div>
        {!hasInsights && !isRegenerating && (
          <span className="text-[10px] font-mono text-[#8E8E93]">
            Insights update on significant filter changes
          </span>
        )}
      </div>

      {/* ── Insight cards ── */}
      {isRegenerating ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : hasInsights ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {l3.map((item, i) => {
            const urgency = URGENCY_CONFIG[item.urgency] || URGENCY_CONFIG.medium;
            const UrgencyIcon = urgency.icon;
            return (
              <div
                key={i}
                className="rounded-xl p-4 border border-black/[0.06]"
                style={{ background: '#FAFAFA' }}
              >
                {/* Urgency badge */}
                <div className="flex items-center justify-between mb-3">
                  <span
                    className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-mono font-bold uppercase tracking-wider"
                    style={{ background: urgency.bg, color: urgency.color }}
                  >
                    <UrgencyIcon size={9} />
                    {urgency.label}
                  </span>
                  {item.metric_impact && (
                    <span className="text-[10px] font-mono text-[#8E8E93]">{item.metric_impact}</span>
                  )}
                </div>

                {/* Title */}
                <h3 className="text-[13px] font-serif italic font-bold text-[#1D1D1F] mb-2 leading-snug">
                  {item.title}
                </h3>

                {/* Insight */}
                <p className="text-[11px] font-mono text-[#3A3A3C] leading-relaxed mb-3">
                  {item.insight}
                </p>

                {/* Action */}
                <div className="border-t border-black/[0.06] pt-2.5">
                  <p className="text-[10px] font-mono text-[#FF6B00] leading-relaxed">
                    → {item.action}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      ) : null}

      {/* ── Date metrics strip ── */}
      {hasDateMetrics && (
        <DateMetricsStrip dateMetrics={dateMetrics} filteredData={filteredData} />
      )}
    </div>
  );
}
