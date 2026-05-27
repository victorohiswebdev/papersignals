#!/usr/bin/env python3
"""Train the RF classifier on the corpus data (Phase 2).

Usage:
    cd ~/projects/papersignals
    source venv/bin/activate
    python -m papersignals.classifier.train

Requires the corpus to have analyzed papers first (run
'papersignals corpus update' or the full pipeline).

Output:
    ~/.papersignals/models/rf_classifier.joblib  — trained model
    ~/.papersignals/models/rf_metadata.json       — training metadata
"""

from __future__ import annotations

import logging
import sys

from papersignals.classifier import RFClassifier
from papersignals.corpus.corpus_db import CorpusDB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("train_classifier")


def main() -> int:
    """Train the RF classifier from the corpus."""
    print("=" * 55)
    print("  RF Classifier Training — PaperSignals Phase 2")
    print("=" * 55)

    # Check corpus state
    db = CorpusDB()
    analyzed = db.total_analyzed()

    if analyzed == 0:
        print("\n❌ No analyzed papers in corpus.")
        print("   Run the pipeline first:")
        print("     papersignals corpus fetch")
        print("     papersignals corpus update")
        print("   Or: python -m papersignals.corpus.pipeline all")
        return 1

    print(f"\n📊 Corpus: {db.total_papers()} papers ({analyzed} analyzed)")

    # Train
    print(f"\n🧠 Training classifier (human={analyzed}, ai=~{analyzed}) ...")
    print("   This will generate synthetic AI text from each paper")
    print("   and train a calibrated Random Forest. May take a while.\n")

    classifier = RFClassifier()

    try:
        metadata = classifier.train_from_corpus(
            corpus_db=db,
            human_papers_limit=analyzed,
            ai_papers_limit=analyzed,
            cv_folds=5,
            test_size=0.2,
        )
    except ValueError as e:
        print(f"\n❌ {e}")
        return 1

    print(f"\n✅ Training complete!")
    print(f"   Model: ~/.papersignals/models/rf_classifier.joblib")
    print(f"   Metadata: ~/.papersignals/models/rf_metadata.json")
    print()
    print(classifier.summary())

    return 0


if __name__ == "__main__":
    sys.exit(main())
