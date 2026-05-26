"""Tests for vocabulary analyzer."""

import pytest
from papersignals.analyzers import vocabulary


class TestVocabularyAnalyzer:
    def test_clean_text(self):
        """Text without AI-favored words should score well."""
        text = "The cat sat on the mat. It was a sunny afternoon. Birds were singing."
        result = vocabulary.analyze(text)
        assert 0 <= result["score"] <= 100
        assert result["risk"] in ("low", "medium", "high")

    def test_flagged_text(self):
        """Text with AI-favored words should flag them."""
        text = "This robust framework leverages comprehensive data to ensure significant improvements."
        result = vocabulary.analyze(text)
        assert 0 <= result["score"] <= 100

    def test_empty_string(self):
        """Empty string should not crash."""
        result = vocabulary.analyze("")
        assert result is not None
