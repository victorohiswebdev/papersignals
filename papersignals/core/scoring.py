"""Score normalization and composite scoring for papersignals.

Supports two scoring modes:
  1. Weighted average (rule-based, deterministic)
  2. RF classifier (data-driven, calibrated probabilities)

The RF classifier mode is preferred when a trained model is available.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default weights for each signal metric
DEFAULT_WEIGHTS: Dict[str, float] = {
    "burstiness": 0.25,
    "transition_density": 0.15,
    "lexical_diversity": 0.20,
    "vocabulary_fingerprint": 0.15,
    "paragraph_uniformity": 0.10,
    "readability": 0.10,
    "perplexity": 0.05,
}


# Default normalization thresholds for each signal (fallback when
# no corpus baseline is available). Structure:
#   signal_name -> metric_key -> [(raw_value, score), ...]
DEFAULT_THRESHOLDS: Dict[str, Dict[str, List[Tuple[float, float]]]] = {
    "burstiness": {
        "std_dev": [(0.0, 0.0), (3.0, 15.0), (5.0, 40.0), (12.0, 85.0), (20.0, 100.0)],
    },
    "transition_density": {
        "density": [(0.0, 100.0), (2.0, 80.0), (5.0, 50.0), (8.0, 20.0), (12.0, 0.0)],
    },
    "lexical_diversity": {
        "mattr": [(0.40, 0.0), (0.55, 20.0), (0.65, 50.0), (0.75, 80.0), (0.85, 100.0)],
    },
    "vocabulary_fingerprint": {
        "hit_count": [(0.0, 100.0), (2.0, 80.0), (6.0, 50.0), (12.0, 20.0), (20.0, 0.0)],
    },
    "paragraph_uniformity": {
        "coefficient_of_variation": [(0.0, 0.0), (0.20, 20.0), (0.40, 60.0), (0.70, 90.0), (1.0, 100.0)],
    },
    "readability": {
        "flesch_kincaid": [(6.0, 0.0), (10.0, 30.0), (14.0, 60.0), (18.0, 85.0), (22.0, 100.0)],
    },
    "perplexity": {
        "perplexity_score": [(0.0, 0.0), (50.0, 25.0), (100.0, 50.0), (200.0, 75.0), (500.0, 100.0)],
    },
}


def normalize_score(
    raw_value: float,
    min_val: float,
    max_val: float,
) -> float:
    """Linearly map a raw value to a 0-100 score.

    Higher scores indicate more human-like writing.
    Values outside [min_val, max_val] are clamped.

    Args:
        raw_value: The raw metric value to normalize.
        min_val: Minimum expected value (maps to 0).
        max_val: Maximum expected value (maps to 100).

    Returns:
        Normalized score between 0 and 100.
    """
    if max_val <= min_val:
        return 50.0  # neutral score for degenerate range

    clamped = max(min_val, min(max_val, raw_value))
    normalized = ((clamped - min_val) / (max_val - min_val)) * 100.0
    return round(normalized, 1)


def normalize_piecewise(
    raw_value: float,
    thresholds: List[Tuple[float, float]],
) -> float:
    """Normalize a raw value using piecewise linear interpolation.

    Maps raw values to 0-100 scores based on a table of (raw, score)
    breakpoints. Useful for data-driven normalization where we have
    percentile distributions from a corpus.

    Args:
        raw_value: The raw metric value.
        thresholds: List of (raw_value, score) tuples sorted by raw.
            e.g. [(0.0, 0.0), (3.0, 15.0), (5.0, 40.0), (12.0, 85.0)].

    Returns:
        Interpolated score between 0 and 100.
    """
    if not thresholds:
        return 50.0

    # Sort by raw value
    sorted_thresholds = sorted(thresholds, key=lambda x: x[0])

    # Clamp extremes
    if raw_value <= sorted_thresholds[0][0]:
        return sorted_thresholds[0][1]
    if raw_value >= sorted_thresholds[-1][0]:
        return sorted_thresholds[-1][1]

    # Find the segment and interpolate
    for i in range(len(sorted_thresholds) - 1):
        x1, y1 = sorted_thresholds[i]
        x2, y2 = sorted_thresholds[i + 1]
        if x1 <= raw_value <= x2:
            if x2 == x1:
                return y1
            fraction = (raw_value - x1) / (x2 - x1)
            return round(y1 + fraction * (y2 - y1), 1)

    return 50.0


def load_corpus_thresholds(
    baseline_path: Optional[str] = None,
) -> Dict[str, Dict[str, List[Tuple[float, float]]]]:
    """Load normalization thresholds from a corpus baseline JSON.

    Falls back to DEFAULT_THRESHOLDS if no baseline file exists.

    Args:
        baseline_path: Path to the baseline JSON.
            Defaults to ~/.papersignals/norms/baseline.json.

    Returns:
        Dict mapping signal_name -> metric_key -> [(raw, score), ...]
    """
    if baseline_path is None:
        baseline_path = os.path.expanduser("~/.papersignals/norms/baseline.json")

    if not os.path.isfile(baseline_path):
        logger.debug("No corpus baseline at %s, using defaults", baseline_path)
        return DEFAULT_THRESHOLDS

    try:
        import json

        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline = json.load(f)

        norms = baseline.get("norms", {})
        if not norms:
            return DEFAULT_THRESHOLDS

        thresholds: Dict[str, Dict[str, List[tuple[float, float]]]] = {}

        for signal_name, signal_norms in norms.items():
            thresholds[signal_name] = {}
            for metric_key, metric_data in signal_norms.items():
                percentiles = metric_data.get("percentiles", {})
                if not percentiles:
                    continue
                # Build threshold table from percentiles
                table = [
                    (percentiles.get("p5", 0.0), 5.0),
                    (percentiles.get("p25", 0.0), 25.0),
                    (percentiles.get("p50", 0.0), 50.0),
                    (percentiles.get("p75", 0.0), 75.0),
                    (percentiles.get("p95", 0.0), 95.0),
                ]
                thresholds[signal_name][metric_key] = table
                logger.debug(
                    "Loaded %s/%s thresholds from corpus baseline",
                    signal_name,
                    metric_key,
                )

        return thresholds

    except (json.JSONDecodeError, OSError, KeyError) as e:
        logger.warning("Failed to load corpus baseline: %s", e)
        return DEFAULT_THRESHOLDS


def _score_to_risk(score: float) -> str:
    """Convert a composite score to a risk level string.

    Args:
        score: Composite score from 0-100.

    Returns:
        'high' if score < 35, 'medium' if 35-65, 'low' if > 65.
    """
    if score < 35:
        return "high"
    elif score <= 65:
        return "medium"
    else:
        return "low"


def compute_composite(
    scores: Dict[str, float],
    weights: Dict[str, float] = None,
) -> Dict:
    """Compute weighted average composite score from individual metrics.

    Args:
        scores: Dict mapping metric names to their 0-100 scores.
                Expected keys: burstiness, transition_density,
                lexical_diversity, vocabulary_fingerprint,
                paragraph_uniformity, readability, perplexity.
        weights: Optional dict of custom weights. Uses DEFAULT_WEIGHTS if None.

    Returns:
        Dict containing:
            'individual_scores': copy of input scores,
            'weights': weights used,
            'composite_score': weighted average (0-100),
            'risk': 'low' | 'medium' | 'high'.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    # Use only weights for metrics that are present in scores
    composite = 0.0
    total_weight = 0.0
    used_scores: Dict[str, float] = {}

    for metric, weight in weights.items():
        if metric in scores and scores[metric] is not None:
            used_scores[metric] = scores[metric]
            composite += scores[metric] * weight
            total_weight += weight

    if total_weight > 0:
        composite = composite / total_weight
    else:
        composite = 50.0  # default neutral

    composite = round(max(0.0, min(100.0, composite)), 1)

    return {
        "individual_scores": dict(used_scores),
        "weights": dict(weights),
        "composite_score": composite,
        "risk": _score_to_risk(composite),
    }


