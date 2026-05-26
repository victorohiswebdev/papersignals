"""Command-line interface for papersignals.

Usage:
    papersignals analyze <file> [--json] [--detailed] [--output FILE]
    papersignals corpus update
    papersignals corpus stats
    papersignals --version
"""

import argparse
import sys
import os
from typing import Dict, Any, Optional

from papersignals import __version__
from papersignals.core.document import parse_document, segment_text
from papersignals.core.scoring import compute_composite
from papersignals.core.report import (
    generate_markdown_report,
    generate_json_report,
    generate_detailed_report,
)
from papersignals.analyzers import (
    burstiness,
    transitions,
    lexical_diversity,
    vocabulary,
    paragraph_uniformity,
    readability,
    perplexity,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="papersignals",
        description="Analyze academic writing for signals that correlate with AI detection.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"papersignals v{__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze a document for AI signals"
    )
    analyze_parser.add_argument(
        "file", type=str, help="Path to the document file (.txt, .md, .docx)"
    )
    analyze_parser.add_argument(
        "--json", action="store_true", help="Output JSON instead of markdown"
    )
    analyze_parser.add_argument(
        "--detailed", action="store_true", help="Include per-sentence breakdown"
    )
    analyze_parser.add_argument(
        "--output", type=str, help="Write output to file instead of stdout"
    )

    # corpus command
    corpus_parser = subparsers.add_parser(
        "corpus", help="Manage the corpus of known documents"
    )
    corpus_subparsers = corpus_parser.add_subparsers(
        dest="corpus_command", help="Corpus operations"
    )
    corpus_subparsers.add_parser("update", help="Update the corpus database")
    corpus_subparsers.add_parser("stats", help="Show corpus statistics")

    return parser


def run_analysis(file_path: str) -> Dict[str, Any]:
    """Run the full analysis pipeline on a document.

    Args:
        file_path: Path to the document file.

    Returns:
        Complete analysis dict with all signals and composite score.
    """
    # Parse document
    doc = parse_document(file_path)
    segments = segment_text(doc["text"])

    # Run all analyzers
    sentences = segments["sentences"]
    paragraphs = segments["paragraphs"]
    text = doc["text"]

    signals: Dict[str, Dict] = {}

    signals["burstiness"] = burstiness.analyze(sentences)
    signals["transition_density"] = transitions.analyze(sentences)
    signals["lexical_diversity"] = lexical_diversity.analyze(text)
    signals["vocabulary_fingerprint"] = vocabulary.analyze(text)
    signals["paragraph_uniformity"] = paragraph_uniformity.analyze(paragraphs)
    signals["readability"] = readability.analyze(text)
    signals["perplexity"] = perplexity.analyze(text)

    # Compute composite score
    scores = {
        name: data.get("score")
        for name, data in signals.items()
    }
    composite = compute_composite(scores)

    return {
        "document": {
            "name": doc["name"],
            "path": doc["path"],
        },
        "segments": {
            "word_count": segments["word_count"],
            "sentence_count": segments["sentence_count"],
            "paragraph_count": segments["paragraph_count"],
        },
        "signals": signals,
        "composite": composite,
    }


def handle_analyze(args: argparse.Namespace) -> int:
    """Handle the 'analyze' subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    file_path = args.file

    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    try:
        analysis = run_analysis(file_path)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error during analysis: {e}", file=sys.stderr)
        return 1

    # Generate output
    if args.json:
        output = generate_json_report(analysis)
    elif args.detailed:
        output = generate_detailed_report(analysis)
    else:
        output = generate_markdown_report(analysis)

    # Write output
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Report written to: {args.output}")
        except OSError as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            return 1
    else:
        print(output)

    return 0


def handle_corpus(args: argparse.Namespace) -> int:
    """Handle the 'corpus' subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    if args.corpus_command == "update":
        print("Corpus update: Not yet implemented.")
        print("This feature will analyze a directory of documents and store results.")
        return 0
    elif args.corpus_command == "stats":
        print("Corpus statistics: Not yet implemented.")
        print("This feature will show aggregate statistics across the corpus.")
        return 0
    else:
        print("Usage: papersignals corpus {update|stats}", file=sys.stderr)
        return 1


def main(argv: Optional[list] = None) -> int:
    """Main entry point for the papersignals CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        return handle_analyze(args)
    elif args.command == "corpus":
        return handle_corpus(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
