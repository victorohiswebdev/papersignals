"""Feature extraction for papersignals RF classifier.

Converts the output of the 7 analyzers into feature vectors
for training the Random Forest classifier.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np


# Feature names and their extraction paths from analyzer results
# Format: (feature_name, signal_key, raw_subkey, default_value)
FEATURE_DEFINITIONS: List[tuple[str, str, str, float]] = [
    # Burstiness
    ("burstiness_std_dev", "burstiness", "std_dev", 0.0),
    ("burstiness_cv", "burstiness", "coefficient_of_variation", 0.0),
    ("burstiness_consecutive", "burstiness", "consecutive_similar_groups", 0),
    # Transitions
    ("transition_density", "transition_density", "density_per_100_words", 0.0),
    ("transition_unique_types", "transition_density", "unique_types", 0.0),
    # Lexical diversity
    ("lexical_ttr", "lexical_diversity", "type_token_ratio", 0.5),
    ("lexical_hapax", "lexical_diversity", "hapax_richness", 0.3),
    # Vocabulary fingerprint
    ("vocab_hits", "vocabulary_fingerprint", "total_flagged", 0),
    ("vocab_density", "vocabulary_fingerprint", "density_per_1000_words", 0.0),
    # Paragraph uniformity
    ("para_std_dev", "paragraph_uniformity", "std_dev_words", 0.0),
    ("para_mean_words", "paragraph_uniformity", "mean_words", 50.0),
    # Readability
    ("readability_fk", "readability", "flesch_kincaid", 12.0),
    ("readability_fog", "readability", "gunning_fog", 14.0),
    # Perplexity
    ("perplexity_estimated", "perplexity", "estimated_perplexity", 100.0),
]

NUM_FEATURES = len(FEATURE_DEFINITIONS)


def extract_features_from_analysis(signals: Dict[str, Any]) -> np.ndarray:
    """Extract a feature vector from analyzer signal results.

    Args:
        signals: Dict from cli.run_analysis()['signals'], where each
                 value is the analyzer result dict.

    Returns:
        NumPy array of shape (NUM_FEATURES,) with feature values.
    """
    features = np.zeros(NUM_FEATURES, dtype=np.float64)

    for i, (name, signal_key, raw_key, default) in enumerate(FEATURE_DEFINITIONS):
        signal_data = signals.get(signal_key, {})
        # Try 'raw' sub-dict first (most analyzers nest under 'raw')
        raw = signal_data.get("raw", signal_data)
        if isinstance(raw, dict):
            value = raw.get(raw_key, default)
        else:
            value = default

        if value is None:
            value = default

        features[i] = float(value)

    return features


def get_feature_names() -> List[str]:
    """Get the list of feature names in order."""
    return [name for name, _, _, _ in FEATURE_DEFINITIONS]


def features_to_dict(features: np.ndarray) -> Dict[str, float]:
    """Convert a feature vector to a named dict.

    Args:
        features: NumPy array of shape (NUM_FEATURES,).

    Returns:
        Dict mapping feature names to values.
    """
    names = get_feature_names()
    return {name: float(features[i]) for i, name in enumerate(names)}