def compute_rf_score(
    signals: Dict[str, Any],
    model_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute RF classifier score from analyzer signals.

    Returns a calibrated probability (0-100) that the text is human-written.
    Falls back to weighted-average composite if no RF model is available.

    Args:
        signals: Dict of analyzer results (from cli.run_analysis).
        model_path: Path to the trained RF classifier joblib file.
            Defaults to ~/.papersignals/models/rf_classifier.joblib.

    Returns:
        Dict containing:
            'rf_score': probability of human (0-100),
            'rf_class': 1 (human) or 0 (AI-like),
            'mode': 'rf_classifier' or 'weighted_average_fallback',
            'composite': weighted-average composite for comparison.
    """
    from papersignals.classifier.features import extract_features_from_analysis

    if model_path is None:
        model_path = os.path.expanduser("~/.papersignals/models/rf_classifier.joblib")

    # Always compute the weighted-average composite for comparison
    signal_scores = {
        name: data.get("score")
        for name, data in signals.items()
    }
    composite_result = compute_composite(signal_scores)

    # Try RF classifier
    if os.path.isfile(model_path):
        try:
            from joblib import load

            model = load(model_path)
            features = extract_features_from_analysis(signals).reshape(1, -1)
            prob = model.predict_proba(features)[0, 1]  # probability of human
            rf_class = model.predict(features)[0]

            rf_score = round(prob * 100.0, 1)

            return {
                "rf_score": rf_score,
                "rf_class": int(rf_class),
                "mode": "rf_classifier",
                "composite": composite_result["composite_score"],
                "risk": _score_to_risk(rf_score),
            }
        except Exception as e:
            logger.warning("RF classifier inference failed: %s", e)

    # Fallback to weighted average
    return {
        "rf_score": composite_result["composite_score"],
        "rf_class": -1,  # unknown
        "mode": "weighted_average_fallback",
        "composite": composite_result["composite_score"],
        "risk": composite_result["risk"],
    }
