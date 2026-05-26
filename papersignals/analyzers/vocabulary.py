"""AI-favored vocabulary analyzer."""

import re
from collections import Counter
from typing import Dict, List, Tuple

from papersignals.core.scoring import normalize_score
from papersignals.utils.wordlists import load_ai_favored_words


def analyze(text: str) -> Dict:
    """Analyze text for AI-favored vocabulary patterns.

    Detects words and phrases that are statistically over-represented
    in AI-generated academic writing.

    Args:
        text: Full input text.

    Returns:
        Dict with keys:
            'score': float (0-100, higher = more human-like),
            'raw': dict of raw statistics,
            'risk': 'low' | 'medium' | 'high',
            'details': dict with 'flagged_words'.
    """
    if not text or not text.strip():
        return {
            "score": 100.0,
            "raw": {
                "total_flagged": 0,
                "unique_flagged": 0,
                "density_per_1000_words": 0.0,
                "total_words": 0,
            },
            "risk": "low",
            "details": {"flagged_words": []},
        }

    ai_words = load_ai_favored_words()
    # Sort by length descending to match multi-word phrases first
    ai_words.sort(key=len, reverse=True)

    total_words = len(text.split())
    if total_words == 0:
        return {
            "score": 100.0,
            "raw": {
                "total_flagged": 0,
                "unique_flagged": 0,
                "density_per_1000_words": 0.0,
                "total_words": 0,
            },
            "risk": "low",
            "details": {"flagged_words": []},
        }

    text_lower = text.lower()
    found_words: Counter = Counter()
    matched_positions: set = set()

    for word in ai_words:
        word_lower = word.lower()
        # Use regex for whole-word boundary matching
        pattern = re.compile(r'\b' + re.escape(word_lower) + r'\b')
        for match in pattern.finditer(text_lower):
            pos = match.start()
            if pos not in matched_positions:
                found_words[word_lower] += 1
                for p in range(pos, match.end()):
                    matched_positions.add(p)

    total_flagged = sum(found_words.values())
    unique_flagged = len(found_words)
    density_per_1000 = (total_flagged / total_words) * 1000 if total_words > 0 else 0.0

    # Classify risk: >2 per 1000 words = high risk
    if density_per_1000 > 2:
        risk = "high"
    elif density_per_1000 >= 1:
        risk = "medium"
    else:
        risk = "low"

    # Score: invert normalize
    # Density of 0 = 100 (best), density of 5+ = 0
    raw_score = normalize_score(density_per_1000, 0, 5)
    score = 100.0 - raw_score
    score = max(0.0, min(100.0, score))

    # Most common flagged words
    frequent = found_words.most_common(15)

    return {
        "score": round(score, 1),
        "raw": {
            "total_flagged": total_flagged,
            "unique_flagged": unique_flagged,
            "density_per_1000_words": round(density_per_1000, 2),
            "total_words": total_words,
        },
        "risk": risk,
        "details": {
            "flagged_words": [
                {"word": word, "count": count}
                for word, count in frequent
            ],
        },
    }
