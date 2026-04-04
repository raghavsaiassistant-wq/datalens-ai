"""
findings_generator.py

Orchestrates the full AI Intelligence pipeline across detection, recommendation, and summarization.
Uses threading to parallelize Anomaly detection and Chart recommendation.
"""
import time
import threading
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
from parsers.base_parser import DataProfile
from ai.nim_client import NIMClient
from ai.anomaly_detector import AnomalyDetector, AnomalyFlag
from ai.chart_recommender import ChartRecommender, ChartConfig
from ai.summarizer import Summarizer
import logging

logger = logging.getLogger("FindingsGenerator")

class FindingsGenerator:
    """Runs the AI pipeline."""

    def generate(self, profile: DataProfile, nim_client: NIMClient, progress_callback: Any = None) -> Dict[str, Any]:
        """Runs the detection, charts and summarization pipeline in parallel."""
        start_time = time.time()
        
        # 0. Sampling for Performance
        original_rows = profile.rows
        if original_rows > 500:
            logger.info(f"Sampling dataset from {original_rows} to 500 rows for AI efficiency.")
            profile.df = profile.df.sample(500, random_state=42) if original_rows > 500 else profile.df
            profile.rows = 500
            profile.warnings.append(f"AI insights generated from a sample of 500 rows (Total: {original_rows}).")

        def update_progress(step: int, message: str):
            if progress_callback:
                progress_callback(step, message)

        update_progress(1, "📂 File successfully read. Analyzing structure...")
        update_progress(2, "🔍 Statistical profiling complete. Initiating AI agents...")

        # 1. Prepare parallel tasks
        detector = AnomalyDetector()
        recommender = ChartRecommender()
        summarizer = Summarizer()

        update_progress(3, "🧠 Intelligent agents are processing your data...")

        with ThreadPoolExecutor(max_workers=3) as executor:
            # We start all three in parallel. 
            # Note: Summarizer will now work without explicit anomalies if they aren't ready,
            # or we accept that it runs on the profile data primarily.
            future_anomalies = executor.submit(detector.detect, profile, nim_client)
            future_charts = executor.submit(recommender.recommend, profile)
            # Parallelize summary + findings + next steps in ONE call or multiple?
            # Keeping it in one call for coherence, but running it in parallel with others.
            future_summary = executor.submit(summarizer.summarize, profile, [], nim_client)

            # Join results
            detection_result = future_anomalies.result()
            update_progress(4, "📊 Dashboard visualization models ready.")
            
            charts_result = future_charts.result()
            update_progress(5, "✨ AI Insight synthesis complete.")
            
            summary = future_summary.result()

        total_time = round(time.time() - start_time, 2)
        logger.info(f"AI Pipeline completed in {total_time}s")
        update_progress(6, "🎉 Analysis complete! Finalizing dashboard...")

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
