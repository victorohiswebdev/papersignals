# PaperSignals — Build Plan (SSOT)

## Mission
Build an open-source writing quality analyzer that scores documents on signals Turnitin's AI detector reads — perplexity, burstiness, transition density, lexical diversity, structural uniformity — providing actionable feedback without requiring a detection database.

## Repo
- **Owner:** victorohiswebdev
- **Name:** papersignals
- **Visibility:** Public
- **License:** MIT

## Directory Structure

```
papersignals/
├── README.md                  # Project overview, badges, quick start
├── LICENSE                    # MIT
├── .gitignore                 # Python + OS + IDE
├── pyproject.toml             # Build config (setuptools)
├── Makefile                   # Common commands
├── PLAN.md                    # This document
├── docs/
│   ├── RESEARCH.md            # Full research: Turnitin, AI detection, plagiarism
│   ├── ARCHITECTURE.md        # System design, module map, data flow
│   ├── SIGNALS_REFERENCE.md   # Deep reference on each of the 7 signals
│   └── PLAYBOOK.md            # Actionable writing playbook for FYP/students
├── papersignals/
│   ├── __init__.py
│   ├── cli.py                 # CLI entry point (argparse)
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── burstiness.py      # Sentence length variance → burstiness score
│   │   ├── transitions.py     # Transition word density & entropy
│   │   ├── lexical_diversity.py # Type-token ratio, hapax richness
│   │   ├── vocabulary.py      # AI-favored word fingerprint
│   │   ├── paragraph_uniformity.py # Paragraph length consistency
│   │   ├── readability.py     # Flesch-Kincaid, Gunning Fog, SMOG
│   │   ├── perplexity.py      # Character/word n-gram surprisal
│   │   └── structural.py      # Structural consistency across sections
│   ├── core/
│   │   ├── __init__.py
│   │   ├── document.py        # .txt/.docx parsing + sentence segmentation
│   │   ├── scoring.py         # Normalize, weight, composite score
│   │   └── report.py          # JSON/Markdown report generation
│   ├── corpus/
│   │   ├── __init__.py
│   │   ├── norms.py           # Baseline distributions from corpus analysis
│   │   └── arxiv_fetcher.py   # arXiv API client for corpus building
│   └── utils/
│       ├── __init__.py
│       ├── text_utils.py      # Sentence splitting, word tokenization
│       └── wordlists.py       # Transition words, AI words, hedging lexicon
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures
│   ├── test_burstiness.py
│   ├── test_transitions.py
│   ├── test_lexical_diversity.py
│   ├── test_vocabulary.py
│   ├── test_paragraph_uniformity.py
│   ├── test_readability.py
│   ├── test_scoring.py
│   └── fixtures/
│       ├── human_sample.txt   # Known human-written academic text
│       ├── ai_sample.txt      # Known AI-generated academic text
│       └── mixed_sample.txt   # Hybrid (base for regression testing)
├── data/
│   ├── wordlists/
│   │   ├── transition_words.txt
│   │   ├── ai_favored_words.txt
│   │   └── hedging_words.txt
│   └── corpus/
│       └── .gitkeep
└── examples/
    └── example_usage.py
```

## Implementation Phases

### Phase 1 — Foundation (this session)
- [x] GitHub auth verified
- [x] Repo name confirmed (papersignals)
- [ ] Create directory structure
- [ ] Create GitHub repo + connect
- [ ] Write .gitignore, LICENSE, pyproject.toml
- [ ] Write RESEARCH.md (comprehensive research findings)
- [ ] Write SIGNALS_REFERENCE.md
- [ ] Write PLAYBOOK.md
- [ ] Write README.md (comprehensive)
- [ ] Write all analysis modules (7 analyzers)
- [ ] Write core engine (document parsing, scoring, report)
- [ ] Write wordlists
- [ ] Write test fixtures + unit tests
- [ ] Push to GitHub

### Phase 2 — Corpus Calibration (future)
- [ ] ArXiv fetcher + baseline norm computation
- [ ] RF classifier on engineered features
- [ ] Integration tests against real papers

### Phase 3 — Dashboard (future)
- [ ] FastAPI backend
- [ ] Next.js frontend
- [ ] Deploy demo instance

## Technical Decisions

**No ML deps initially.** Pure Python stdlib + NLTK for sentence tokenization. Keeps install lightweight and deps minimal.

**Sentence segmentation:** Use `pypdf` + `python-docx` for file parsing. NLTK's `sent_tokenize` for sentence splitting. Pure Python otherwise.

**Scoring model:** Each analyzer returns a raw metric → normalized to 0-100 using percentile-based thresholds from established linguistics research. Composite score is a weighted average.

**Weighting (initial):**
- Burstiness: 25%
- Transition density: 15%
- Lexical diversity: 20%
- Vocabulary fingerprint: 15%
- Paragraph uniformity: 10%
- Readability: 10%
- Perplexity estimate: 5%

## Signal Reference Sources
Research drawn from: Turnitin whitepapers (AIW-1, AIW-2, AIR-1), Liang et al. 2023 (Stanford), Perkins et al. 2024, Goulart et al. 2024, Herbold et al. 2023, Weber-Wulff et al. 2023, IEEE/ACM studies on AI text detection.

## CLI API (target)
```
papersignals analyze paper.docx
papersignals analyze paper.txt --json
papersignals analyze paper.md --detailed
papersignals corpus update          # Refresh arxiv baselines
papersignals corpus stats           # Show current baseline norms
```
