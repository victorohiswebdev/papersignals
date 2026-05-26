"""Burstiness analyzer — measures sentence length variance."""

import math
from typing import Dict, List, Tuple

from papersignals.core.scoring import normalize_score


def analyze(sentences: List[str]) -> Dict:
    """Analyze sentence length variance (burstiness).

    Burstiness measures how much sentence lengths vary. Human writing
    typically has high variance, while AI text tends toward uniform
    sentence lengths.

    Args:
        sentences: List of sentence strings.

    Returns:
        Dict with keys:
            'score': float (0-100, higher = more human-like),
            'raw': dict of raw statistics,
            'risk': 'low' | 'medium' | 'high',
            'details': dict of flagged items.
    """
    if not sentences or len(sentences) < 2:
        return {
            "score": 100.0,
            "raw": {
                "mean_length": 0.0,
                "std_dev": 0.0,
                "coefficient_of_variation": 0.0,
                "sentence_count": len(sentences) if sentences else 0,
                "consecutive_similar_groups": 0,
            },
            "risk": "low",
            "details": {
                "message": "Insufficient sentences for burstiness analysis",
            },
        }

    # Compute lengths of each sentence in words
    lengths = [len(s.split()) for s in sentences]

    # Mean and standard deviation
    n = len(lengths)
    mean_len = sum(lengths) / n
    variance = sum((x - mean_len) ** 2 for x in lengths) / n
    std_dev = math.sqrt(variance)

    # Coefficient of variation (CV)
    cv = std_dev / mean_len if mean_len > 0 else 0.0

    # Find consecutive same-length sentences (within 3 words, 3+ in a row)
    consecutive_groups = _find_consecutive_similar(lengths, tolerance=3, min_run=3)

    # Classify risk based on std_dev
    # Lower std_dev = more uniform = higher AI risk
    if std_dev < 4:
        risk = "high"
    elif std_dev <= 8:
        risk = "medium"
    else:
        risk = "low"

    # Score: invert and normalize
    # SD of 2 -> ~10, SD of 12 -> ~85
    # Using a range of 0-15 for SD, clamped
    score = normalize_score(std_dev, 0, 15)
    # High SD gives high score; our normalize maps low->0, high->100
    # But SD=0 should give score 0, SD=15 should give score 100
    # That's already what normalize_score does with min=0, max=15
    # However we want to invert: higher risk (low SD) = lower score
    # Already correct since low SD gives low score and we defined
    # lower score = more AI-like.

    return {
        "score": round(score, 1),
        "raw": {
            "mean_length": round(mean_len, 2),
            "std_dev": round(std_dev, 2),
            "coefficient_of_variation": round(cv, 4),
            "sentence_count": n,
            "consecutive_similar_groups": len(consecutive_groups),
        },
        "risk": risk,
        "details": {
            "consecutive_similar_groups": [
                {
                    "start": g[0],
                    "end": g[1],
                    "count": g[2],
                    "length": g[3],
                }
                for g in consecutive_groups
            ],
        },
    }


def _find_consecutive_similar(
    lengths: List[int],
    tolerance: int = 3,
    min_run: int = 3,
) -> List[Tuple[int, int, int, int]]:
    """Find runs of consecutive sentences with similar lengths.

    Args:
        lengths: List of sentence word counts.
        tolerance: Max difference in length to consider similar.
        min_run: Minimum consecutive sentences to flag.

    Returns:
        List of (start_index, end_index, count, length) tuples.
    """
    if not lengths:
        return []

    groups: List[Tuple[int, int, int, int]] = []
    run_start = 0
    run_length = lengths[0]

    for i in range(1, len(lengths)):
        if abs(lengths[i] - run_length) <= tolerance:
            # Continue the run
            continue
        else:
            # End of a run
            run_count = i - run_start
            if run_count >= min_run:
                groups.append((run_start, i - 1, run_count, run_length))
            # Start new run
            run_start = i
            run_length = lengths[i]

    # Check final run
    run_count = len(lengths) - run_start
    if run_count >= min_run:
        groups.append((run_start, len(lengths) - 1, run_count, run_length))

    return groups
