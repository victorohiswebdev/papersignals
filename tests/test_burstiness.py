"""Tests for burstiness analyzer."""

import pytest
from papersignals.analyzers import burstiness


class TestBurstinessAnalyzer:
    def test_varied_sentence_lengths(self):
        """High variance in sentence length should score well."""
        sentences = [
            "This is a short sentence.",
            "Here is another brief one.",
            "This sentence, however, is deliberately long and complex because it contains multiple clauses, subordinate structures, and qualifying information that extends its length considerably beyond the average.",
            "Short again.",
            "This one is medium length with several words.",
            "A brief punch.",
            "This sentence explores the intricate relationship between multiple variables in a controlled experimental setting, demonstrating the complexity of natural language patterns.",
            "Terse.",
        ]
        result = burstiness.analyze(sentences)
        assert 0 <= result["score"] <= 100
        assert result["risk"] in ("low", "medium")
        assert result["raw"]["std_dev"] > 5

    def test_uniform_sentences(self):
        """Uniform sentence lengths should score poorly (AI-typical)."""
        sentences = [
            "The system uses a machine learning algorithm for data processing.",
            "This approach enables efficient real time decision making capabilities.",
            "Furthermore the framework integrates multiple sensor inputs seamlessly.",
            "Moreover the results demonstrate significant improvements in accuracy.",
            "Additionally the architecture supports scalable deployment options.",
            "It is important to note that the methodology was validated thoroughly.",
            "The experimental findings confirm the initial research hypotheses.",
            "In conclusion this work presents a comprehensive analytical framework.",
        ]
        result = burstiness.analyze(sentences)
        assert 0 <= result["score"] <= 100
        if result["raw"]["std_dev"] < 4:
            assert result["risk"] == "high"

    def test_single_sentence(self):
        """Single sentence should not crash and return neutral score."""
        result = burstiness.analyze(["This is a single sentence."])
        assert 0 <= result["score"] <= 100
        assert result["risk"] in ("low", "medium", "high")

    def test_empty_input(self):
        """Empty input should not crash."""
        result = burstiness.analyze([])
        assert result["score"] == 100 or result["risk"] == "low"

    def test_consecutive_similar_detection(self):
        """Should detect consecutive sentences of similar length."""
        sentences = [
            "This sentence has exactly eight words here.",
            "Here is another eight word sentence now.",
            "This one also has eight total words see.",
            "Different length sentence right here okay.",
            "Back to the eight word pattern again now.",
            "And here we have another set of eight.",
            "Short one.",
            "Eight word sentence pattern continues more.",
        ]
        result = burstiness.analyze(sentences)
        assert "consecutive_similar_groups" in result["raw"]
