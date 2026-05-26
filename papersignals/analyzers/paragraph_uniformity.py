"""Paragraph uniformity analyzer."""

import math
from typing import Dict, List

from papersignals.core.scoring import normalize_score
from papersignals.utils.text_utils import word_count


def analyze(paragraphs: List[str]) -> Dict:
    """Analyze paragraph length uniformity.

    AI-generated text often exhibits unusually uniform paragraph
    lengths, while human writing tends to vary paragraph length
    more naturally.

    Args:
        paragraphs: List of paragraph strings.

    Returns:
        Dict with keys:
            'score': float (0-100, higher = more human-like),
            'raw': dict of raw statistics,
            'risk': 'low' | 'medium' | 'high',
            'details': dict with 'flagged_paragraphs'.
    """
    if not paragraphs or len(paragraphs) < 2:
        return {
            "score": 100.0,
            "raw": {
                "mean_words": 0.0,
                "std_dev_words": 0.0,
                "mean_sentences": 0.0,
                "std_dev_sentences": 0.0,
                "paragraph_count": len(paragraphs) if paragraphs else 0,
                "nearly_identical_pairs": 0,
            },
            "risk": "low",
            "details": {
                "message": "Insufficient paragraphs for uniformity analysis",
            },
        }

    # Compute paragraph lengths in words
    word_lengths = [word_count(p) for p in paragraphs]

    # Compute paragraph lengths in sentences (approximate by splitting on .!?)
    sentence_counts = []
    import re
    for p in paragraphs:
        sents = re.split(r'(?<=[.!?])\s+', p)
        sentence_counts.append(len(sents))

    n = len(word_lengths)

    # Statistics for word lengths
    mean_words = sum(word_lengths) / n
    variance_words = sum((wl - mean_words) ** 2 for wl in word_lengths) / n
    std_dev_words = math.sqrt(variance_words)

    # Statistics for sentence counts
    mean_sentences = sum(sentence_counts) / n
    variance_sentences = sum((sc - mean_sentences) ** 2 for sc in sentence_counts) / n
    std_dev_sentences = math.sqrt(variance_sentences)

    # Find paragraph pairs that are nearly identical in length (within 5 words)
    identical_pairs = 0
    flagged_paras: List[Dict] = []
    for i in range(len(word_lengths)):
        for j in range(i + 1, len(word_lengths)):
            if abs(word_lengths[i] - word_lengths[j]) <= 5:
                identical_pairs += 1
                flagged_paras.append({
                    "para_1": i + 1,
                    "para_2": j + 1,
                    "len_1": word_lengths[i],
                    "len_2": word_lengths[j],
                })

    # Only flag unique pairs (limit to first 20 for display)
    if len(flagged_paras) > 20:
        flagged_paras = flagged_paras[:20]

    # Classify risk based on std_dev of paragraph word lengths
    if std_dev_words < 25:
        risk = "high"
    elif std_dev_words <= 45:
        risk = "medium"
    else:
        risk = "low"

    # Score: invert normalize
    # SD of 0 -> 0, SD of 60+ -> 100
    raw_score = normalize_score(std_dev_words, 0, 60)
    score = max(0.0, min(100.0, raw_score))

    return {
        "score": round(score, 1),
        "raw": {
            "mean_words": round(mean_words, 2),
            "std_dev_words": round(std_dev_words, 2),
            "mean_sentences": round(mean_sentences, 2),
            "std_dev_sentences": round(std_dev_sentences, 2),
            "paragraph_count": n,
            "nearly_identical_pairs": identical_pairs,
        },
        "risk": risk,
        "details": {
            "flagged_paragraphs": flagged_paras,
            "paragraph_lengths": word_lengths,
        },
    }
