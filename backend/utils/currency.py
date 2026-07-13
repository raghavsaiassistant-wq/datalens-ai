"""
utils/currency.py — Detect and format currency values.
Fix for Bug #4: hardcoded "$K" USD in analytical_engine.py.
"""
import re
import logging
from typing import Dict, Any
import pandas as pd

logger = logging.getLogger("Currency")

CURRENCY_PATTERNS = [
    # (regex on column name, code, symbol, scale)
    (r"(usd|\$|dollar)", "USD", "$", 1),
    (r"(inr|₹|rs\.?|rupee)", "INR", "₹", 1),
    (r"(eur|€|euro)", "EUR", "€", 1),
    (r"(gbp|£|pound)", "GBP", "£", 1),
    (r"(aed|د\.إ)", "AED", "د.إ", 1),
    (r"(jpy|¥|yen)", "JPY", "¥", 1),
    (r"(cny|rmb|yuan)", "CNY", "¥", 1),
]

SCALE_LABELS = {
    1: "",
    1_000: "K",
    1_000_000: "M",
    1_000_000_000: "B",
}


def detect_currency(df: pd.DataFrame, profile) -> Dict[str, Any]:
    """
    Detect currency from column names. Returns the first match.
    Defaults to USD with $K if nothing detected.
    """
    for col in df.columns:
        col_lower = str(col).lower()
        for pattern, code, symbol, _ in CURRENCY_PATTERNS:
            if re.search(pattern, col_lower):
                logger.info(f"Detected currency {code} from column '{col}'")
                return {"code": code, "symbol": symbol, "scale": ""}
    return {"code": "USD", "symbol": "$", "scale": ""}


def format_value(value: float, currency: Dict[str, Any], *, precision: int = 1) -> str:
    """
    Format a numeric value with currency symbol and auto-scaling.
    Example: format_value(1234567, {"symbol":"$"}) → "$1.2M"
    """
    if value is None or pd.isna(value):
        return "—"
    abs_v = abs(value)
    symbol = currency.get("symbol", "$")

    if abs_v >= 1_000_000_000:
        return f"{symbol}{value / 1_000_000_000:.{precision}f}B"
    if abs_v >= 1_000_000:
        return f"{symbol}{value / 1_000_000:.{precision}f}M"
    if abs_v >= 1_000:
        return f"{symbol}{value / 1_000:.{precision}f}K"
    if abs_v >= 1:
        return f"{symbol}{value:,.0f}"
    return f"{symbol}{value:.{precision + 2}f}"


def format_percent(value: float, *, precision: int = 1) -> str:
    """Format a fraction as percentage: 0.42 → '42.0%'"""
    if value is None or pd.isna(value):
        return "—"
    return f"{value * 100:.{precision}f}%"
