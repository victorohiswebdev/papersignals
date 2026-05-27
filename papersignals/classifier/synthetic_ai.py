"""Synthetic AI text generator for papersignals Phase 2.

Generates AI-typical versions of real academic text by applying
transformations that mirror known patterns of LLM-generated writing.
This produces paired training data for the Random Forest classifier.

Each transformation targets one of the 7 signals:
  - Sentence length uniformity (reduces burstiness)
  - Increased transition word density
  - Reduced lexical diversity
  - AI-favored vocabulary injection
  - Paragraph length uniformity
  - Narrowed readability range
  - Lowered perplexity (n-gram predictability)
"""

from __future__ import annotations

import logging
import random
import re
from typing import Dict, List, Optional

from papersignals.utils.wordlists import (
    load_transition_words,
    load_ai_favored_words,
)

logger = logging.getLogger(__name__)

# Probability of applying each transformation
TRANSFORM_PROB = 0.7


class SyntheticAIGenerator:
    """Generate synthetic AI-typical text from human-written text.

    Applies a configurable set of transformations to create text
    with the statistical fingerprints of LLM-generated writing.

    Args:
        seed: Random seed for reproducibility.
        transform_prob: Base probability of applying each transformation.
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        transform_prob: float = TRANSFORM_PROB,
    ):
        self.rng = random.Random(seed)
        self.transform_prob = transform_prob

    def generate(self, text: str) -> str:
        """Convert human-written text to AI-typical text.

        Applies multiple transformations in sequence to produce text
        with AI-like statistical patterns.

        Args:
            text: Original human-written text.

        Returns:
            Transformed text with AI-typical patterns.
        """
        if not text or len(text.strip()) < 50:
            return text

        result = text

        # Apply transformations in order
        if self.rng.random() < self.transform_prob:
            result = self._uniformize_sentence_length(result)

        if self.rng.random() < self.transform_prob:
            result = self._add_transition_words(result)

        if self.rng.random() < self.transform_prob:
            result = self._reduce_lexical_diversity(result)

        if self.rng.random() < self.transform_prob:
            result = self._inject_ai_vocabulary(result)

        if self.rng.random() < self.transform_prob:
            result = self._uniformize_paragraphs(result)

        if self.rng.random() < self.transform_prob:
            result = self._narrow_readability(result)

        return result

    def generate_batch(
        self,
        texts: List[str],
        progress_callback=None,
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
    # Individual transformations
    # ----------------------------------------------------------------

    def _uniformize_sentence_length(self, text: str) -> str:
        """Reduce sentence length variance (lowers burstiness).

        Splits long sentences and joins short ones to push all
        sentences toward a 15-25 word target range.
        """
        sentences = self._split_sentences(text)
        if len(sentences) < 3:
            return text

        result: List[str] = []
        buffer: List[str] = []

        target_min = 14
        target_max = 26

        for sent in sentences:
            words = sent.split()
            word_count = len(words)

            if word_count > target_max:
                # Split long sentence at conjunction or comma
                split_point = self._find_split_point(words, target_min, target_max)
                if split_point > 0:
                    result.append(" ".join(words[:split_point]) + ".")
                    remaining = words[split_point:]
                    if remaining:
                        # Capitalize first word
                        remaining[0] = remaining[0][0].upper() + remaining[0][1:]
                        result.append(" ".join(remaining) + ".")
                else:
                    result.append(sent)
            elif word_count < target_min and buffer:
                # Merge with previous short sentence
                buffer_sentences = " ".join(buffer)
                buffer_words = buffer_sentences.split()
                combined = buffer_words + words
                if len(combined) <= target_max:
                    buffer = [sent]
                    result[-1] = " ".join(combined) + "."
                else:
                    result.append(sent)
            else:
                result.append(sent)

        # Flush buffer
        if buffer:
            result.extend(buffer)

        return " ".join(result)

    def _find_split_point(
        self, words: List[str], min_len: int, max_len: int
    ) -> int:
        """Find a good position to split a long sentence.

        Prefers splitting at commas, semicolons, or conjunctions.
        """
        conjunctions = {"and", "or", "but", "however", "therefore", "thus", "while", "whereas", "although", "since", "because"}

        # Try comma positions first
        for i in range(min_len, min(max_len, len(words) - 1)):
            if words[i].endswith(",") or words[i] == ",":
                return i + 1 if not words[i].endswith(",") else i + 1

        # Try conjunction positions
        for i in range(min_len, min(max_len, len(words) - 1)):
            if words[i].lower() in conjunctions:
                return i

        # Fall back to midpoint
        mid = len(words) // 2
        if min_len <= mid <= max_len:
            return mid

        return 0

    def _add_transition_words(self, text: str) -> str:
        """Increase transition word density (raises AI signal).

        Inserts transition words at sentence beginnings and within
        sentences at a controlled rate.
        """
        sentences = self._split_sentences(text)
        if len(sentences) < 3:
            return text

        # Flatten transition categories into a single list
        all_transitions = load_transition_words()

        if not all_transitions:
            # Fallback transitions
            all_transitions = [
                "Furthermore", "Moreover", "Additionally",
                "However", "Nevertheless", "Consequently",
                "Therefore", "Thus", "Specifically",
                "In particular", "Notably", "Importantly",
                "Furthermore", "Moreover", "Additionally",
            ]

        result: List[str] = []
        insertion_rate = 0.3  # 30% of sentences get a transition

        for i, sent in enumerate(sentences):
            if i == 0:
                # Don't add transitions to first sentence
                result.append(sent)
                continue

            if self.rng.random() < insertion_rate:
                transition = self.rng.choice(all_transitions)
                # Capitalize properly
                if not transition[0].isupper():
                    transition = transition[0].upper() + transition[1:]

                if self.rng.random() < 0.6:
                    # Add at beginning
                    result.append(f"{transition}, {sent[0].lower() if sent else ''}{sent[1:]}")
                else:
                    # Add mid-sentence
                    words = sent.split()
                    if len(words) > 8:
                        pos = len(words) // 3
                        transition_lower = transition[0].lower() + transition[1:]
                        words.insert(pos, f"{transition_lower},")
                        result.append(" ".join(words))
                    else:
                        result.append(sent)
            else:
                result.append(sent)

        return " ".join(result)

    def _reduce_lexical_diversity(self, text: str) -> str:
        """Reduce vocabulary variety (lowers lexical diversity).

        Replaces less common words with more common synonyms.
        """
        # Common word replacement pairs: rare -> common
        replacements = {
            "demonstrates": "shows",
            "demonstrate": "show",
            "demonstrated": "showed",
            "exhibits": "has",
            "exhibit": "have",
            "exhibited": "had",
            "facilitates": "helps",
            "facilitate": "help",
            "facilitated": "helped",
            "elucidates": "explains",
            "elucidate": "explain",
            "elucidated": "explained",
            "delineates": "describes",
            "delineate": "describe",
            "delineated": "described",
            "implements": "uses",
            "implement": "use",
            "implemented": "used",
            "optimizes": "improves",
            "optimize": "improve",
            "optimized": "improved",
            "generates": "produces",
            "generate": "produce",
            "generated": "produced",
            "evaluates": "tests",
            "evaluate": "test",
            "evaluated": "tested",
            "assesses": "checks",
            "assess": "check",
            "assessed": "checked",
            "achieves": "gets",
            "achieve": "get",
            "achieved": "got",
            "acquires": "gets",
            "acquire": "get",
            "acquired": "got",
            "identifies": "finds",
            "identify": "find",
            "identified": "found",
            "constructs": "builds",
            "construct": "build",
            "constructed": "built",
            "computes": "calculates",
            "compute": "calculate",
            "computed": "calculated",
        }

        result_parts: List[str] = []
        for sent in self._split_sentences(text):
            words = sent.split()
            replaced = []
            for w in words:
                clean = w.strip(".,;:!?()\"'")
                punct = w[len(clean):] if len(clean) < len(w) else ""
                lower = clean.lower()
                if lower in replacements and self.rng.random() < 0.5:
                    new_word = replacements[lower]
                    # Preserve capitalization
                    if clean[0].isupper():
                        new_word = new_word[0].upper() + new_word[1:]
                    replaced.append(new_word + punct)
                else:
                    replaced.append(w)
            result_parts.append(" ".join(replaced))

        return " ".join(result_parts)

    def _inject_ai_vocabulary(self, text: str) -> str:
        """Inject AI-favored words (raises vocabulary fingerprint).

        Replaces neutral phrases with words from the AI-favored lexicon.
        """
        # Flatten AI-favored words
        all_ai_words = load_ai_favored_words()

        if not all_ai_words:
            all_ai_words = [
                "delve", "tapestry", "testament", "navigate", "realm",
                "multifaceted", "nuanced", "leverage", "pivotal", "robust",
                "comprehensive", "synthesize", "intricate", "paradigm",
                "foster", "holistic", "underscore", "dynamic", "facilitate",
                "revolutionize", "cutting-edge", "landscape", "ultimately",
                "essential", "significant", "moreover", "furthermore",
            ]

        # Replacement patterns: neutral_phrase -> AI phrase
        phrase_replacements = {
            "is important": "is pivotal",
            "very important": "crucial",
            "a lot of": "a significant number of",
            "many different": "a diverse range of",
            "look at": "examine",
            "looks at": "examines",
            "looked at": "examined",
            "more complex": "more intricate",
            "different aspects": "multifaceted dimensions",
            "big picture": "holistic landscape",
            "new way": "novel paradigm",
            "in many ways": "across multiple dimensions",
        }

        result = text
        # Apply phrase replacements
        for neutral, ai_phrase in phrase_replacements.items():
            if neutral.lower() in result.lower() and self.rng.random() < 0.4:
                # Case-insensitive replacement
                pattern = re.compile(re.escape(neutral), re.IGNORECASE)
                result = pattern.sub(ai_phrase, result)

        # Inject individual AI words
        sentences = self._split_sentences(result)
        injection_rate = 0.15  # 15% of sentences get an AI word
        result_sents: List[str] = []

        for sent in sentences:
            if self.rng.random() < injection_rate:
                ai_word = self.rng.choice(all_ai_words)
                words = sent.split()
                if len(words) > 6:
                    pos = self.rng.randint(2, len(words) - 3)
                    words.insert(pos, ai_word)
                    result_sents.append(" ".join(words))
                else:
                    result_sents.append(sent)
            else:
                result_sents.append(sent)

        return " ".join(result_sents)

    def _uniformize_paragraphs(self, text: str) -> str:
        """Make paragraph lengths more uniform (raises AI signal).

        Splits or merges paragraphs to reduce variance.
        """
        paragraphs = text.split("\n\n")
        if len(paragraphs) < 2:
            return text

        target_words = 75  # Target words per paragraph

        result: List[str] = []
        buffer: List[str] = []
        buffer_words = 0

        for para in paragraphs:
            words = len(para.split())

            if words > target_words * 1.5:
                # Split into smaller chunks
                sentences = self._split_sentences(para)
                chunk: List[str] = []
                chunk_words = 0
                for sent in sentences:
                    sw = len(sent.split())
                    if chunk_words + sw > target_words and chunk:
                        result.append(" ".join(chunk))
                        chunk = [sent]
                        chunk_words = sw
                    else:
                        chunk.append(sent)
                        chunk_words += sw
                if chunk:
                    result.append(" ".join(chunk))
            elif words < target_words * 0.5 and result:
                # Merge with previous paragraph
                prev = result[-1]
                combined = prev + " " + para
                if len(combined.split()) <= target_words * 1.2:
                    result[-1] = combined
                else:
                    result.append(para)
            else:
                result.append(para)

        return "\n\n".join(result)

    def _narrow_readability(self, text: str) -> str:
        """Narrow readability range to AI-typical levels.

        Replaces complex multi-syllable words with simpler alternatives
        and simplifies sentence structure.
        """
        replacements = {
            "implementation": "use",
            "implementation of": "using",
            "methodology": "method",
            "methodologies": "methods",
            "architecture": "design",
            "architectures": "designs",
            "utilization": "use",
            "utilize": "use",
            "utilizes": "uses",
            "utilized": "used",
            "optimization": "improvement",
            "optimizations": "improvements",
            "characterization": "description",
            "characteristics": "features",
            "configuration": "setup",
            "configurations": "setups",
            "representation": "representation",
            "representations": "representations",
        }

        result = text
        for complex_w, simple_w in replacements.items():
            if self.rng.random() < 0.3:
                pattern = re.compile(r"\b" + re.escape(complex_w) + r"\b", re.IGNORECASE)
                result = pattern.sub(simple_w, result)

        return result

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Simple sentence splitting that preserves punctuation.

        Falls back to regex-based splitting if NLTK not available.
        """
        try:
            from nltk.tokenize import sent_tokenize
            return sent_tokenize(text)
        except (ImportError, LookupError):
            # Simple regex fallback
            sentences = re.split(r'(?<=[.!?])\s+', text)
            return [s.strip() for s in sentences if s.strip()]

