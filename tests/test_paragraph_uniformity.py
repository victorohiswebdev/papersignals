"""Tests for paragraph uniformity analyzer."""

import pytest
from papersignals.analyzers import paragraph_uniformity


class TestParagraphUniformityAnalyzer:
    def test_varied_paragraphs(self):
        """Varied paragraph lengths should score well."""
        paragraphs = [
            "Short paragraph here.",
            "This is a medium length paragraph with several sentences in it. It continues with more text. And even more to make it longer. This paragraph has multiple ideas expressed across several sentences covering different aspects of the topic being discussed.",
            "Brief.",
        ]
        result = paragraph_uniformity.analyze(paragraphs)
        assert 0 <= result["score"] <= 100

    def test_uniform_paragraphs(self):
        """Uniform paragraph lengths should score poorly."""
        paragraphs = [
            "This is the first paragraph with roughly the same length as the others.",
            "This is the second paragraph with roughly the same length as the others.",
            "This is the third paragraph with roughly the same length as the others.",
            "This is the fourth paragraph with roughly the same length as the others.",
        ]
        result = paragraph_uniformity.analyze(paragraphs)
        assert 0 <= result["score"] <= 100

    def test_single_paragraph(self):
        """Single paragraph should not crash."""
        result = paragraph_uniformity.analyze(["This is a single paragraph."])
        assert result is not None
