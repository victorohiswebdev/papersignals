"""Baseline norms computation for papersignals Phase 2.

Computes percentile distributions for each signal's raw metrics
from a corpus of human-written academic papers. These data-driven
norms replace the hardcoded thresholds in the original scoring engine.

Usage:
    norms = NormsCalculator(corpus_db)
    baseline = norms.compute_baseline()
    norms.save_baseline("~/.papersignals/norms/baseline.json")
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from papersignals.corpus.corpus_db import CorpusDB

logger = logging.getLogger(__name__)

# Metrics we extract from each analyzer result for norm computation
SIGNAL_METRICS: Dict[str, List[str]] = {
    "burstiness": ["std_dev", "coefficient_of_variation"],
    "transition_density": ["density_per_100_words", "unique_types"],
    "lexical_diversity": ["type_token_ratio", "hapax_richness"],
    "vocabulary_fingerprint": ["total_flagged", "density_per_1000_words"],
    "paragraph_uniformity": ["std_dev_words", "mean_words", "paragraph_count"],
    "readability": ["flesch_kincaid", "gunning_fog"],
    "perplexity": ["estimated_perplexity"],
}


def compute_percentiles(
    values: List[float],
    percentiles: Optional[List[float]] = None,
) -> Dict[str, float]:
    """Compute percentile thresholds from a list of values.

    Args:
        values: List of raw metric values (NaNs and None filtered out).
        percentiles: Percentile thresholds to compute.
            Defaults to [5, 10, 25, 50, 75, 90, 95].

    Returns:
        Dict mapping percentile label (e.g. 'p5') to value.
    """
    if percentiles is None:
        percentiles = [5, 10, 25, 50, 75, 90, 95]

    # Filter invalid values
    clean = [v for v in values if v is not None and not (isinstance(v, float) and np.isnan(v))]
    if not clean:
        return {f"p{p}": 0.0 for p in percentiles}

    arr = np.array(clean, dtype=float)
    result: Dict[str, float] = {}
    for p in percentiles:
        result[f"p{p}"] = float(np.percentile(arr, p))
    return result


def compute_stats(values: List[float]) -> Dict[str, float]:
    """Compute summary statistics from a list of values.

    Args:
        values: List of raw metric values.

    Returns:
        Dict with mean, std, min, max, median, count.
    """
    clean = [v for v in values if v is not None and not (isinstance(v, float) and np.isnan(v))]
    if not clean:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "median": 0.0, "count": 0}

    arr = np.array(clean, dtype=float)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "median": float(np.median(arr)),
        "count": len(arr),
    }


class NormsCalculator:
    """Compute baseline percentile norms from a corpus of human papers.

    Args:
        corpus_db: Initialized CorpusDB instance pointing to the corpus data.
    """

    def __init__(self, corpus_db: CorpusDB):
        self.db = corpus_db

    def compute_baseline(self) -> Dict[str, Any]:
        """Compute baseline norms from all analyzed papers in the corpus.

        Extracts raw metric values from each paper's analysis results
        and computes percentile distributions for every signal metric.

        Returns:
            Dict with structure:
            {
                "norms": {
                    "burstiness": {
                        "std_dev": {"p5": ..., "p50": ..., "p95": ..., "stats": {...}},
                        "coefficient_of_variation": {...},
                    },
                    ...
                },
                "metadata": {
                    "total_papers": int,
                    "total_analyzed": int,
                    "generated_at": str (ISO timestamp),
                    "categories": {...},
                }
            }
        """
        analyses = self.db.get_all_analyses()
        if not analyses:
            logger.warning("No analysis results found in corpus DB.")
            return {"norms": {}, "metadata": {"total_papers": 0, "total_analyzed": 0}}

        # Collect raw values for each signal metric
        metric_values: Dict[str, List[float]] = {}

        for analysis in analyses:
            analysis_dict = analysis.to_dict()
            for signal_name, metric_keys in SIGNAL_METRICS.items():
                raw = analysis_dict.get(signal_name, {})
                raw_inner = raw.get("raw", raw)  # handle both nested styles
                if isinstance(raw_inner, dict):
                    for metric_key in metric_keys:
                        val = raw_inner.get(metric_key)
                        full_key = f"{signal_name}.{metric_key}"
                        if full_key not in metric_values:
                            metric_values[full_key] = []
                        if val is not None:
                            metric_values[full_key].append(val)

        # Compute percentiles for each metric
        norms: Dict[str, Any] = {}
        for signal_name, metric_keys in SIGNAL_METRICS.items():
            signal_norms: Dict[str, Any] = {}
            for metric_key in metric_keys:
                full_key = f"{signal_name}.{metric_key}"
                values = metric_values.get(full_key, [])
                signal_norms[metric_key] = {
                    "percentiles": compute_percentiles(values),
                    "stats": compute_stats(values),
                }
            norms[signal_name] = signal_norms

        metadata = {
            "total_papers": self.db.total_papers(),
            "total_analyzed": len(analyses),
            "categories": self.db._count_categories(),
            "generated_at": __import__("datetime").datetime.now().isoformat(),
        }

        return {"norms": norms, "metadata": metadata}

    def save_baseline(
        self,
        output_path: Optional[str] = None,
    ) -> str:
        """Compute and save the baseline norms to a JSON file.

        Args:
            output_path: Path to save the baseline JSON.
                Defaults to ~/.papersignals/norms/baseline.json.

        Returns:
            Path to the saved file.
        """
        if output_path is None:
            output_path = os.path.expanduser("~/.papersignals/norms/baseline.json")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        baseline = self.compute_baseline()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(baseline, f, indent=2, ensure_ascii=False)

        logger.info("Saved baseline norms to %s", output_path)
        return output_path

    @staticmethod
    def load_baseline(
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Load a previously saved baseline norms JSON.

        Args:
            path: Path to the baseline JSON.
                Defaults to ~/.papersignals/norms/baseline.json.

        Returns:
            Baseline norms dict, or empty dict if not found.
        """
        if path is None:
            path = os.path.expanduser("~/.papersignals/norms/baseline.json")

        if not os.path.isfile(path):
            logger.warning("Baseline norms not found at %s", path)
            return {}

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def metric_threshold_table(
        self,
        signal_name: str,
        metric_key: str,
    ) -> List[Tuple[float, float, str]]:
        """Convert baseline percentiles to a scoring threshold table.

        Produces a list of (raw_value, score, label) tuples suitable
        for the scoring engine's piecewise linear interpolation.

        The mapping uses the 5th, 25th, 50th, 75th, and 95th percentiles.
        Higher signal values generally = more human-like, but for some
        metrics (e.g. vocabulary hit_count) lower = more human-like.

        Args:
            signal_name: e.g. 'burstiness', 'vocabulary_fingerprint'.
            metric_key: e.g. 'std_dev', 'hit_count'.

        Returns:
            List of (raw_value, score, label) tuples.
        """
        baseline = self.load_baseline()
        norms = baseline.get("norms", {})
        signal_norms = norms.get(signal_name, {})
        metric_norms = signal_norms.get(metric_key, {})
        percentiles = metric_norms.get("percentiles", {})
        stats = metric_norms.get("stats", {})

        if not percentiles:
            # Fall back to generic thresholds
            return [
                (0.0, 0.0, "very_low"),
                (5.0, 25.0, "low"),
                (10.0, 50.0, "medium"),
                (15.0, 75.0, "high"),
                (20.0, 100.0, "very_high"),
            ]

        # Map percentiles to score values
        # p5 -> score 5, p25 -> 25, p50 -> 50, p75 -> 75, p95 -> 95
        mapping = [
            (percentiles.get("p5", 0.0), 5.0, "very_low"),
            (percentiles.get("p25", 0.0), 25.0, "low"),
            (percentiles.get("p50", 0.0), 50.0, "medium"),
            (percentiles.get("p75", 0.0), 75.0, "high"),
            (percentiles.get("p95", 0.0), 95.0, "very_high"),
        ]

        # Some metrics are inverted: lower raw value = more human-like
        # Vocabulary hit_count, transition density, perplexity
        inverted_signals = {
            "vocabulary_fingerprint",
            "transition_density",
            "perplexity",
        }

        # Paragraph count is also inverted (more paragraphs > 1 is good)
        if metric_key == "paragraph_count":
            inverted_signals.add("paragraph_uniformity")

        if signal_name in inverted_signals:
            # Invert: high raw value = low score
            mapping = [
                (raw_val, 100.0 - score, label)
                for raw_val, score, label in mapping
            ]
            # Sort by raw value ascending
            mapping.sort(key=lambda x: x[0])

        return mapping
