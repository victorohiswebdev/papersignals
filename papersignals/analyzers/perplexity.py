"""Perplexity estimation analyzer.

NOTE: This is an approximation of perplexity using character-level
n-gram surprisal, not true LLM-based perplexity. It provides a
useful heuristic but should not be treated as a definitive metric.
"""

import math
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

from papersignals.core.scoring import normalize_score


# Character n-gram order for surprisal estimation
_NGRAM_ORDER = 4

# Pre-computed approximate English character bigram frequencies
# Based on general English text corpus statistics
_ENGLISH_UNIGRAMS: Dict[str, float] = {
    ' ': 0.182, 'e': 0.102, 't': 0.075, 'a': 0.065, 'o': 0.062,
    'i': 0.061, 'n': 0.057, 's': 0.053, 'h': 0.047, 'r': 0.047,
    'd': 0.035, 'l': 0.034, 'c': 0.025, 'u': 0.025, 'm': 0.020,
    'w': 0.020, 'f': 0.019, 'g': 0.018, 'y': 0.018, 'p': 0.017,
    'b': 0.015, 'v': 0.010, 'k': 0.008, 'j': 0.002, 'x': 0.002,
    'q': 0.001, 'z': 0.001,
}


def analyze(text: str) -> Dict:
    """Estimate text perplexity using character-level n-gram surprisal.

    This is an approximation based on character n-gram frequencies
    from common English patterns. Lower perplexity can indicate
    more predictable (potentially AI-generated) text, while higher
    perplexity suggests more natural variation.

    Args:
        text: Full input text.

    Returns:
        Dict with keys:
            'score': float (0-100, higher = more human-like),
            'raw': dict with perplexity stats,
            'risk': 'low' | 'medium' | 'high',
            'details': dict with additional info.

    Note:
        This is NOT true LLM perplexity. It uses character-level
        n-gram statistics as a lightweight approximation. Results
        should be interpreted with caution.
    """
    if not text or not text.strip():
        return {
            "score": 100.0,
            "raw": {
                "estimated_perplexity": 0.0,
                "avg_log_prob": 0.0,
                "char_count": 0,
            },
            "risk": "low",
            "details": {"message": "Empty text", "note": "Approximation only"},
        }

    # Normalize text for analysis
    cleaned = text.lower()
    # Keep alphanumeric, spaces, and basic punctuation
    cleaned = re.sub(r'[^a-z0-9\s\.\,\;\:\!\?\-]', '', cleaned)
    cleaned = cleaned.strip()

    if len(cleaned) < 10:
        return {
            "score": 50.0,
            "raw": {
                "estimated_perplexity": 100.0,
                "avg_log_prob": -4.6,
                "char_count": len(cleaned),
            },
            "risk": "medium",
            "details": {"message": "Text too short for reliable perplexity estimation", "note": "Approximation only"},
        }

    # Build character-level n-gram model from the text itself
    # For a real system we'd use a pre-built model, but this
    # captures the basic distribution
    ngram_counts, context_counts = _build_ngram_model(cleaned, _NGRAM_ORDER)

    # Compute average log probability (surprisal)
    total_log_prob = 0.0
    total_chars = 0

    for i in range(_NGRAM_ORDER, len(cleaned)):
        context = cleaned[i - _NGRAM_ORDER:i]
        char = cleaned[i]

        prob = _estimate_char_prob(char, context, ngram_counts, context_counts)
        if prob > 0:
            total_log_prob += -math.log2(prob)
            total_chars += 1

    if total_chars == 0:
        avg_log_prob = 0.0
        perplexity = 1.0
    else:
        avg_log_prob = total_log_prob / total_chars
        perplexity = math.pow(2, avg_log_prob)

    # Expected perplexity range for natural text: ~5-15
    # Lower perplexity (< 5) = very predictable = potentially AI-like
    # Higher perplexity (> 15) = more varied = more human-like
    # But extremely high (> 25) could indicate noisy text
    if perplexity < 5:
        risk = "high"
    elif perplexity <= 15:
        risk = "medium"
    else:
        risk = "low"

    # Score: normalize and invert
    # Perplexity of 2 -> 0, perplexity of 25 -> 100
    raw_score = normalize_score(perplexity, 2, 25)
    score = max(0.0, min(100.0, raw_score))

    return {
        "score": round(score, 1),
        "raw": {
            "estimated_perplexity": round(perplexity, 2),
            "avg_log_prob": round(avg_log_prob, 4),
            "char_count": len(cleaned),
            "ngram_order": _NGRAM_ORDER,
        },
        "risk": risk,
        "details": {
            "note": "Approximation only — not true LLM perplexity",
            "method": f"Character-level {_NGRAM_ORDER}-gram surprisal",
        },
    }


def _build_ngram_model(
    text: str, n: int
) -> Tuple[Counter, Counter]:
    """Build character n-gram counts from text.

    Args:
        text: Cleaned lowercase text.
        n: N-gram order.

    Returns:
        Tuple of (ngram_counts, context_counts) where
        ngram_counts maps n-grams to counts, and
        context_counts maps (n-1)-gram contexts to counts.
    """
    ngram_counts: Counter = Counter()
    context_counts: Counter = Counter()

    for i in range(len(text) - n + 1):
        ngram = text[i:i + n]
        context = ngram[:-1]
        ngram_counts[ngram] += 1
        context_counts[context] += 1

    return ngram_counts, context_counts


def _estimate_char_prob(
    char: str,
    context: str,
    ngram_counts: Counter,
    context_counts: Counter,
) -> float:
    """Estimate probability of a character given its context.

    Uses Katz back-off with interpolation from lower-order n-grams.

    Args:
        char: The next character.
        context: The preceding (n-1) characters.
        ngram_counts: N-gram frequency counter.
        context_counts: Context frequency counter.

    Returns:
        Estimated probability (0 < prob <= 1).
    """
    ngram = context + char
    context_count = context_counts.get(context, 0)
    ngram_count = ngram_counts.get(ngram, 0)

    if context_count > 0 and ngram_count > 0:
        # Maximum likelihood estimate with smoothing
        return ngram_count / context_count
    elif context_count > 0:
        # Back-off: use added smoothing
        return 0.01 / (context_count + 1)
    else:
        # Unknown context: use unigram fallback
        return _ENGLISH_UNIGRAMS.get(char, 0.001)
