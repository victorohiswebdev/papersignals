"""The arxiv_fetcher for papersignals Phase 2.

Fetches academic papers from the arXiv API across configurable
subject categories, respects rate limits, and returns structured
paper data for corpus analysis.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional

import arxiv

logger = logging.getLogger(__name__)


# arXiv API rate limit: 1 request per 3 seconds per arXiv terms of use
ARXIV_RATE_LIMIT_SECONDS = 3.5

# Maximum results per API call (arXiv max per page)
MAX_PER_PAGE = 100

# Default categories to fetch
DEFAULT_CATEGORIES: List[str] = [
    "cs.AI",       # Artificial Intelligence
    "cs.CL",       # Computation and Language
    "cs.LG",       # Machine Learning
    "cs.IR",       # Information Retrieval
    "cs.CY",       # Computers and Society
    "cs.HC",       # Human-Computer Interaction
    "stat.ML",     # Machine Learning (Statistics)
    "stat.AP",     # Applications (Statistics)
    "eess.AS",     # Audio and Speech Processing
    "eess.IV",     # Image and Video Processing
]

# Target: at least 500 papers total across categories
DEFAULT_TARGET_PER_CATEGORY = 60


@dataclass
class PaperRecord:
    """Structured record for a single arXiv paper."""

    arxiv_id: str
    title: str
    abstract: str
    categories: List[str]
    published: str  # ISO date string
    updated: str  # ISO date string
    authors: List[str] = field(default_factory=list)
    pdf_url: str = ""
    comment: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_arxiv_result(cls, result: arxiv.Result) -> "PaperRecord":
        """Convert an arxiv API Result to a PaperRecord."""
        return cls(
            arxiv_id=result.entry_id.split("/")[-1].split("v")[0],
            title=result.title,
            abstract=result.summary,
            categories=[c for c in (result.categories or [])],
            published=result.published.isoformat() if result.published else "",
            updated=result.updated.isoformat() if result.updated else "",
            authors=[a.name for a in (result.authors or [])],
            pdf_url=result.pdf_url or "",
            comment=result.comment or "",
        )


class ArxivFetcher:
    """Fetch papers from the arXiv API with rate limiting and caching.

    Args:
        cache_dir: Directory to store fetched paper JSON files.
            Defaults to ~/.papersignals/corpus/arxiv/.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.papersignals/corpus/arxiv")
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

        self._client = arxiv.Client(
            page_size=MAX_PER_PAGE,
            delay_seconds=ARXIV_RATE_LIMIT_SECONDS,
            num_retries=5,
        )

    def fetch_category(
        self,
        category: str,
        max_results: int = DEFAULT_TARGET_PER_CATEGORY,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.SubmittedDate,
        force_refetch: bool = False,
    ) -> List[PaperRecord]:
        """Fetch papers from a specific arXiv category.

        Args:
            category: arXiv category code (e.g. 'cs.AI').
            max_results: Maximum number of papers to fetch.
            sort_by: Sort criterion for results.
            force_refetch: If True, re-fetch even if cached.

        Returns:
            List of PaperRecord objects.
        """
        # Check cache first
        cached = self._load_cache(category)
        if cached and not force_refetch:
            logger.info(
                "Using cached %d papers for %s", len(cached), category
            )
            return cached[:max_results]

        logger.info(
            "Fetching up to %d papers from arXiv %s ...",
            max_results,
            category,
        )

        search = arxiv.Search(
            query=f"cat:{category}",
            max_results=max_results,
            sort_by=sort_by,
        )

        results: List[PaperRecord] = []
        try:
            for result in self._client.results(search):
                record = PaperRecord.from_arxiv_result(result)
                results.append(record)
        except Exception as e:
            logger.error("Error fetching %s: %s", category, e)
            # Return whatever we got
            if not results:
                raise

        logger.info("Fetched %d papers from %s", len(results), category)
        self._save_cache(category, results)
        return results

    def fetch_multiple_categories(
        self,
        categories: Optional[List[str]] = None,
        per_category: int = DEFAULT_TARGET_PER_CATEGORY,
        force_refetch: bool = False,
    ) -> Dict[str, List[PaperRecord]]:
        """Fetch papers from multiple arXiv categories.

        Args:
            categories: List of category codes. Uses DEFAULT_CATEGORIES if None.
            per_category: Max papers per category.
            force_refetch: If True, re-fetch cached categories.

        Returns:
            Dict mapping category codes to lists of PaperRecord.
        """
        if categories is None:
            categories = DEFAULT_CATEGORIES

        all_papers: Dict[str, List[PaperRecord]] = {}

        for cat in categories:
            try:
                papers = self.fetch_category(
                    category=cat,
                    max_results=per_category,
                    force_refetch=force_refetch,
                )
                all_papers[cat] = papers
            except Exception as e:
                logger.warning("Skipping category %s: %s", cat, e)
                all_papers[cat] = []

        return all_papers

    def fetch_recent(
        self,
        category: str = "cs.AI",
        days: int = 30,
        max_results: int = 100,
    ) -> List[PaperRecord]:
        """Fetch recently submitted papers from a category.

        Args:
            category: arXiv category code.
            days: Number of days of recent papers to fetch.
            max_results: Maximum number of results.

        Returns:
            List of PaperRecord objects.
        """
        from datetime import timedelta, timezone

        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
            "%Y%m%d"
        )

        search = arxiv.Search(
            query=f"cat:{category} AND submittedDate:[{cutoff}0000 TO {cutoff}2359]",
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )

        results: List[PaperRecord] = []
        try:
            for result in self._client.results(search):
                record = PaperRecord.from_arxiv_result(result)
                results.append(record)
        except Exception as e:
            logger.error("Error fetching recent %s: %s", category, e)

        logger.info("Fetched %d recent papers from %s", len(results), category)
        return results

    # ----------------------------------------------------------------
    # Cache helpers
    # ----------------------------------------------------------------

    def _cache_path(self, category: str) -> str:
        safe = category.replace(".", "_").replace("/", "_")
        return os.path.join(self.cache_dir, f"{safe}.json")

    def _save_cache(self, category: str, papers: List[PaperRecord]) -> None:
        path = self._cache_path(category)
        data = [p.to_dict() for p in papers]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.debug("Cached %d papers to %s", len(papers), path)

    def _load_cache(self, category: str) -> List[PaperRecord]:
        path = self._cache_path(category)
        if not os.path.isfile(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [PaperRecord(**item) for item in data]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("Failed to load cache %s: %s", path, e)
            return []

    def get_cached_categories(self) -> List[str]:
        """List categories that have cached data."""
        if not os.path.isdir(self.cache_dir):
            return []
        files = [f for f in os.listdir(self.cache_dir) if f.endswith(".json")]
        return [f.replace(".json", "").replace("_", ".") for f in sorted(files)]

    def total_cached_papers(self) -> int:
        """Count total cached papers across all categories."""
        total = 0
        for cat in self.get_cached_categories():
            papers = self._load_cache(cat)
            total += len(papers)
        return total
