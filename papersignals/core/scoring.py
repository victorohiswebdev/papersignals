"""Score normalization and composite scoring for papersignals."""

from typing import Dict


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


def normalize_score(raw_value: float, min_val: float, max_val: float) -> float:
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
    used_scores = {}

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
