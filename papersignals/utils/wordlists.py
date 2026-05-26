"""Word list management for papersignals."""

import os
from typing import List, Optional

# Default transition words used as fallback
_DEFAULT_TRANSITION_WORDS: List[str] = [
    "however", "therefore", "furthermore", "moreover", "consequently",
    "nevertheless", "nonetheless", "meanwhile", "subsequently", "thus",
    "hence", "accordingly", "additionally", "also", "although",
    "besides", "certainly", "conversely", "elsewhere", "equally",
    "eventually", "finally", "first", "firstly", "further",
    "last", "lastly", "likewise", "namely", "next",
    "notably", "otherwise", "particularly", "presently", "previously",
    "rather", "regardless", "second", "secondly", "similarly",
    "simultaneously", "since", "so", "still", "then",
    "thereafter", "thereby", "therefore", "third", "thirdly",
    "thus", "undoubtedly", "unlike", "until", "whereas",
    "while", "alternatively", "because", "despite", "due to",
    "in addition", "in conclusion", "in contrast", "in summary",
    "on the contrary", "on the other hand", "specifically", "ultimately",
    "as a result", "for example", "for instance", "in particular",
]

# Default AI-favored words used as fallback
_DEFAULT_AI_FAVORED_WORDS: List[str] = [
    "delve", "explore", "examine", "investigate", "uncover",
    "reveal", "illuminate", "elucidate", "demystify", "unpack",
    "navigate", "traverse", "leverage", "utilize", "optimize",
    "streamline", "facilitate", "bolster", "amplify", "augment",
    "enhance", "elevate", "enrich", "robust", "comprehensive",
    "holistic", "systematic", "transformative", "paradigm", "landscape",
    "ecosystem", "realm", "domain", "intersection", "convergence",
    "synergy", "scalable", "actionable", "impactful", "meaningful",
    "pivotal", "crucial", "vital", "essential", "fundamental",
    "notably", "significantly", "substantially", "fostering",
    "groundbreaking", "cutting-edge", "state-of-the-art", "novel",
    "innovative", "disruptive", "unprecedented", "invaluable",
    "indispensable", "imperative", "paramount", "multifaceted",
    "nuanced", "intricate", "sophisticated", "bespoke",
    "evidence-based", "data-driven", "insight-driven",
    "stakeholder", "cross-functional", "interdisciplinary",
    "interconnected", "interplay", "scaffolding", "framework",
    "roadmap", "blueprint", "cornerstone", "bedrock",
    "hallmark", "tapestry", "fabric", "pipeline",
    "workflow", "lifecycle", "trajectory", "momentum",
]

# Default hedging words used as fallback
_DEFAULT_HEDGING_WORDS: List[str] = [
    "might", "maybe", "perhaps", "possibly", "probably",
    "likely", "unlikely", "potentially", "arguably", "seemingly",
    "apparently", "ostensibly", "presumably", "reportedly", "allegedly",
    "suggests", "indicates", "implies", "appears", "seems",
    "tends", "could", "would", "may", "should",
    "somewhat", "rather", "quite", "fairly", "relatively",
    "comparatively", "moderately", "slightly", "some",
    "generally", "overall", "broadly", "largely", "mostly",
    "mainly", "chiefly", "predominantly", "often", "frequently",
    "sometimes", "occasionally", "rarely", "seldom",
    "nearly", "almost", "virtually", "essentially", "basically",
    "fundamentally", "roughly", "approximately", "about",
    "partially", "partly",
]


def _get_data_dir() -> str:
    """Get the path to the data/wordlists directory.

    Returns:
        Absolute path to the wordlists directory.
    """
    # Resolve relative to this file's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up two levels: papersignals/utils/ -> papersignals/
    project_dir = os.path.dirname(script_dir)
    return os.path.join(project_dir, "data", "wordlists")


def _load_wordlist(filename: str, default_words: List[str]) -> List[str]:
    """Load a wordlist from file, falling back to defaults.

    Args:
        filename: Name of the wordlist file in data/wordlists/.
        default_words: Default list to use if file not found.

    Returns:
        List of word/phrase strings.
    """
    filepath = os.path.join(_get_data_dir(), filename)
    if os.path.isfile(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                words = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            if words:
                return words
        except (OSError, IOError):
            pass
    return list(default_words)


def load_transition_words() -> List[str]:
    """Load transition words list.

    Tries to load from data/wordlists/transition_words.txt first.
    Falls back to built-in default list.

    Returns:
        List of transition words/phrases.
    """
    return _load_wordlist("transition_words.txt", _DEFAULT_TRANSITION_WORDS)


def load_ai_favored_words() -> List[str]:
    """Load AI-favored words list.

    Tries to load from data/wordlists/ai_favored_words.txt first.
    Falls back to built-in default list.

    Returns:
        List of AI-favored words/phrases.
    """
    return _load_wordlist("ai_favored_words.txt", _DEFAULT_AI_FAVORED_WORDS)


def load_hedging_words() -> List[str]:
    """Load hedging words list.

    Tries to load from data/wordlists/hedging_words.txt first.
    Falls back to built-in default list.

    Returns:
        List of hedging words/phrases.
    """
    return _load_wordlist("hedging_words.txt", _DEFAULT_HEDGING_WORDS)
