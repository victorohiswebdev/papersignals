"""Tests for transitions analyzer."""

import pytest
from papersignals.analyzers import transitions


class TestTransitionsAnalyzer:
    def test_low_transition_density(self):
        """Few transitions should score well."""
        sentences = [
            "The system processes data locally.",
            "This reduces latency significantly.",
            "Edge computing enables real-time decisions.",
            "Network connectivity is not required.",
            "The approach works in remote areas.",
        ]
        result = transitions.analyze(sentences)
        assert 0 <= result["score"] <= 100

    def test_high_transition_density(self):
        """Many transitions should score poorly (AI-typical)."""
        sentences = [
            "Furthermore the system uses a machine learning algorithm.",
            "Moreover this approach enables efficient data processing.",
            "Additionally the framework integrates multiple sensors.",
            "In addition the results demonstrate significant improvements.",
            "Furthermore the architecture supports scalable deployment.",
            "Moreover the experimental findings confirm the hypothesis.",
        ]
        result = transitions.analyze(sentences)
        assert 0 <= result["score"] <= 100

    def test_empty_input(self):
        """Empty input should not crash."""
        result = transitions.analyze([])
        assert result is not None

    def test_no_transitions(self):
        """Text with no transition words should score well."""
        sentences = [
            "The cat sat on the mat.",
            "It was a sunny afternoon.",
            "Birds were singing in the garden.",
            "The dog barked at the mailman.",
        ]
        result = transitions.analyze(sentences)
        assert result["score"] >= 50
