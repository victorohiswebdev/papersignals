"""Readability metrics analyzer."""

import math
import re
from typing import Dict, List

from papersignals.core.scoring import normalize_score


def analyze(text: str) -> Dict:
    """Analyze text readability using standard metrics.

    Computes Flesch-Kincaid Grade Level, Gunning Fog Index, and
    average sentence length to assess readability.

    Args:
        text: Full input text.

    Returns:
        Dict with keys:
            'score': float (0-100, higher = more human-like),
            'raw': dict with readability metrics,
            'risk': 'low' | 'medium' | 'high',
            'details': dict with additional info.
    """
    if not text or not text.strip():
        return {
            "score": 100.0,
            "raw": {
                "flesch_kincaid": 0.0,
                "gunning_fog": 0.0,
                "average_sentence_length": 0.0,
                "average_syllables_per_word": 0.0,
                "total_words": 0,
                "total_sentences": 0,
            },
            "risk": "low",
            "details": {"message": "Empty text"},
        }

    # Count sentences
    sentences = _count_sentences(text)
    total_sentences = len(sentences)
    if total_sentences == 0:
        return {
            "score": 50.0,
            "raw": {
                "flesch_kincaid": 0.0,
                "gunning_fog": 0.0,
                "average_sentence_length": 0.0,
                "average_syllables_per_word": 0.0,
                "total_words": 0,
                "total_sentences": 0,
            },
            "risk": "medium",
            "details": {"message": "Unable to detect sentences"},
        }

    # Count words and syllables
    words = text.split()
    total_words = len(words)
    if total_words == 0:
        return {
            "score": 50.0,
            "raw": {
                "flesch_kincaid": 0.0,
                "gunning_fog": 0.0,
                "average_sentence_length": 0.0,
                "average_syllables_per_word": 0.0,
                "total_words": 0,
                "total_sentences": 0,
            },
            "risk": "medium",
            "details": {"message": "No words found"},
        }

    # Count syllables
    total_syllables = sum(_count_syllables(w) for w in words)
    avg_syllables_per_word = total_syllables / total_words if total_words > 0 else 0.0

    # Average sentence length
    avg_sentence_length = total_words / total_sentences if total_sentences > 0 else 0.0

    # Flesch-Kincaid Grade Level
    # FK = 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
    fk_grade = (
        0.39 * avg_sentence_length
        + 11.8 * avg_syllables_per_word
        - 15.59
    )
    fk_grade = max(0.0, fk_grade)

    # Gunning Fog Index
    # Fog = 0.4 * (words/sentences + 100 * complex_words/words)
    complex_words = sum(1 for w in words if _count_syllables(w) >= 3)
    complex_percentage = (complex_words / total_words) * 100 if total_words > 0 else 0.0
    fog_index = 0.4 * (avg_sentence_length + complex_percentage)
    fog_index = max(0.0, fog_index)

    # Classify risk based on expected academic range: FK 12-16
    if 12 <= fk_grade <= 16:
        risk = "low"
    elif 8 <= fk_grade <= 18:
        risk = "medium"
    else:
        risk = "high"

    # Score: how well does FK fall in academic range?
    # Perfect at FK=14 (middle of 12-16), score drops as it deviates
    ideal_fk = 14.0
    deviation = abs(fk_grade - ideal_fk)
    # Max deviation considered: 14 points (0 or 28)
    raw_score = normalize_score(deviation, 0, 14)
    score = 100.0 - raw_score
    score = max(0.0, min(100.0, score))

    return {
        "score": round(score, 1),
        "raw": {
            "flesch_kincaid": round(fk_grade, 2),
            "gunning_fog": round(fog_index, 2),
            "average_sentence_length": round(avg_sentence_length, 2),
            "average_syllables_per_word": round(avg_syllables_per_word, 2),
            "total_words": total_words,
            "total_sentences": total_sentences,
            "complex_words_percentage": round(complex_percentage, 2),
        },
        "risk": risk,
        "details": {
            "flesch_kincaid_interpretation": _fk_interpretation(fk_grade),
        },
    }


def _count_sentences(text: str) -> List[str]:
    """Split text into sentences for readability analysis.

    Args:
        text: Input text.

    Returns:
        List of sentence strings.
    """
    # Simple sentence splitting for readability purposes
    # Split on sentence endings followed by space and capital letter
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in sentences if s.strip()]


def _count_syllables(word: str) -> int:
    """Estimate syllable count for a single word.

    Uses a vowel-group counting algorithm with common English
    exceptions.

    Args:
        word: A single word.

    Returns:
        Estimated number of syllables.
    """
    word = word.lower().strip()
    if not word:
        return 0

    # Remove trailing 'e' (silent e)
    if word.endswith('e') and len(word) > 2:
        word = word[:-1]

    # Handle special cases
    specials = {
        "the": 1, "he": 1, "she": 1, "we": 1, "me": 1,
        "be": 1, "to": 1, "do": 1, "go": 1, "so": 1,
        "no": 1, "by": 1, "my": 1, "ly": 1,
        "area": 3, "idea": 3, "real": 2,
        "every": 3, "evening": 3,
        "beautiful": 3, "family": 3,
    }
    if word in specials:
        return specials[word]

    # Count vowel groups
    vowels = "aeiouy"
    count = 0
    prev_is_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel

    # Ensure at least 1 syllable
    if count == 0:
        count = 1

    return count


def _fk_interpretation(fk: float) -> str:
    """Provide interpretation of Flesch-Kincaid score.

    Args:
        fk: Flesch-Kincaid grade level.

    Returns:
        Interpretation string.
    """
    if fk < 6:
        return "Elementary school level"
    elif fk < 9:
        return "Middle school level"
    elif fk < 12:
        return "High school level"
    elif fk <= 16:
        return "College / Academic level (expected range)"
    else:
        return "Graduate / Professional level"
