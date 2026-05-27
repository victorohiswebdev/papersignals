"""Corpus pipeline orchestrator for papersignals Phase 2.

Orchestrates the full corpus workflow:
  1. Fetch papers from arXiv across multiple categories
  2. Run all 7 analyzers on each paper's abstract
  3. Compute baseline percentile distributions
  4. Save baseline norms for the scoring engine

Usage:
    python -m papersignals.corpus.pipeline fetch    # Step 1: fetch papers
    python -m papersignals.corpus.pipeline analyze  # Step 2: run analyzers
    python -m papersignals.corpus.pipeline norms    # Step 3: compute norms
    python -m papersignals.corpus.pipeline all      # Steps 1-3 in sequence
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from typing import Dict, List

from papersignals.cli import run_analysis
from papersignals.corpus.arxiv_fetcher import DEFAULT_CATEGORIES, ArxivFetcher
from papersignals.corpus.corpus_db import AnalysisResult, CorpusDB
from papersignals.corpus.norms import NormsCalculator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("corpus_pipeline")


def cmd_fetch(
    categories: List[str],
    per_category: int,
    force: bool = False,
) -> int:
    """Fetch papers from arXiv and save to local corpus DB.

    Returns:
        Number of new papers saved.
    """
    logger.info(
        "Fetching %d papers per category from %d categories ...",
        per_category,
        len(categories),
    )
    logger.info("Categories: %s", ", ".join(categories))

    fetcher = ArxivFetcher()
    all_papers = fetcher.fetch_multiple_categories(
        categories=categories,
        per_category=per_category,
        force_refetch=force,
    )

    db = CorpusDB()
    total_new = 0
    for cat, papers in all_papers.items():
        if not papers:
            logger.warning("No papers fetched for %s", cat)
            continue
        paper_dicts = [p.to_dict() for p in papers]
        new_count = db.save_papers(paper_dicts)
        total_new += new_count
        logger.info(
            "  %s: %d papers (%d new)",
            cat,
            len(papers),
            new_count,
        )

    total = db.total_papers()
    logger.info(
        "Done fetching. Corpus now has %d papers (%d new this run).",
        total,
        total_new,
    )
    return total_new


def cmd_analyze(limit: int = 0) -> int:
    """Run all 7 analyzers on unanalyzed papers in the corpus.

    Args:
        limit: Max papers to analyze this run (0 = all).

    Returns:
        Number of papers analyzed.
    """
    db = CorpusDB()
    unanalyzed = db.unanalyzed_papers()

    if not unanalyzed:
        logger.info("All papers in corpus have been analyzed already.")
        return 0

    if limit > 0:
        unanalyzed = unanalyzed[:limit]

    logger.info("Analyzing %d papers ...", len(unanalyzed))
    analyzed_count = 0
    errors = 0

    for i, paper in enumerate(unanalyzed):
        paper_id = paper.get("arxiv_id", "unknown")
        abstract = paper.get("abstract", "")

        if not abstract or len(abstract.strip()) < 50:
            logger.debug("Skipping %s: abstract too short", paper_id)
            continue

        try:
            # We run the analyzers via the document parsing + segmentation
            # path, reusing the same pipeline that analyze command uses.
            # We create a virtual document by wrapping the abstract text.
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as f:
                f.write(abstract)
                tmp_path = f.name

            try:
                analysis = run_analysis(tmp_path)
            finally:
                os.unlink(tmp_path)

            # Extract signal results
            signals = analysis.get("signals", {})

            result = AnalysisResult(
                paper_id=paper_id,
                burstiness=signals.get("burstiness", {}),
                transition_density=signals.get("transition_density", {}),
                lexical_diversity=signals.get("lexical_diversity", {}),
                vocabulary_fingerprint=signals.get("vocabulary_fingerprint", {}),
                paragraph_uniformity=signals.get("paragraph_uniformity", {}),
                readability=signals.get("readability", {}),
                perplexity=signals.get("perplexity", {}),
            )
            result.analyzed_at = __import__(
                "datetime"
            ).datetime.now().isoformat()

            db.save_analysis(paper_id, result)
            analyzed_count += 1

            if (i + 1) % 50 == 0:
                logger.info(
                    "  Progress: %d/%d analyzed (%d errors)",
                    i + 1,
                    len(unanalyzed),
                    errors,
                )

        except Exception as e:
            logger.warning("Error analyzing %s: %s", paper_id, e)
            errors += 1

    total = db.total_analyzed()
    logger.info(
        "Done. Analyzed %d papers this run (%d errors). "
        "Total analyzed: %d / %d in corpus.",
        analyzed_count,
        errors,
        total,
        db.total_papers(),
    )
    return analyzed_count


def cmd_norms(output_path: str = "") -> str:
    """Compute and save baseline norms from analyzed corpus.

    Args:
        output_path: Path for output norms JSON.

    Returns:
        Path to saved norms file.
    """
    db = CorpusDB()
    total = db.total_analyzed()

    if total < 10:
        logger.warning(
            "Only %d papers analyzed. Need at least 10 for meaningful norms. "
            "Run 'analyze' on more papers first.",
            total,
        )

    calculator = NormsCalculator(db)

    if output_path:
        saved = calculator.save_baseline(output_path)
    else:
        saved = calculator.save_baseline()

    # Print summary
    baseline = calculator.load_baseline(saved)
    norms = baseline.get("norms", {})
    metadata = baseline.get("metadata", {})

    print(f"\n📊 Baseline Norms Summary")
    print(f"   Papers analyzed: {metadata.get('total_analyzed', 0)}")
    print(f"   Categories: {len(metadata.get('categories', {}))}")
    print()

    for signal_name, signal_norms in norms.items():
        print(f"  {signal_name}:")
        for metric_key, metric_data in signal_norms.items():
            percentiles = metric_data.get("percentiles", {})
            stats = metric_data.get("stats", {})
            p5 = percentiles.get("p5", 0)
            p50 = percentiles.get("p50", 0)
            p95 = percentiles.get("p95", 0)
            print(
                f"    {metric_key}: p5={p5:.1f}  p50={p50:.1f}  p95={p95:.1f}  "
                f"mean={stats.get('mean', 0):.2f}  n={stats.get('count', 0)}"
            )
    print(f"\n   Norms saved to: {saved}")

    return saved


def cmd_all(
    categories: List[str],
    per_category: int,
    analyze_limit: int = 0,
    force_fetch: bool = False,
) -> None:
    """Run the full corpus pipeline: fetch → analyze → norms."""
    logger.info("=" * 50)
    logger.info("PHASE 2 CORPUS PIPELINE — Starting")
    logger.info("=" * 50)

    # Step 1: Fetch
    t0 = time.time()
    cmd_fetch(categories, per_category, force=force_fetch)
    t1 = time.time()
    logger.info("Fetch completed in %.1fs", t1 - t0)

    # Step 2: Analyze
    cmd_analyze(limit=analyze_limit)
    t2 = time.time()
    logger.info("Analysis completed in %.1fs", t2 - t1)

    # Step 3: Norms
    cmd_norms()
    t3 = time.time()
    logger.info("Norms computed in %.1fs", t3 - t2)

    logger.info("=" * 50)
    logger.info("CORPUS PIPELINE COMPLETE (total: %.1fs)", t3 - t0)
    logger.info("=" * 50)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="papersignals-corpus-pipeline",
        description="ArXiv corpus pipeline for papersignals Phase 2.",
    )
    parser.add_argument(
        "command",
        choices=["fetch", "analyze", "norms", "all"],
        help="Pipeline step to run.",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        default=[],
        help="arXiv categories to fetch (default: all default categories).",
    )
    parser.add_argument(
        "--per-category",
        type=int,
        default=60,
        help="Papers to fetch per category (default: 60).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max papers to analyze (0 = all unanalyzed).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-fetch categories even if cached.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Output path for norms JSON.",
    )
    return parser


def main(argv: list = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    categories = args.categories or DEFAULT_CATEGORIES

    if args.command == "fetch":
        cmd_fetch(categories, args.per_category, force=args.force)
    elif args.command == "analyze":
        cmd_analyze(limit=args.limit)
    elif args.command == "norms":
        cmd_norms(output_path=args.output)
    elif args.command == "all":
        cmd_all(
            categories,
            args.per_category,
            analyze_limit=args.limit,
            force_fetch=args.force,
        )
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
