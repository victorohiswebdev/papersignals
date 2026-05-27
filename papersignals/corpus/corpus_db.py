"""Local corpus database for papersignals Phase 2.

Stores fetched paper metadata and computed analysis results
in a local JSON-based store for offline use and incremental
updates.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Stores the result of running the 7 analyzers on a paper."""

    paper_id: str
    burstiness: Dict[str, Any]
    transition_density: Dict[str, Any]
    lexical_diversity: Dict[str, Any]
    vocabulary_fingerprint: Dict[str, Any]
    paragraph_uniformity: Dict[str, Any]
    readability: Dict[str, Any]
    perplexity: Dict[str, Any]
    analyzed_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "AnalysisResult":
        return cls(**data)


@dataclass
class CorpusStats:
    """Aggregate statistics for the entire corpus."""

    total_papers: int = 0
    total_analyzed: int = 0
    categories: Dict[str, int] = field(default_factory=dict)
    avg_word_count: float = 0.0
    created_at: str = ""


class CorpusDB:
    """Local on-disk database for the papersignals corpus.

    Stores papers in a simple directory structure under a root path.
    Each paper gets a JSON file indexed by arXiv ID.

    Args:
        root_dir: Root directory for corpus storage.
            Defaults to ~/.papersignals/corpus/.
    """

    def __init__(self, root_dir: Optional[str] = None):
        if root_dir is None:
            root_dir = os.path.expanduser("~/.papersignals/corpus")
        self.root_dir = root_dir

        # Sub-directories
        self._papers_dir = os.path.join(root_dir, "papers")
        self._analysis_dir = os.path.join(root_dir, "analysis")
        self._metadata_file = os.path.join(root_dir, "corpus_metadata.json")

        os.makedirs(self._papers_dir, exist_ok=True)
        os.makedirs(self._analysis_dir, exist_ok=True)

    # ----------------------------------------------------------------
    # Paper storage
    # ----------------------------------------------------------------

    def save_papers(self, papers: List[Dict]) -> int:
        """Save paper records to the database.

        Args:
            papers: List of paper dicts (from PaperRecord.to_dict()).

        Returns:
            Number of papers saved (newly added).
        """
        count = 0
        for paper in papers:
            paper_id = paper.get("arxiv_id", "")
            if not paper_id:
                continue
            path = os.path.join(self._papers_dir, f"{paper_id}.json")
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(paper, f, indent=2, ensure_ascii=False)
                count += 1
        return count

    def get_paper(self, paper_id: str) -> Optional[Dict]:
        """Get a single paper by arXiv ID."""
        path = os.path.join(self._papers_dir, f"{paper_id}.json")
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_all_papers(self) -> List[Dict]:
        """Get all stored papers."""
        papers: List[Dict] = []
        if not os.path.isdir(self._papers_dir):
            return papers
        for fn in sorted(os.listdir(self._papers_dir)):
            if fn.endswith(".json"):
                path = os.path.join(self._papers_dir, fn)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        papers.append(json.load(f))
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning("Failed to read %s: %s", fn, e)
        return papers

    def total_papers(self) -> int:
        """Count total papers in the database."""
        if not os.path.isdir(self._papers_dir):
            return 0
        return len(
            [f for f in os.listdir(self._papers_dir) if f.endswith(".json")]
        )

    # ----------------------------------------------------------------
    # Analysis results storage
    # ----------------------------------------------------------------

    def save_analysis(self, paper_id: str, result: AnalysisResult) -> None:
        """Save analysis results for a paper.

        Args:
            paper_id: arXiv paper ID.
            result: AnalysisResult from running the analyzers.
        """
        path = os.path.join(self._analysis_dir, f"{paper_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    def get_analysis(self, paper_id: str) -> Optional[AnalysisResult]:
        """Get analysis results for a paper."""
        path = os.path.join(self._analysis_dir, f"{paper_id}.json")
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AnalysisResult.from_dict(data)

    def get_all_analyses(self) -> List[AnalysisResult]:
        """Get all stored analysis results."""
        results: List[AnalysisResult] = []
        if not os.path.isdir(self._analysis_dir):
            return results
        for fn in sorted(os.listdir(self._analysis_dir)):
            if fn.endswith(".json"):
                try:
                    result = self.get_analysis(fn.replace(".json", ""))
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.warning("Failed to load analysis %s: %s", fn, e)
        return results

    def total_analyzed(self) -> int:
        """Count papers that have been analyzed."""
        if not os.path.isdir(self._analysis_dir):
            return 0
        return len(
            [f for f in os.listdir(self._analysis_dir) if f.endswith(".json")]
        )

    # ----------------------------------------------------------------
    # Bulk operations
    # ----------------------------------------------------------------

    def unanalyzed_papers(self) -> List[Dict]:
        """Get all papers that haven't been analyzed yet."""
        all_papers = self.get_all_papers()
        analyzed_ids = {
            fn.replace(".json", "")
            for fn in os.listdir(self._analysis_dir)
            if fn.endswith(".json")
        }
        return [p for p in all_papers if p.get("arxiv_id", "") not in analyzed_ids]

    def get_metadata(self) -> CorpusStats:
        """Get corpus metadata/stats."""
        return CorpusStats(
            total_papers=self.total_papers(),
            total_analyzed=self.total_analyzed(),
            categories=self._count_categories(),
            created_at=datetime.now().isoformat(),
        )

    def _count_categories(self) -> Dict[str, int]:
        """Count papers per category."""
        counts: Dict[str, int] = {}
        for paper in self.get_all_papers():
            cats = paper.get("categories", [])
            if isinstance(cats, list):
                for cat in cats:
                    counts[cat] = counts.get(cat, 0) + 1
            elif isinstance(cats, str):
                counts[cats] = counts.get(cats, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: -x[1]))
