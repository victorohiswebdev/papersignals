"""Transition word density analyzer."""

import re
from collections import Counter
from typing import Dict, List

from papersignals.core.scoring import normalize_score
from papersignals.utils.wordlists import load_transition_words


def analyze(sentences: List[str]) -> Dict:
    """Analyze transition word density in text.

    High density of transition words can be a signal of AI-generated
    text, as LLMs tend to overuse explicit transitional phrases.

    Args:
        sentences: List of sentence strings.

    Returns:
        Dict with keys:
            'score': float (0-100, higher = more human-like),
            'raw': dict of raw statistics,
            'risk': 'low' | 'medium' | 'high',
            'details': dict with 'frequent_transitions'.
    """
    if not sentences:
        return {
            "score": 100.0,
            "raw": {
                "total_transitions": 0,
                "density_per_100_words": 0.0,
                "unique_types": 0,
                "total_words": 0,
            },
            "risk": "low",
            "details": {"frequent_transitions": []},
        }

    transition_words = load_transition_words()
    # Sort by length (longest first) to match multi-word phrases before single words
    transition_words.sort(key=len, reverse=True)

    full_text = " ".join(sentences)
    total_words = len(full_text.split())
    if total_words == 0:
        return {
            "score": 100.0,
            "raw": {
                "total_transitions": 0,
                "density_per_100_words": 0.0,
                "unique_types": 0,
                "total_words": 0,
            },
            "risk": "low",
            "details": {"frequent_transitions": []},
        }

    # Lowercase the text for matching
    text_lower = full_text.lower()

    # Count transition word occurrences
    found_transitions: Counter = Counter()
    # Track which indices we've matched to avoid double-counting
    matched_positions: set = set()

    for tw in transition_words:
        tw_lower = tw.lower()
        # Use regex to find whole-word matches
        pattern = re.compile(r'\b' + re.escape(tw_lower) + r'\b')
        for match in pattern.finditer(text_lower):
            pos = match.start()
            if pos not in matched_positions:
                found_transitions[tw_lower] += 1
                # Mark all character positions in this match
                for p in range(pos, match.end()):
                    matched_positions.add(p)

    total_transitions = sum(found_transitions.values())
    density_per_100 = (total_transitions / total_words) * 100 if total_words > 0 else 0.0
    unique_types = len(found_transitions)

    # Classify risk
    if density_per_100 > 5:
        risk = "high"
    elif density_per_100 >= 2:
        risk = "medium"
    else:
        risk = "low"

    # Score: invert normalize
    # Density of 0 -> score 100 (best), density of 10+ -> score 0
    raw_score = normalize_score(density_per_100, 0, 10)
    # Invert: high density = low score
    score = 100.0 - raw_score
    score = max(0.0, min(100.0, score))

    # Most frequent transitions
    frequent = found_transitions.most_common(10)

    return {
        "score": round(score, 1),
        "raw": {
            "total_transitions": total_transitions,
            "density_per_100_words": round(density_per_100, 2),
            "unique_types": unique_types,
            "total_words": total_words,
        },
        "risk": risk,
        "details": {
            "frequent_transitions": [
                {"word": word, "count": count}
                for word, count in frequent
            ],
        },
    }
