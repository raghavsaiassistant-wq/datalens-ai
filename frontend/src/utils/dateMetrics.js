/**
 * dateMetrics.js
 *
 * Pure JS functions for computing time-series metrics from filtered records.
 * No React, no side effects, no external dependencies.
 * All functions return null gracefully when data is insufficient (<4 points).
 */

// ─── Helpers ─────────────────────────────────────────────────────────── //

function parseDate(val) {
  const d = new Date(val);
  return isNaN(d.getTime()) ? null : d;
}

function getYearMonth(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
}

function getYearWeek(date) {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() + 4 - (d.getDay() || 7));
  const year = d.getFullYear();
  const week = Math.ceil(((d - new Date(year, 0, 1)) / 86400000 + 1) / 7);
  return `${year}-W${String(week).padStart(2, '0')}`;
}

function groupAndAverage(records, dateCol, valueCol, groupFn) {
  const groups = {};
  for (const r of records) {
    const d = parseDate(r[dateCol]);
    const v = parseFloat(r[valueCol]);
    if (!d || isNaN(v)) continue;
    const key = groupFn(d);
    if (!groups[key]) groups[key] = [];
    groups[key].push(v);
  }
  return Object.entries(groups)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([period, vals]) => ({
      period,
      value: vals.reduce((a, b) => a + b, 0) / vals.length
    }));
}

function pctChange(current, previous) {
  if (!previous || previous === 0) return null;
  return Math.round(((current - previous) / Math.abs(previous)) * 10000) / 100;
}

function validRecords(records, dateCol, valueCol) {
  return records.filter(r => parseDate(r[dateCol]) && !isNaN(parseFloat(r[valueCol])));
}

// ─── Public API ───────────────────────────────────────────────────────── //

/**
 * Month-over-month % change for a given value column.
 * @returns {number|null}
 */
export function computeMoM(records, dateCol, valueCol) {
  const valid = validRecords(records, dateCol, valueCol);
  if (valid.length < 4) return null;
  const monthly = groupAndAverage(valid, dateCol, valueCol, getYearMonth);
  if (monthly.length < 2) return null;
  return pctChange(monthly.at(-1).value, monthly.at(-2).value);
}

/**
 * Week-over-week % change for a given value column.
 * @returns {number|null}
 */
export function computeWoW(records, dateCol, valueCol) {
  const valid = validRecords(records, dateCol, valueCol);
  if (valid.length < 4) return null;
  const weekly = groupAndAverage(valid, dateCol, valueCol, getYearWeek);
  if (weekly.length < 2) return null;
  return pctChange(weekly.at(-1).value, weekly.at(-2).value);
}

/**
 * Year-over-year % change for a given value column.
 * @returns {number|null}
 */
export function computeYoY(records, dateCol, valueCol) {
  const valid = validRecords(records, dateCol, valueCol);
  if (valid.length < 4) return null;
  const yearly = groupAndAverage(valid, dateCol, valueCol, d => String(d.getFullYear()));
  if (yearly.length < 2) return null;
  return pctChange(yearly.at(-1).value, yearly.at(-2).value);
}

/**
 * Simple linear trend via least-squares regression.
 * @returns {{ slope: number, direction: 'up'|'down'|'flat' } | null}
 */
export function computeTrend(records, dateCol, valueCol) {
  const valid = validRecords(records, dateCol, valueCol);
  if (valid.length < 4) return null;

  const sorted = [...valid].sort((a, b) => parseDate(a[dateCol]) - parseDate(b[dateCol]));
  const n = sorted.length;
  const xs = sorted.map((_, i) => i);
  const ys = sorted.map(r => parseFloat(r[valueCol]));

  const xMean = xs.reduce((a, b) => a + b, 0) / n;
  const yMean = ys.reduce((a, b) => a + b, 0) / n;

  let num = 0, den = 0;
  for (let i = 0; i < n; i++) {
    num += (xs[i] - xMean) * (ys[i] - yMean);
    den += (xs[i] - xMean) ** 2;
  }

  const slope = den === 0 ? 0 : num / den;
  const direction = slope > 0.01 * yMean ? 'up' : slope < -0.01 * yMean ? 'down' : 'flat';

  return { slope: Math.round(slope * 1000) / 1000, direction };
}

/**
 * Best and worst monthly periods by average value.
 * @returns {{ best: { period: string, value: number }, worst: { period: string, value: number } } | null}
 */
export function computeBestWorst(records, dateCol, valueCol) {
  const valid = validRecords(records, dateCol, valueCol);
  if (valid.length < 4) return null;
  const monthly = groupAndAverage(valid, dateCol, valueCol, getYearMonth);
  if (monthly.length < 2) return null;

  const best  = monthly.reduce((a, b) => b.value > a.value ? b : a);
  const worst = monthly.reduce((a, b) => b.value < a.value ? b : a);

  return {
    best:  { period: best.period,  value: Math.round(best.value  * 100) / 100 },
    worst: { period: worst.period, value: Math.round(worst.value * 100) / 100 }
  };
}

/**
 * Merges backend DateIntelligence output with client-side recomputed metrics
 * for the currently filtered record set.
 *
 * @param {Array}  filteredRecords   — current state.filteredData
 * @param {Object} dateIntelligence  — state.dateMetrics from backend
 * @returns {Object} merged metrics keyed by column name
 */
export function buildDynamicDateMetrics(filteredRecords, dateIntelligence) {
  if (!dateIntelligence || !filteredRecords || filteredRecords.length === 0) {
    return dateIntelligence || {};
  }

  const dateCol = dateIntelligence.date_col;
  if (!dateCol) return dateIntelligence;

  const merged = { ...dateIntelligence, metrics: { ...(dateIntelligence.metrics || {}) } };

  for (const col of Object.keys(merged.metrics)) {
    const mom = computeMoM(filteredRecords, dateCol, col);
    const wow = computeWoW(filteredRecords, dateCol, col);
    const yoy = computeYoY(filteredRecords, dateCol, col);
    const trend = computeTrend(filteredRecords, dateCol, col);
    const bw    = computeBestWorst(filteredRecords, dateCol, col);

    merged.metrics[col] = {
      ...merged.metrics[col],
      ...(mom   !== null ? { mom_pct:      mom }                          : {}),
      ...(wow   !== null ? { wow_pct:      wow }                          : {}),
      ...(yoy   !== null ? { yoy_pct:      yoy }                          : {}),
      ...(trend !== null ? { trend_slope:  trend.slope,
                             trend_direction: trend.direction }           : {}),
      ...(bw    !== null ? { best_period:  bw.best.period,
                             worst_period: bw.worst.period }              : {}),
    };
  }

  return merged;
}
