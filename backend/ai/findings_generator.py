"""
findings_generator.py

Orchestrates the full AI Intelligence pipeline across detection, recommendation, and summarization.
Uses threading to parallelize Anomaly detection and Chart recommendation.
"""
import time
import threading
from typing import Dict, Any, List
from parsers.base_parser import DataProfile
from ai.nim_client import NIMClient
from ai.anomaly_detector import AnomalyDetector, AnomalyFlag
from ai.chart_recommender import ChartRecommender, ChartConfig
from ai.summarizer import Summarizer
import logging

logger = logging.getLogger("FindingsGenerator")

class FindingsGenerator:
    """Runs the AI pipeline."""

    def generate(self, profile: DataProfile, nim_client: NIMClient) -> Dict[str, Any]:
        """Runs the detection, charts and summarization pipeline and returns an AnalysisResult block."""
        start_time = time.time()
        
        detection_result: List[AnomalyFlag] = []
        charts_result: List[ChartConfig] = []
        
        def run_anomalies():
            try:
                detector = AnomalyDetector()
                res = detector.detect(profile, nim_client)
                detection_result.extend(res)
            except Exception as e:
                logger.error(f"Anomaly detection failed: {e}")
                
        def run_charts():
            try:
                recommender = ChartRecommender()
                res = recommender.recommend(profile)
                charts_result.extend(res)
            except Exception as e:
                logger.error(f"Chart recommendation failed: {e}")

        # 1 & 2. Run detector and recommender in parallel
        t1 = threading.Thread(target=run_anomalies)
        t2 = threading.Thread(target=run_charts)
        t1.start(); t2.start()
        t1.join(); t2.join()
        
        # 3. Summarizer
        summarizer = Summarizer()
        summary = summarizer.summarize(profile, detection_result, nim_client)
        
        total_time = round(time.time() - start_time, 2)
        logger.info(f"AI Pipeline completed in {total_time}s")
        
        # 4. Result combination
        return {
            "profile": {
                "file_name": profile.file_name,
                "source_type": profile.source_type,
                "rows": profile.rows,
                "cols": profile.cols,
                "columns": profile.columns,
                "column_types": profile.column_types,
                "kpi_columns": profile.kpi_columns,
                "has_datetime": profile.has_datetime,
                "has_numeric": profile.has_numeric,
                "null_pct": profile.null_pct,
                "duplicates": profile.duplicates,
                "warnings": profile.warnings
            },
            "charts": [self._dataclass_to_dict(c) for c in charts_result],
            "anomalies": [self._dataclass_to_dict(a) for a in detection_result],
            "executive_summary": summary.get("executive_summary", ""),
            "key_findings": summary.get("key_findings", []),
            "next_steps": summary.get("next_steps", []),
            "data_health_score": summary.get("data_health_score", 0),
            "processing_time": total_time
        }
        
    def _dataclass_to_dict(self, obj: Any) -> Dict[str, Any]:
        from dataclasses import asdict
        d = asdict(obj)
        return d
