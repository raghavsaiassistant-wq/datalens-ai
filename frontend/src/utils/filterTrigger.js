/**
 * filterTrigger.js
 *
 * Determines whether a client-side filter change crosses the threshold
 * for triggering a backend AI insight regeneration.
 *
 * Thresholds:
 *   Large datasets (>50k rows): regenerate if ≥10% of rows are filtered out
 *   Small datasets (≤50k rows): regenerate if ≥20% of rows are filtered out
 */

/**
 * @param {number} originalRowCount  — total rows in the unfiltered dataset
 * @param {number} filteredRowCount  — rows remaining after applying filters
 * @returns {boolean}
 */
export function shouldTriggerRegeneration(originalRowCount, filteredRowCount) {
  if (!originalRowCount || originalRowCount === 0) return false;
  const threshold = originalRowCount > 50000 ? 0.10 : 0.20;
  const reduction = (originalRowCount - filteredRowCount) / originalRowCount;
  return reduction >= threshold;
}
