"""
filter_trigger.py

Determines whether a filter change is significant enough to warrant
re-running the AI insight pipeline on the backend.
"""


class FilterTrigger:
    """
    Evaluates whether a client-side filter change crosses the threshold
    for triggering an AI insight regeneration.

    Thresholds:
      - Large datasets (>50k rows): regenerate if ≥10% of rows are filtered out
      - Small datasets (≤50k rows): regenerate if ≥20% of rows are filtered out
    """

    def should_regenerate(self, original_profile: dict, filtered_stats: dict) -> bool:
        """
        Returns True if the row reduction from filtering is significant enough
        to warrant a new AI insight generation.

        Args:
            original_profile: dict with at least {"rows": int}
            filtered_stats:   dict with at least {"rows": int}
        """
        original_rows = original_profile.get("rows", 0)
        filtered_rows = filtered_stats.get("rows", 0)

        if original_rows == 0:
            return False

        threshold = 0.10 if original_rows > 50000 else 0.20
        reduction = (original_rows - filtered_rows) / original_rows
        return reduction >= threshold
