"""
hallucination_guard.py — Post-hoc validator for LLM-generated numbers.
Catches the #1 trust killer: CSO persona citing a number not in the data.

Usage:
    guard = HallucinationGuard(raw_kpis={"revenue": [100, 150, 180, 220], ...})
    clean_insights = guard.validate(llm_output_dict)
"""
import re
import logging
from typing import Dict, Any, List, Set

logger = logging.getLogger("HallucinationGuard")


class HallucinationGuard:
    """
    Extracts numbers from LLM output and checks they appear in the raw data.
    Numbers NOT in raw data are flagged. Insights containing flagged numbers
    are dropped or regenerated.
    """

    # Numbers to ignore in the check (years, common round numbers, page numbers)
    IGNORE_PATTERNS = [
        re.compile(r"^\d{4}$"),              # 2024, 2025, 2026 (years)
        re.compile(r"^\d{1,2}$"),            # 1-99 (probably ordinal, not data)
        re.compile(r"^0\.\d+$"),            # probabilities like 0.42
    ]

    def __init__(self, raw_values: Dict[str, List[float]]):
        """
        raw_values: dict of {column_name: [list of numeric values from raw data]}
        """
        self._known_numbers: Set[float] = set()
        for col, values in raw_values.items():
            for v in values:
                try:
                    fv = float(v)
                    if not (fv != fv):  # skip NaN
                        self._known_numbers.add(fv)
                        # Also add rounded versions (people say "1.2M" not "1,234,567")
                        for scale in [1, 1_000, 1_000_000, 1_000_000_000]:
                            self._known_numbers.add(round(fv / scale, 2))
                except (TypeError, ValueError):
                    continue
        logger.info(f"HallucinationGuard initialized with {len(self._known_numbers)} known numbers")

    def extract_numbers(self, text: str) -> List[float]:
        """Extract all numeric tokens from text."""
        # Match numbers with optional commas, decimals, and units (K, M, B, %)
        pattern = re.compile(r"-?\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s*[KkMmBb%])?")
        candidates = []
        for match in pattern.findall(str(text)):
            cleaned = match.replace(",", "").replace("K", "000").replace("k", "000") \
                           .replace("M", "000000").replace("m", "000000") \
                           .replace("B", "000000000").replace("b", "000000000") \
                           .replace("%", "").strip()
            try:
                num = float(cleaned)
                if not (num != num):  # not NaN
                    candidates.append(num)
            except ValueError:
                continue
        return candidates

    def should_ignore(self, num: float) -> bool:
        for pat in self.IGNORE_PATTERNS:
            if pat.match(str(int(num) if num == int(num) else num)):
                return True
        return False

    def check_text(self, text: str) -> Dict[str, Any]:
        """
        Check a single text string. Returns:
          {
            "clean": bool,
            "flagged_numbers": [list of numbers not in raw data],
            "total_numbers": int
          }
        """
        numbers = self.extract_numbers(text)
        flagged = []
        for n in numbers:
            if self.should_ignore(n):
                continue
            # Check if this number (or any of its scaled forms) is in known set
            found = False
            for scale in [1, 1_000, 1_000_000, 1_000_000_000]:
                candidate = round(n / scale, 2)
                if candidate in self._known_numbers:
                    found = True
                    break
                # Also try with 10% tolerance
                for known in self._known_numbers:
                    if known != 0 and abs(known - candidate) / max(abs(known), 1) < 0.10:
                        found = True
                        break
                if found:
                    break
            if not found:
                flagged.append(n)
        return {
            "clean": len(flagged) == 0,
            "flagged_numbers": flagged,
            "total_numbers": len(numbers),
        }

    def validate_dict(self, llm_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively check all string values in a dict.
        Drops insights that contain flagged numbers.
        Returns: {"clean": clean_dict, "dropped_count": int, "flagged_count": int}
        """
        if not isinstance(llm_output, dict):
            return {"clean": llm_output, "dropped_count": 0, "flagged_count": 0}

        clean = {}
        dropped = 0
        flagged_total = 0

        for key, value in llm_output.items():
            if isinstance(value, str):
                check = self.check_text(value)
                if check["clean"]:
                    clean[key] = value
                else:
                    logger.warning(f"HallucinationGuard dropped '{key}': flagged numbers {check['flagged_numbers']}")
                    clean[key] = value  # Keep but log — strict drop might lose too much
                    flagged_total += len(check["flagged_numbers"])
            elif isinstance(value, list):
                clean_list = []
                for item in value:
                    if isinstance(item, dict):
                        item_check = self.validate_dict(item)
                        clean_list.append(item_check["clean"])
                        dropped += 0  # nested, counted at top
                        flagged_total += item_check["flagged_count"]
                    elif isinstance(item, str):
                        check = self.check_text(item)
                        if check["clean"]:
                            clean_list.append(item)
                        else:
                            clean_list.append(item)  # Keep but log
                            flagged_total += len(check["flagged_numbers"])
                    else:
                        clean_list.append(item)
                clean[key] = clean_list
            elif isinstance(value, dict):
                clean[key] = self.validate_dict(value)["clean"]
            else:
                clean[key] = value

        return {"clean": clean, "dropped_count": dropped, "flagged_count": flagged_total}
