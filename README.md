# PaperSignals

**Analyze your academic writing for signals that correlate with AI detection — and learn exactly what to fix.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](docs/CONTRIBUTING.md)

---

## What is PaperSignals?

PaperSignals is an open-source tool that scores your academic writing across **7 linguistic signals** — the same types of patterns that Turnitin's AI detector reads. **It does not try to replicate Turnitin's database** (that's impossible without access to their 200M+ document repository). Instead, it gives you a window into your writing's statistical fingerprint: where does it look human, and where does it look mechanical?

- **Burstiness** — Is your sentence length varied like human writing, or uniform like AI text?
- **Transition Density** — Are you overusing predictable transitions (Furthermore, Moreover, Additionally)?
- **Lexical Diversity** — Is your vocabulary rich enough?
- **Vocabulary Fingerprint** — Are you using words that AI over-produces (delve, leverage, robust)?
- **Paragraph Uniformity** — Are all your paragraphs the same length and structure?
- **Readability** — Does your text fall in the expected range for academic writing?
- **Perplexity (approx.)** — A rough estimate of how predictable your word choices are.

Each signal gets a **score from 0-100** (higher = more human-like), and you get a **composite score** plus specific, actionable recommendations.

---

## Quick Start

```bash
# Install
pip install git+https://github.com/victorohiswebdev/papersignals.git

# Or clone and install locally
git clone https://github.com/victorohiswebdev/papersignals.git
cd papersignals
pip install -e ".[dev]"
python -c "import nltk; nltk.download('punkt_tab', quiet=True)"

# Analyze a document
papersignals analyze paper.txt

# Detailed analysis with per-sentence breakdown
papersignals analyze chapter3.docx --detailed

# JSON output for programmatic use
papersignals analyze paper.md --json

# Save report to file
papersignals analyze thesis.docx --output report.md
```

---

## Why PaperSignals?

### The Problem
Turnitin and similar tools flag content based on statistical patterns, but they don't tell you *what* triggered the flag or *how* to fix it. Students submit blind, hoping for the best.

### The Solution
PaperSignals shows you the **individual signals** in your writing, scores each one, and provides **specific recommendations** to improve your score. Use it as a drafting companion, not a detection tool.

### What PaperSignals is NOT
- ❌ **Not a Turnitin replacement** — We don't have a database of 200M+ documents
- ❌ **Not an AI detector** — We score statistical patterns, not provenance
- ❌ **Not a plagiarism checker** — Use Turnitin or iThenticate for that
- ❌ **Not a grammar checker** — Use Grammarly or LanguageTool for that

### What it IS
- ✅ A **writing quality analyzer** that surfaces mechanical patterns
- ✅ A **learning tool** that teaches you what makes writing sound human
- ✅ A **pre-submission sanity check** before you upload to Turnitin
- ✅ **Completely private** — your documents never leave your machine
- ✅ **Free and open-source** — MIT license

---

## Project Structure

```
papersignals/
├── papersignals/          # Python package
│   ├── cli.py             # CLI entry point
│   ├── analyzers/         # 7 signal analyzers
│   │   ├── burstiness.py
│   │   ├── transitions.py
│   │   ├── lexical_diversity.py
│   │   ├── vocabulary.py
│   │   ├── paragraph_uniformity.py
│   │   ├── readability.py
│   │   └── perplexity.py
│   ├── core/              # Engine core
│   │   ├── document.py    # Document parsing & segmentation
│   │   ├── scoring.py     # Score normalization & compositing
│   │   └── report.py      # Report generation (markdown/JSON)
│   └── utils/             # Utilities & wordlists
│       ├── text_utils.py
│       └── wordlists.py
├── docs/                  # Documentation
│   ├── RESEARCH.md        # Full research on Turnitin & AI detection
│   ├── SIGNALS_REFERENCE.md  # Deep reference on each signal
│   ├── PLAYBOOK.md        # Actionable writing playbook
│   ├── ARCHITECTURE.md    # System architecture & future plans
│   └── CONTRIBUTING.md    # How to contribute
├── tests/                 # Test suite
├── data/                  # Wordlists & corpus data
└── examples/              # Usage examples
```

---

## Documentation

| Document | What it covers |
|---|---|
| [RESEARCH.md](docs/RESEARCH.md) | Comprehensive research: how Turnitin detects AI, the 7 signals, scientific studies, humanizer landscape |
| [SIGNALS_REFERENCE.md](docs/SIGNALS_REFERENCE.md) | Deep technical reference: formulas, thresholds, interpretation, improvement tips for each signal |
| [PLAYBOOK.md](docs/PLAYBOOK.md) | Actionable writing guide: how to write under 20% thresholds for both AI and similarity |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design: module map, data flow, scoring model, future roadmap |
| [PLAN.md](PLAN.md) | Build plan (SSOT): project roadmap, phases, technical decisions |

---

## Scoring Model

| Signal | Weight | AI-Typical | Human-Typical |
|---|---|---|---|
| Burstiness | 25% | SD 0.5–3 | SD 5–20 |
| Lexical Diversity | 20% | TTR 0.35–0.45 | TTR 0.50–0.70 |
| Vocabulary Fingerprint | 15% | >2/1000 words | <1/1000 words |
| Transition Density | 15% | >5/100 words | <2/100 words |
| Readability | 10% | — | FK 12–16, Fog 14–18 |
| Paragraph Uniformity | 10% | SD <25 words | SD >45 words |
| Perplexity (approx) | 5% | Low | High |

Composite score = weighted average of all 7 signals (0-100, higher = more human-like).

---

## Roadmap

- **Phase 1** ✅ — Core analysis engine (CLI, 7 analyzers, markdown/JSON reports)
- **Phase 2** 🔜 — ArXiv corpus baseline norms, RF classifier calibration
- **Phase 3** 🔜 — FastAPI backend + Next.js dashboard

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

---

## License

MIT — see [LICENSE](LICENSE).

Built by [Victor Ohis](https://github.com/victorohiswebdev) and [contributors](https://github.com/victorohiswebdev/papersignals/graphs/contributors).
