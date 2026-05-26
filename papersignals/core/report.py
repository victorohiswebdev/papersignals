"""Report generation for papersignals."""

import json
from typing import Dict, List, Any


def _score_bar(score: float) -> str:
    """Generate a simple ASCII/Unicode gauge bar for a score.

    Args:
        score: Score from 0-100.

    Returns:
        A string like '████████░░ 80/100'.
    """
    filled = max(0, min(10, int(score / 10)))
    empty = 10 - filled
    bar = "█" * filled + "░" * empty
    return f"{bar} {score:.0f}/100"


def _risk_emoji(risk: str) -> str:
    """Get emoji for a risk level.

    Args:
        risk: 'low', 'medium', or 'high'.

    Returns:
        Emoji string.
    """
    return {"low": "✅", "medium": "⚠️", "high": "🔴"}.get(risk, "❓")


def _format_flag_section(flagged: Dict[str, Any]) -> str:
    """Format a flagged items section for the markdown report.

    Args:
        flagged: Dict with 'type' and list of flagged items.

    Returns:
        Markdown string or empty string if no items.
    """
    lines: List[str] = []
    for key, items in flagged.items():
        if items and len(items) > 0:
            lines.append(f"  - **{key.replace('_', ' ').title()}**: {len(items)} found")
            # Show first few
            for item in items[:5]:
                if isinstance(item, dict):
                    detail = item.get("text", item.get("word", str(item)))
                    if len(detail) > 80:
                        detail = detail[:77] + "..."
                    lines.append(f"    - `{detail}`")
                else:
                    item_str = str(item)
                    if len(item_str) > 80:
                        item_str = item_str[:77] + "..."
                    lines.append(f"    - `{item_str}`")
            if len(items) > 5:
                lines.append(f"    - *...and {len(items) - 5} more*")
    return "\n".join(lines)


def generate_markdown_report(analysis: dict) -> str:
    """Generate a formatted markdown report.

    Args:
        analysis: Complete analysis dict from the pipeline.

    Returns:
        Markdown string.
    """
    doc_info = analysis.get("document", {})
    segments = analysis.get("segments", {})
    signals = analysis.get("signals", {})
    composite = analysis.get("composite", {})

    lines: List[str] = []
    lines.append(f"# 📄 Papersignals Analysis Report")
    lines.append(f"")
    lines.append(f"**Document**: {doc_info.get('name', 'Unknown')}")
    lines.append(f"**Word Count**: {segments.get('word_count', 0)}")
    lines.append(f"**Sentences**: {segments.get('sentence_count', 0)}")
    lines.append(f"**Paragraphs**: {segments.get('paragraph_count', 0)}")
    lines.append(f"")

    # Composite score
    comp_score = composite.get("composite_score", 50.0)
    comp_risk = composite.get("risk", "medium")
    lines.append(f"## Overall Assessment")
    lines.append(f"")
    lines.append(f"{_risk_emoji(comp_risk)} **Risk Level**: {comp_risk.upper()}")
    lines.append(f"")
    lines.append(f"**Composite Score**:")
    lines.append(f"")
    lines.append(f"```")
    lines.append(f"{_score_bar(comp_score)}")
    lines.append(f"```")
    lines.append(f"")
    lines.append(f"| Metric | Score | Risk |")
    lines.append(f"|--------|-------|------|")
    ind_scores = composite.get("individual_scores", {})
    for metric, score in ind_scores.items():
        metric_risk = _score_to_risk(score)
        emoji = _risk_emoji(metric_risk)
        lines.append(
            f"| {metric.replace('_', ' ').title()} | {score:.1f}/100 | {emoji} {metric_risk} |"
        )
    lines.append(f"")

    # Per-metric details
    lines.append(f"## Signal Details")
    lines.append(f"")

    for metric_name, signal in signals.items():
        metric_label = metric_name.replace("_", " ").title()
        score = signal.get("score", 50.0)
        risk = signal.get("risk", "medium")
        raw = signal.get("raw", {})

        lines.append(f"### {metric_label}")
        lines.append(f"")
        lines.append(f"- **Score**: {score:.1f}/100")
        lines.append(f"- **Risk**: {_risk_emoji(risk)} {risk.upper()}")

        # Add raw stats
        if raw:
            lines.append(f"- **Stats**:")
            for stat_key, stat_val in raw.items():
                if isinstance(stat_val, float):
                    lines.append(f"  - {stat_key.replace('_', ' ').title()}: {stat_val:.2f}")
                else:
                    lines.append(f"  - {stat_key.replace('_', ' ').title()}: {stat_val}")

        # Flagged items
        details = signal.get("details", {})
        if details:
            flagged_text = _format_flag_section(details)
            if flagged_text:
                lines.append(f"- **Flags**:")
                lines.append(flagged_text)

        lines.append(f"")

    # Recommendations
    lines.append(f"## Recommendations")
    lines.append(f"")
    recommendations = _generate_recommendations(composite, signals)
    if recommendations:
        for rec in recommendations:
            lines.append(f"- {rec}")
    else:
        lines.append(f"- No specific recommendations - text appears natural.")
    lines.append(f"")

    lines.append(f"---")
    lines.append(f"*Generated by papersignals v0.1.0*")

    return "\n".join(lines)


