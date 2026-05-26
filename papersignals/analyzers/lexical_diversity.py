"""Lexical diversity analyzer — vocabulary richness metrics."""

import math
from collections import Counter
from typing import Dict, List

from papersignals.core.scoring import normalize_score


def analyze(text: str) -> Dict:
    """Analyze lexical diversity of the text.

    Measures vocabulary richness through Type-Token Ratio (TTR),
    hapax richness, and mean word frequency rank.

    Args:
        text: Full input text.

    Returns:
        Dict with keys:
            'score': float (0-100, higher = more human-like),
            'raw': dict of raw statistics,
            'risk': 'low' | 'medium' | 'high',
            'details': dict with vocabulary stats.
    """
    if not text or not text.strip():
        return {
            "score": 100.0,
            "raw": {
                "type_token_ratio": 0.0,
                "hapax_richness": 0.0,
                "total_words": 0,
                "unique_words": 0,
                "hapax_count": 0,
            },
            "risk": "low",
            "details": {"message": "Empty text"},
        }

    words = text.lower().split()
    total_words = len(words)

    if total_words < 10:
        return {
            "score": 50.0,
            "raw": {
                "type_token_ratio": len(set(words)) / total_words if total_words else 0,
                "hapax_richness": 0.0,
                "total_words": total_words,
                "unique_words": len(set(words)),
                "hapax_count": 0,
            },
            "risk": "medium",
            "details": {"message": "Very short text, diversity metrics may be unreliable"},
        }

    # Type-Token Ratio
    word_freqs = Counter(words)
    unique_words = len(word_freqs)
    ttr = unique_words / total_words if total_words > 0 else 0.0

    # Hapax richness (words appearing only once)
    hapax_count = sum(1 for count in word_freqs.values() if count == 1)
    hapax_richness = hapax_count / total_words if total_words > 0 else 0.0

    # Classify risk based on TTR
    if ttr < 0.45:
        risk = "high"
    elif ttr <= 0.55:
        risk = "medium"
    else:
        risk = "low"

    # Score: normalize TTR directly
    # TTR of 0.0 -> 0, TTR of 1.0 -> 100
    score = normalize_score(ttr, 0, 1)

    return {
        "score": round(score, 1),
        "raw": {
            "type_token_ratio": round(ttr, 4),
            "hapax_richness": round(hapax_richness, 4),
            "total_words": total_words,
            "unique_words": unique_words,
            "hapax_count": hapax_count,
        },
        "risk": risk,
        "details": {
            "top_frequency_words": [
                {"word": word, "count": count}
                for word, count in word_freqs.most_common(10)
            ],
        },
    }
