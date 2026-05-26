"""Tests for scoring module."""

import pytest
from papersignals.core.scoring import normalize_score, compute_composite, _score_to_risk


class TestNormalizeScore:
    def test_min_value(self):
        assert normalize_score(0, 0, 100) == 0.0

    def test_max_value(self):
        assert normalize_score(100, 0, 100) == 100.0

    def test_mid_value(self):
        assert normalize_score(50, 0, 100) == 50.0

    def test_clamp_low(self):
        assert normalize_score(-10, 0, 100) == 0.0

    def test_clamp_high(self):
        assert normalize_score(110, 0, 100) == 100.0

    def test_degenerate_range(self):
        assert normalize_score(50, 10, 10) == 50.0


class TestCompositeScore:
    def test_all_perfect(self):
        scores = {k: 100.0 for k in [
            "burstiness", "transition_density", "lexical_diversity",
            "vocabulary_fingerprint", "paragraph_uniformity", "readability", "perplexity"
        ]}
        result = compute_composite(scores)
        assert result["composite_score"] == 100.0
        assert result["risk"] == "low"

    def test_all_zero(self):
        scores = {k: 0.0 for k in [
            "burstiness", "transition_density", "lexical_diversity",
            "vocabulary_fingerprint", "paragraph_uniformity", "readability", "perplexity"
        ]}
        result = compute_composite(scores)
        assert result["composite_score"] == 0.0
        assert result["risk"] == "high"

    def test_partial_scores(self):
        result = compute_composite({"burstiness": 100.0, "readability": 50.0})
        assert result["composite_score"] > 0
        assert len(result["individual_scores"]) == 2

    def test_empty_scores(self):
        result = compute_composite({})
        assert result["composite_score"] == 50.0


class TestScoreToRisk:
    def test_high_risk(self):
        assert _score_to_risk(20) == "high"
        assert _score_to_risk(34) == "high"

    def test_medium_risk(self):
        assert _score_to_risk(35) == "medium"
        assert _score_to_risk(50) == "medium"
        assert _score_to_risk(65) == "medium"

    def test_low_risk(self):
        assert _score_to_risk(66) == "low"
        assert _score_to_risk(100) == "low"