def _score_to_risk(score: float) -> str:
    """Convert a 0-100 score to a risk level string.

    Args:
        score: Score from 0-100.

    Returns:
        'high', 'medium', or 'low'.
    """
    if score < 35:
        return "high"
    elif score <= 65:
        return "medium"
    else:
        return "low"


def _generate_recommendations(composite: Dict, signals: Dict) -> List[str]:
    """Generate actionable recommendations based on signal analysis.

    Args:
        composite: Composite scoring results.
        signals: Individual signal analysis results.

    Returns:
        List of recommendation strings.
    """
    recs: List[str] = []

    # Burstiness
    burst = signals.get("burstiness", {})
    if burst.get("risk") == "high":
        recs.append(
            "📏 **Sentence length variation is low** — Try varying sentence lengths. "
            "Mix short, punchy sentences with longer, complex ones to create a more natural rhythm."
        )
    elif burst.get("risk") == "medium":
        recs.append(
            "📏 **Sentence length variation could be improved** — "
            "Add more variety in sentence lengths to reduce repetitive patterns."
        )

    # Transition density
    trans = signals.get("transition_density", {})
    if trans.get("risk") == "high":
        recs.append(
            "🔗 **High transition word density** — Reduce the use of explicit transition words. "
            "Rely more on natural logical flow between sentences rather than overt signposting."
        )

    # Lexical diversity
    lex = signals.get("lexical_diversity", {})
    if lex.get("risk") in ("high", "medium"):
        recs.append(
            "📖 **Lexical diversity is limited** — Broaden your vocabulary. "
            "Use more synonyms and varied word choices to increase lexical richness."
        )

    # Vocabulary fingerprint
    vocab = signals.get("vocabulary_fingerprint", {})
    if vocab.get("risk") == "high":
        recs.append(
            "🔤 **AI-favored vocabulary detected** — Replace common AI-signaling words "
            "(e.g., 'delve', 'leverage', 'utilize') with more natural alternatives."
        )

    # Paragraph uniformity
    para = signals.get("paragraph_uniformity", {})
    if para.get("risk") == "high":
        recs.append(
            "📐 **Paragraph lengths are too uniform** — Vary paragraph lengths. "
            "Some paragraphs can be a single sentence, others several paragraphs long."
        )

    # Readability
    read = signals.get("readability", {})
    if read.get("raw", {}).get("flesch_kincaid", 0) < 10:
        recs.append(
            "📊 **Readability is lower than typical academic writing** — "
            "Consider simplifying sentence structures and vocabulary."
        )
    elif read.get("raw", {}).get("flesch_kincaid", 0) > 18:
        recs.append(
            "📊 **Readability is very high** — Academic writing typically scores "
            "FK 12-16. Very high readability may appear unnatural."
        )

    return recs


def generate_json_report(analysis: dict) -> str:
    """Generate a JSON report string.

    Args:
        analysis: Complete analysis dict from the pipeline.

    Returns:
        JSON string with indent=2.
    """
    return json.dumps(analysis, indent=2, default=str)


def _build_sentence_breakdown(signals: Dict, segments: Dict) -> List[Dict]:
    """Build per-sentence breakdown entries.

    Args:
        signals: Dict of signal analysis results.
        segments: Dict with 'sentences' list.

    Returns:
        List of dicts, one per sentence with individual scores.
    """
    sentences = segments.get("sentences", [])
    breakdown: List[Dict] = []
    for i, sent in enumerate(sentences):
        entry = {
            "index": i + 1,
            "text": sent,
            "length": len(sent.split()),
        }
        breakdown.append(entry)
    return breakdown


def generate_detailed_report(analysis: dict) -> str:
    """Generate a detailed report including per-sentence breakdown.

    Args:
        analysis: Complete analysis dict from the pipeline.

    Returns:
        Markdown string with detailed breakdown.
    """
    base_report = generate_markdown_report(analysis)
    segments = analysis.get("segments", {})
    signals = analysis.get("signals", {})

    lines = base_report.split("\n")
    lines.append(f"")
    lines.append(f"## Per-Sentence Breakdown")
    lines.append(f"")
    sentences = segments.get("sentences", [])
    for i, sent in enumerate(sentences):
        word_len = len(sent.split())
        lines.append(f"**{i+1}.** ({word_len} words) {sent}")

    return "\n".join(lines)
