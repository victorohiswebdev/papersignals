"""Individual signal analyzers for papersignals.

Each analyzer module exports a single `analyze()` function that takes
text/sentences/paragraphs and returns a standardized result dict.
"""

from papersignals.analyzers import (
    burstiness,
    transitions,
    lexical_diversity,
    vocabulary,
    paragraph_uniformity,
    readability,
    perplexity,
)

__all__ = [
    "burstiness",
    "transitions",
    "lexical_diversity",
    "vocabulary",
    "paragraph_uniformity",
    "readability",
    "perplexity",
]
