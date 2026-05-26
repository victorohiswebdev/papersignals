"""Tests for lexical diversity analyzer."""

import pytest
from papersignals.analyzers import lexical_diversity


class TestLexicalDiversityAnalyzer:
    def test_high_diversity(self):
        """High TTR should score well."""
        text = (
            "The integration of edge computing with artificial intelligence "
            "has emerged as a transformative paradigm in precision agriculture. "
            "This convergence addresses critical limitations in conventional "
            "IoT based farming systems particularly in developing economies "
            "where intermittent network connectivity renders cloud dependent "
            "architectures impractical for time sensitive operations."
        )
        result = lexical_diversity.analyze(text)
        assert 0 <= result["score"] <= 100
        assert result["raw"]["type_token_ratio"] > 0.5

    def test_low_diversity(self):
        """Low TTR should score poorly."""
        text = "The system uses the system for the system to process the system data for the system."
        result = lexical_diversity.analyze(text)
        assert 0 <= result["score"] <= 100

    def test_empty_string(self):
        """Empty string should not crash."""
        result = lexical_diversity.analyze("")
        assert result is not None

    def test_single_word(self):
        """Single word should not crash."""
        result = lexical_diversity.analyze("Hello")
        assert result is not None
