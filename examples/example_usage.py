"""Example usage of papersignals analysis engine."""

from papersignals.core.document import parse_document, segment_text
from papersignals.core.scoring import compute_composite
from papersignals.analyzers import (
    burstiness,
    transitions,
    lexical_diversity,
    vocabulary as vocab_analyzer,
    paragraph_uniformity,
    readability,
    perplexity,
)


def analyze_text(text: str) -> dict:
    """Run full analysis pipeline on text."""
    segmented = segment_text(text)
    sentences = segmented["sentences"]
    paragraphs = segmented["paragraphs"]

    results = {
        "burstiness": burstiness.analyze(sentences),
        "transitions": transitions.analyze(sentences),
        "lexical_diversity": lexical_diversity.analyze(text),
        "vocabulary": vocab_analyzer.analyze(text),
        "paragraph_uniformity": paragraph_uniformity.analyze(paragraphs),
        "readability": readability.analyze(text),
        "perplexity": perplexity.analyze(text),
    }

    composite = compute_composite({k: v["score"] for k, v in results.items()})

    return {
        "metrics": results,
        "composite": composite,
        "document_stats": {
            "word_count": segmented["word_count"],
            "sentence_count": segmented["sentence_count"],
            "paragraph_count": segmented["paragraph_count"],
        },
    }


if __name__ == "__main__":
    sample = (
        "Edge AI represents a significant advancement in precision agriculture. "
        "By processing data locally on edge devices, farmers can make real-time "
        "decisions without depending on cloud connectivity. This is particularly "
        "valuable in remote agricultural regions where internet access is limited. "
        "The system employs a Raspberry Pi as the central compute node. "
        "Various sensors collect environmental data at regular intervals. "
        "A machine learning model processes this data to optimize irrigation schedules. "
        "The results demonstrate measurable improvements in water efficiency."
    )

    report = analyze_text(sample)
    print(f"Document stats: {report['document_stats']}")
    print(f"Composite score: {report['composite']['composite_score']:.1f}/100")
    print(f"Risk level: {report['composite']['risk_level']}")
    print("\nPer-metric scores:")
    for name, m in report["metrics"].items():
        print(f"  {name:25s} {m['score']:.1f}/100  (risk: {m['risk']})")
