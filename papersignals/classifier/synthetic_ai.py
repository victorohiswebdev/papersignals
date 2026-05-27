"""Synthetic AI text generator for papersignals Phase 2 — v2.

Generates AI-typical versions of real academic text. Uses a multi-pass
approach (default 3 passes) focused on the features that most
distinguish the RF classifier's decision boundary.

Key targets (weighted by RF feature importance):
  - Readability FK/Fog: push into narrow 14-18 FK range
  - Transition density: 4-8 per 100 words
  - Vocab fingerprint: 1-3 AI-favored words per document
  - Burstiness: target 70% of sentences in 15-28 word range
"""

from __future__ import annotations

import logging
import random
import re
from typing import Callable, Dict, List, Optional

from papersignals.utils.wordlists import (
    load_transition_words,
    load_ai_favored_words,
)

logger = logging.getLogger(__name__)

TRANSFORM_PROB = 0.9
DEFAULT_PASSES = 3


class SyntheticAIGenerator:
    """Generate synthetic AI-typical text from human-written text.

    v2 — uses pattern templates and targeted transformations to
    produce text that closely mirrors the statistical fingerprints
    of real LLM-generated academic writing.

    Args:
        seed: Random seed for reproducibility.
        transform_prob: Base transform probability.
    """

    # LLM-typical sentence template patterns. Each is a list of
    # (prefix, insertion_point) pairs where insertion_point
    # is the index into the tokenized sentence.
    LLM_SENTENCE_PATTERNS = [
        # Introductory / framing patterns
        "It is worth noting that {}",
        "Importantly, {}",
        "Notably, {}",
        "Interestingly, {}",
        "As expected, {}",
        "In particular, {}",
        "Specifically, {}",
        "More broadly, {}",
        "Crucially, {}",
        "In practice, {}",
        # Result / finding patterns
        "Our results demonstrate that {}",
        "These findings suggest that {}",
        "This indicates that {}",
        "Taken together, these results suggest that {}",
        "This underscores the importance of {}",
        "This highlights the role of {}",
        "This is consistent with prior work showing that {}",
        # Reasoning / explanation patterns
        "This can be attributed to {}",
        "One explanation for this is {}",
        "This is likely because {}",
        "This may be due to {}",
    ]

    # AI-typical hedging/qualifier phrases (overused by LLMs)
    HEDGING_PATTERNS = [
        "to some extent",
        "to a certain degree",
        "in many cases",
        "in most instances",
        "as it were",
        "so to speak",
        "broadly speaking",
        "generally speaking",
        "in a sense",
        "to a large extent",
    ]

    # AI-typical self-referential structures (LLMs love these)
    FRAMING_EXPRESSIONS = [
        "It is important to note that",
        "It should be emphasized that",
        "It is worth highlighting that",
        "It is crucial to consider that",
        "It is essential to recognize that",
        "It is also worth mentioning that",
    ]

    def __init__(
        self,
        seed: Optional[int] = None,
        transform_prob: float = TRANSFORM_PROB,
        num_passes: int = DEFAULT_PASSES,
    ):
        self.rng = random.Random(seed)
        self.transform_prob = transform_prob
        self.num_passes = num_passes
        self._transitions = load_transition_words() or self._default_transitions()
        self._ai_words = load_ai_favored_words() or self._default_ai_words()

    def generate(self, text: str) -> str:
        """Convert human-written text to AI-typical text.

        Applies a multi-pass (default 3) transformation pipeline that
        progressively pushes text toward AI statistical profiles.

        Each pass applies all 6 stages in sequence:
          1. LLM sentence patterns
          2. Hedging insertion
          3. AI vocabulary injection
          4. Transition word addition
          5. Length uniformization
          6. Vocabulary narrowing

        Args:
            text: Original human-written text.

        Returns:
            Transformed text with AI-typical statistical patterns.
        """
        if not text or len(text.strip()) < 50:
            return text

        result = text
        for _ in range(self.num_passes):
            result = self._apply_pass(result)

        return result

    def _apply_pass(self, text: str) -> str:
        """Apply one transformation pass."""
        result = text

        if self.rng.random() < self.transform_prob:
            result = self._apply_sentence_patterns(result)
        if self.rng.random() < self.transform_prob:
            result = self._add_hedging(result)
        if self.rng.random() < self.transform_prob:
            result = self._inject_ai_vocabulary_v2(result)
        if self.rng.random() < self.transform_prob:
            result = self._add_transition_words_v2(result)
        if self.rng.random() < self.transform_prob:
            result = self._uniformize_length(result)
        if self.rng.random() < self.transform_prob:
            result = self._narrow_vocabulary(result)

        return result

    def generate_batch(
        self,
        texts: List[str],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[str]:
        """Generate AI-typical versions of multiple texts.

        Args:
            texts: List of original texts.
            progress_callback: Optional callable(current, total).

        Returns:
            List of transformed texts.
        """
        results: List[str] = []
        for i, text in enumerate(texts):
            results.append(self.generate(text))
            if progress_callback:
                progress_callback(i + 1, len(texts))
        return results

    # ----------------------------------------------------------------
    # Stage 1: LLM sentence pattern templates
    # ----------------------------------------------------------------

    def _apply_sentence_patterns(self, text: str) -> str:
        """Rewrite sentences using LLM-typical patterns.

        Selects ~20% of sentences and replaces them with pattern-
        templated versions that mirror how LLMs write.
        """
        sentences = self._split_sentences(text)
        if len(sentences) < 4:
            return text

        result: List[str] = []
        for i, sent in enumerate(sentences):
            if i == 0:
                # Keep first sentence as-is (it's usually the paper title
                # restatement which is already dense)
                result.append(sent)
                continue

            words = sent.split()
            if len(words) < 6:
                result.append(sent)
                continue

            # 20% chance to template this sentence
            if self.rng.random() < 0.20:
                pattern = self.rng.choice(self.LLM_SENTENCE_PATTERNS)

                # Extract the core content (last ~70% of the sentence)
                core_start = max(0, len(words) - max(4, len(words) - 2))
                core = " ".join(words[core_start:])

                # Remove trailing punctuation from core if present
                core = core.rstrip(".,;:")

                # Insert core into template
                templated = pattern.format(core)

                # Clean up any double spaces or weird casing
                templated = templated[0].upper() + templated[1:] if templated else templated
                if not templated.endswith("."):
                    templated += "."
                result.append(templated)
            else:
                result.append(sent)

        return " ".join(result)

    # ----------------------------------------------------------------
    # Stage 2: Add hedging and qualification
    # ----------------------------------------------------------------

    def _add_hedging(self, text: str) -> str:
        """Insert hedging/qualifier phrases at natural positions.

        LLMs heavily overuse hedging—this makes the text sound
        more cautious and "comprehensive."
        """
        sentences = self._split_sentences(text)
        if len(sentences) < 3:
            return text

        result: List[str] = []
        for i, sent in enumerate(sentences):
            words = sent.split()
            if len(words) < 8:
                result.append(sent)
                continue

            # 25% chance to hedge this sentence
            if self.rng.random() < 0.25:
                hedge = self.rng.choice(self.HEDGING_PATTERNS)

                # Insert hedge at one of three positions:
                pos_type = self.rng.randint(0, 2)
                if pos_type == 0:
                    # After first 2-3 words
                    insert_at = min(3, len(words) - 2)
                    words.insert(insert_at, hedge + ",")
                elif pos_type == 1:
                    # Before the main verb phrase (~40% through)
                    insert_at = max(2, min(len(words) // 2 - 1, len(words) - 3))
                    words.insert(insert_at, hedge + ",")
                else:
                    # At end, as an appositive
                    words.insert(-1, hedge)

                result.append(" ".join(words))
            else:
                result.append(sent)

        return " ".join(result)

    # ----------------------------------------------------------------
    # Stage 3: AI vocabulary injection
    # ----------------------------------------------------------------

    def _inject_ai_vocabulary_v2(self, text: str) -> str:
        """Inject AI-favored vocabulary at natural positions.

        v2 improvement: replaces parts of existing phrases rather than
        randomly inserting AI words, producing more natural-sounding
        but AI-typical text.
        """
        # Tiered AI vocabulary with context substitutions
        phrase_subs: Dict[str, str] = {
            # Replacements that expand human phrases into AI style
            r"\b(show|shows|shown)\b": "demonstrate",
            r"\b(use|uses|used)\b": "utilize",
            r"\b(help|helps|helped)\b": "facilitate",
            r"\b(make|makes|made)\b": "facilitate",
            r"\b(improve|improves|improved)\b": "enhance",
            r"\b(big|large)\b": "significant",
            r"\b(many)\b": "numerous",
            r"\b(different)\b": "diverse",
            r"\b(important)\b": "crucial",
            r"\b(need|needs)\b": "require",
            r"\b(get|gets|got)\b": "achieve",
            r"\b(new)\b": "novel",
            r"\b(hard|difficult)\b": "challenging",
            r"\b(good)\b": "effective",
            r"\b(very)\b": "highly",
            r"\b(look|looks|looked)\b": "examine",
            r"\b(clear)\b": "evident",
            r"\b(givegives|gave)\b": "provide",
            r"\b(way|ways)\b": "approach",
            r"\b(idea|ideas)\b": "concept",
            r"\b(part|parts)\b": "component",
            r"\b(group|groups)\b": "category",
            r"\b(set|sets)\b": "configuration",
            r"\b(small)\b": "minor",
            r"\b(change|changes|changed)\b": "modify",
            r"\b(main)\b": "primary",
        }

        result = text
        for pattern, replacement in phrase_subs.items():
            if self.rng.random() < 0.3:  # 30% chance per pattern
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        # Also inject high-signal AI words — guarantee at least 1 per document
        ai_hits = 0
        target_ai_hits = max(1, min(3, len(text.split()) // 50))  # 1-3 per doc
        sentences = self._split_sentences(result)
        result_sents: List[str] = []
        for sent in sentences:
            words = sent.split()
            if len(words) > 8 and (self.rng.random() < 0.25 or ai_hits < target_ai_hits) and ai_hits < 5:
                ai_word = self.rng.choice(self._ai_words)
                insert_at = self.rng.randint(2, len(words) - 3)
                # Add comma after injected word for naturalness
                words.insert(insert_at, ai_word)
                result_sents.append(" ".join(words))
                ai_hits += 1
            else:
                result_sents.append(sent)

        return " ".join(result_sents)

    # ----------------------------------------------------------------
    # Stage 4: Strategic transition words
    # ----------------------------------------------------------------

    def _add_transition_words_v2(self, text: str) -> str:
        """Add transition words at strategic positions.

        v2: uses the transition words that turnitin actually flags
        (Furthermore, Moreover, Additionally, However, etc.)
        at a density of ~4-6 per 100 words.
        """
        sentences = self._split_sentences(text)
        if len(sentences) < 4:
            return text

        # Compute target density
        total_words = len(text.split())
        target_transitions = max(2, int(total_words * 0.04))  # 4 per 100 words

        # Categorize transitions
        additive = [
            w for w in self._transitions
            if w.lower() in ["furthermore", "moreover", "additionally", "also", "besides"]
        ] or ["Furthermore", "Moreover", "Additionally"]

        contrastive = [
            w for w in self._transitions
            if w.lower() in ["however", "nevertheless", "nonetheless", "conversely", "yet"]
        ] or ["However", "Nevertheless", "Conversely"]

        conclusive = [
            w for w in self._transitions
            if w.lower() in ["therefore", "consequently", "thus", "hence", "accordingly"]
        ] or ["Therefore", "Consequently", "Thus"]

        result: List[str] = []
        added = 0

        for i, sent in enumerate(sentences):
            if i == 0:
                result.append(sent)
                continue

            if added >= target_transitions:
                result.append(sent)
                continue

            # Determine transition type based on sentence position
            if i < len(sentences) * 0.4:
                pool = additive + contrastive
            elif i < len(sentences) * 0.8:
                pool = contrastive + conclusive
            else:
                pool = conclusive + additive

            if self.rng.random() < 0.35:
                transition = self.rng.choice(pool)
                # Capitalize
                transition_str = transition[0].upper() + transition[1:]
                # Insert at beginning with comma
                result.append(f"{transition_str}, {sent[0].lower() if sent else ''}{sent[1:]}")
                added += 1
            else:
                result.append(sent)

        return " ".join(result)

    # ----------------------------------------------------------------
    # Stage 5: Uniform sentence length
    # ----------------------------------------------------------------

    def _uniformize_length(self, text: str) -> str:
        """Push sentence lengths toward a narrow target range.

        LLM text typically has 70% of sentences in the 15-30 word range.
        Short sentences get expanded, long sentences get compressed.
        """
        sentences = self._split_sentences(text)
        if len(sentences) < 4:
            return text

        result: List[str] = []
        target = 22  # target words per sentence
        tolerance = 8  # acceptable range: 14-30

        for sent in sentences:
            words = sent.split()
            n = len(words)

            if n < 14:
                # Expand short sentence with a clause or hedge
                if self.rng.random() < 0.6:
                    expansions = [
                        f"In particular, {sent[0].lower() if sent else ''}{sent[1:]}",
                        f"More specifically, {sent[0].lower() if sent else ''}{sent[1:]}",
                        f"It is also worth noting that {sent[0].lower() if sent else ''}{sent[1:]}",
                    ]
                    result.append(self.rng.choice(expansions))
                else:
                    result.append(sent)
            elif n > 35:
                # Compress long sentence — strip a qualifying clause
                # Remove "which" / "that" clauses
                compressed = re.sub(
                    r",\s*(which|that)\s+[\w\s,;:]+?(?=,\s|\s+and|\s+or|\s+\.)",
                    "",
                    sent,
                    count=1,
                )
                if len(compressed.split()) > n * 0.7 and len(compressed.split()) <= 35:
                    result.append(compressed)
                else:
                    # Fall back to splitting at a conjunction
                    split_patterns = [r",\s+and\s+", r",\s+but\s+", r",\s+while\s+", r",\s+whereas\s+"]
                    split_found = False
                    for pat in split_patterns:
                        parts = re.split(pat, sent, maxsplit=1)
                        if len(parts) == 2:
                            first = parts[0] + "."
                            second = parts[1][0].upper() + parts[1][1:] if parts[1] else parts[1]
                            if not second.endswith("."):
                                second += "."
                            result.append(first)
                            result.append(second)
                            split_found = True
                            break
                    if not split_found:
                        result.append(sent)
            else:
                result.append(sent)

        return " ".join(result)

    # ----------------------------------------------------------------
    # Stage 6: Vocabulary narrowing
    # ----------------------------------------------------------------

    def _narrow_vocabulary(self, text: str) -> str:
        """Reduce lexical diversity by using common synonyms.

        Maps varied vocabulary to a smaller set of frequently-used
        words, mimicking the narrower vocabulary of LLMs.
        """
        narrowing: Dict[str, List[str]] = {
            r"\b(approach|method|technique|methodology)\b": ["approach", "method", "technique"],
            r"\b(result|finding|outcome|consequence)\b": ["result", "finding", "outcome"],
            r"\b(analyze|examine|investigate|study|explore)\b": ["analyze", "examine", "investigate"],
            r"\b(demonstrate|show|indicate|reveal|illustrate)\b": ["demonstrate", "show", "indicate"],
            r"\b(significant|substantial|considerable|notable)\b": ["significant", "substantial"],
            r"\b(enhance|improve|boost|strengthen)\b": ["enhance", "improve"],
            r"\b(implement|deploy|apply|employ)\b": ["implement", "apply"],
            r"\b(evaluate|assess|measure|quantify)\b": ["evaluate", "assess"],
            r"\b(comprehensive|thorough|extensive|exhaustive)\b": ["comprehensive", "extensive"],
            r"\b(various|diverse|multiple|several)\b": ["various", "multiple"],
            r"\b(develop|create|build|construct)\b": ["develop", "create"],
            r"\b(identify|detect|recognize|discern)\b": ["identify", "detect"],
        }

        result = text
        for pattern, alternatives in narrowing.items():
            if self.rng.random() < 0.35:
                def replace_with_alt(match: re.Match) -> str:
                    alt = self.rng.choice(alternatives)
                    # Preserve case
                    original = match.group(0)
                    if original[0].isupper():
                        return alt[0].upper() + alt[1:]
                    return alt
                result = re.sub(pattern, replace_with_alt, result, flags=re.IGNORECASE)

        return result

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        try:
            from nltk.tokenize import sent_tokenize
            return sent_tokenize(text)
        except (ImportError, LookupError):
            sentences = re.split(r'(?<=[.!?])\s+', text)
            return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def _default_transitions() -> List[str]:
        return [
            "furthermore", "moreover", "additionally", "however",
            "nevertheless", "consequently", "therefore", "thus",
            "specifically", "notably", "importantly", "conversely",
        ]

    @staticmethod
    def _default_ai_words() -> List[str]:
        return [
            "delve", "tapestry", "testament", "navigate", "realm",
            "multifaceted", "nuanced", "leverage", "pivotal", "robust",
            "comprehensive", "synthesize", "intricate", "paradigm",
            "foster", "holistic", "underscore", "dynamic", "facilitate",
            "revolutionize", "cutting-edge", "landscape", "ultimately",
            "essential", "significant", "moreover", "furthermore",
        ]
