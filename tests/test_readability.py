"""Tests for readability analyzer."""

import pytest
from papersignals.analyzers import readability


class TestReadabilityAnalyzer:
    def test_academic_text(self):
        """Academic text should land in expected readability ranges."""
        text = (
            "The integration of edge computing with artificial intelligence "
            "has emerged as a transformative paradigm in precision agriculture. "
            "This convergence addresses critical limitations in conventional "
            "IoT based farming systems. The system architecture employs a "
            "Raspberry Pi as the edge compute node interfaced with an Arduino "
            "Uno co-processor for analog sensor data acquisition."
        )
        result = readability.analyze(text)
        assert 0 <= result["score"] <= 100
        assert result["raw"]["flesch_kincaid"] > 5

    def test_simple_text(self):
        """Simple text should have lower readability scores."""
        text = "The cat sat on the mat. It was a sunny day. The dog ran fast."
        result = readability.analyze(text)
        assert 0 <= result["score"] <= 100

    def test_empty_string(self):
        """Empty string should not crash."""
        result = readability.analyze("")
        assert result is not None
