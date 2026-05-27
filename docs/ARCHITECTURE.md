# PaperSignals — Architecture Document

> **Purpose:** System architecture, module map, data flow, scoring model, CLI API reference, future roadmap, and key design decisions.

---

## 1. Overview

PaperSignals is an **open-source writing quality analyzer** that scores documents on the statistical signals Turnitin's AI detector reads. It provides:

- **Analysis of 7 signals** known to underpin AI-generated text detection
- **A composite Writing Authenticity Score** (0–100) with actionable breakdowns
- **Transparent, explainable output** — every metric is traceable to concrete text properties
- **No external ML dependencies** — pure Python, NLTK, and established formulas

### What PaperSignals Does

- Reads `.txt` and `.docx` files
- Splits text into sentences and paragraphs
- Computes burstiness, transition density, lexical diversity, vocabulary fingerprint, paragraph uniformity, readability, and approximate perplexity
- Normalizes raw metrics to 0–100 using percentile-based thresholds from linguistics research
- Outputs a composite score with per-signal breakdowns in JSON and/or Markdown

### What PaperSignals Does NOT Do

- **Does not access Turnitin's database** — no black-box comparison
- **Does not use LLMs or transformer models** — no GPT/bert dependencies
- **Does not guarantee detection accuracy** — it estimates the **statistical profile** of your text, not Turnitin's actual verdict
- **Does not store or transmit your documents** — all analysis is local
- **Does not detect plagiarism** — it analyzes writing style, not content similarity

---

## 2. Module Map (Phase 2 — Updated)

```
papersignals/
├── cli.py                      # Entry point: argparse CLI
├── core/
│   ├── document.py             # Document parsing + sentence segmentation
│   ├── scoring.py              # Normalization, weighting, composite + RF score
│   └── report.py               # JSON / Markdown report generation
├── analyzers/
│   ├── burstiness.py           # Sentence length variance → burstiness score
│   ├── transitions.py          # Transition word density & entropy
│   ├── lexical_diversity.py    # Type-token ratio, hapax richness, MATTR
│   ├── vocabulary.py           # AI-favored word fingerprint
│   ├── paragraph_uniformity.py # Paragraph length consistency
│   ├── readability.py          # Flesch-Kincaid, Gunning Fog, SMOG
│   └── perplexity.py           # Character/word n-gram surprisal
├── corpus/                     # Phase 2 — ArXiv corpus & baseline norms
│   ├── arxiv_fetcher.py        # arXiv API client with rate limiting & caching
│   ├── corpus_db.py            # Local JSON-based paper & analysis storage
│   ├── norms.py                # Percentile distribution computation
│   └── pipeline.py             # Orchestrator: fetch → analyze → norms
├── classifier/                 # Phase 2 — RF classifier
│   ├── features.py             # Feature extraction from analyzer results
│   ├── synthetic_ai.py         # Rule-based AI text generator for training data
│   └── train.py                # Training pipeline (CV + calibration)
├── utils/
│   ├── text_utils.py           # Sentence splitting, word tokenization
│   └── wordlists.py            # Transition words, AI words, hedging lexicon
└── data/
    └── wordlists/              # Flat text wordlist files
```

### Module Descriptions

**`cli.py`** — Argparse-based command-line interface. Routes `papersignals analyze` and `papersignals corpus` subcommands. Handles file discovery, output format flags (JSON, Markdown, detailed), and error reporting.

**`core/document.py`** — Document ingestion layer. Uses `python-docx` for `.docx` parsing and built-in `pathlib` for `.txt`. Strips non-prose content (tables, code blocks, references). Passes cleaned text to NLTK's `sent_tokenize` for sentence segmentation.

**`core/scoring.py`** — Takes raw metrics from all 7 analyzers, normalizes each to a 0–100 scale using percentile thresholds, applies the weighting matrix, and computes the composite Writing Authenticity Score.

**`core/report.py`** — Formats analysis results. Generates either a human-readable Markdown report with color-coded signal breakdowns or a machine-readable JSON structure.

**`analyzers/burstiness.py`** — Sentence word counts → standard deviation → burstiness score. Handles edge cases (single-sentence documents, very short texts).

**`analyzers/transitions.py`** — Tokenizes text → matches against transition wordlist → computes frequency per 100 words and Shannon entropy over the transition distribution.

**`analyzers/lexical_diversity.py`** — Tokenizes → computes TTR, MATTR (window=100), and hapax richness. MATTR is the primary metric; TTR is reported as context.

**`analyzers/vocabulary.py`** — Tokenizes → matches against AI-favored word lexicon → returns hit count, hit density (per 1000 words), and severity tier classification (red/orange/yellow).

**`analyzers/paragraph_uniformity.py`** — Paragraph boundary detection → word counts → CV (coefficient of variation) and SD.

**`analyzers/readability.py`** — Syllable counting (using a lookup + heuristic fallback) → FKGL, Gunning Fog, SMOG → computes paragraph-level readability SD.

**`analyzers/perplexity.py`** — Word trigram frequency table (within-document) → add-1 smoothed conditional probabilities → average surprisal → estimated perplexity. Document-level only; short-document guardrails.

**`corpus/norms.py`** — Stores baseline percentile distributions for each signal, derived from established linguistics research. Used by `scoring.py` for normalization. In Phase 2, these will be updated dynamically from ArXiv corpus analysis.

**`corpus/arxiv_fetcher.py`** — arXiv API client for building a reference corpus of human-written academic papers. Downloads abstracts and full texts in specified categories. Used for corpus calibration (Phase 2).

**`utils/text_utils.py`** — Reusable text processing utilities: sentence splitting (NLTK wrapper), word tokenization (NLTK wrapper), paragraph boundary detection, non-prose content filtering, syllable counting.

**`utils/wordlists.py`** — Static data: transition words categorized by type, AI-favored word lexicon with severity tiers, hedging words. Loaded by analyzers at runtime.

---

## 3. Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Input File  │────▶│  Document    │────▶│  Text Cleaning  │
│  (.txt/.docx)│     │  Parsing     │     │  (non-prose     │
└─────────────┘     └──────────────┘     │   stripping)    │
                                          └────────┬────────┘
                                                   │
                                          ┌────────▼────────┐
                                          │  Sentence &      │
                                          │  Paragraph Split │
                                          └────────┬────────┘
                                                   │
                    ┌──────────────────────────────┼──────────────────────────────┐
                    │                              │                              │
          ┌─────────▼─────────┐       ┌────────────▼──────────┐      ┌───────────▼───────────┐
          │  Analyzer Pipeline │       │  Analyzer Pipeline    │      │  Analyzer Pipeline     │
          │  (Per-Sentence)    │       │  (Per-Document)       │      │  (Per-Paragraph)       │
          │                    │       │                       │      │                        │
          │  • Burstiness      │       │  • Lexical Diversity  │      │  • Paragraph            │
          │  • Perplexity      │       │  • Vocabulary         │      │    Uniformity           │
          │                    │       │    Fingerprint        │      │  • Readability          │
          │                    │       │  • Transition Density │      │    (per-paragraph)      │
          │                    │       │                       │      │                        │
          └─────────┬─────────┘       └────────────┬──────────┘      └───────────┬───────────┘
                    │                              │                              │
                    └──────────────────────────────┼──────────────────────────────┘
                                                   │
                                          ┌────────▼────────┐
                                          │  Raw Metrics     │
                                          │  (7 signals)     │
                                          └────────┬────────┘
                                                   │
                                          ┌────────▼────────┐
                                          │  Normalization   │
                                          │  (0-100 per      │
                                          │   signal)        │
                                          └────────┬────────┘
                                                   │
                                          ┌────────▼────────┐
                                          │  Weighted        │
                                          │  Composite Score │
                                          └────────┬────────┘
                                                   │
                                          ┌────────▼────────┐
                                          │  Report          │
                                          │  Generator       │
                                          │  (MD / JSON)     │
                                          └────────┬────────┘
                                                   │
                                          ┌────────▼────────┐
                                          │  Output          │
                                          │  (stdout / file) │
                                          └─────────────────┘
```

### Step-by-Step

1. **File Input:** User provides a path to `.txt` or `.docx`.
2. **Document Parsing (`document.py`):** Extracts raw text. For `.docx`, preserves paragraph structure via `python-docx`. For `.txt`, reads as-is.
3. **Text Cleaning:** Strips non-prose content: tables, code blocks, reference lists, headers (configurable).
4. **Segmentation:** Splits into sentences (NLTK `sent_tokenize`) and paragraphs (double-newline boundaries).
5. **Analyzer Pipeline:** Each analyzer receives the tokenized text and returns a raw metric. Analyzers are independent — no inter-analyzer dependencies.
6. **Normalization (`scoring.py`):** Each raw metric is mapped to a 0–100 score using percentile thresholds from `corpus/norms.py`.
7. **Composite Score:** Weighted average of the 7 normalized scores.
8. **Report Generation (`report.py`):** Formats results as Markdown (human-readable) or JSON (machine-readable).
9. **Output:** Printed to stdout or written to file.

---

## 4. Scoring Model

### Normalization

Each raw metric is normalized to a 0–100 scale using **piecewise linear interpolation** against known thresholds.

Example — Burstiness (sentence length SD):

| Raw Value | Normalized Score | Interpretation |
|---|---|---|
| < 3.0 | 0–15 | Strong AI signal |
| 3.0 – 5.0 | 15–40 | Borderline |
| 5.0 – 12.0 | 40–85 | Typical human range |
| 12.0 – 20.0 | 85–95 | Strongly human |
| > 20.0 | 95–100 | Extremely varied (rare) |

Mapping function: `score = interpolate(raw_value, threshold_table)` where `threshold_table` is a list of `(raw, score)` breakpoints.

### Weighting Matrix

| Signal | Weight | Rationale |
|---|---|---|
| Burstiness | 25% | Strongest single discriminator in published research |
| Lexical diversity | 20% | Second-strongest; captures vocabulary richness |
| Transition density | 15% | Important but can be optimized consciously |
| Vocabulary fingerprint | 15% | Directly catches AI-favored word choices |
| Paragraph uniformity | 10% | Structural signal, slower to change |
| Readability | 10% | Useful in aggregate, weak alone |
| Perplexity (approx.) | 5% | Least reliable (approximate method) |

### Composite Score

```
composite = Σ (weightᵢ × scoreᵢ) / Σ weightᵢ
```

Where `scoreᵢ` is the normalized 0–100 value for signal `i`.

### Score Interpretation

| Range | Label | Meaning |
|---|---|---|
| 0–20 | AI-like | Text shares strong statistical profile with AI-generated text |
| 20–40 | AI-influenced | Multiple signals in AI range — likely AI-assisted |
| 40–60 | Mixed | Some signals human, some not — review flagged areas |
| 60–80 | Human-like | Mostly consistent with human academic writing |
| 80–100 | Authentic | Strongly human statistical profile |

---

## 5. CLI API Reference

### Command Structure

```
papersignals <command> [options] [file ...]
```

### Commands

#### `analyze`

Analyze one or more documents.

```
papersignals analyze paper.docx
papersignals analyze paper.txt --json
papersignals analyze paper.md --detailed
papersignals analyze *.pdf --batch
```

| Option | Type | Default | Description |
|---|---|---|---|
| `file` | positional | required | Path(s) to document(s) |
| `--json` | flag | False | Output JSON instead of Markdown |
| `--detailed` | flag | False | Include per-sentence and per-paragraph breakdowns |
| `--batch` | flag | False | Process multiple files (glob pattern) |
| `--output` | string | stdout | File path to write output |
| `--quiet` | flag | False | Suppress status messages |

#### `corpus`

Manage corpus baselines (Phase 2).

```
papersignals corpus update          # Fetch new arxiv baselines
papersignals corpus stats           # Show current baseline norms
papersignals corpus reset           # Reset to research-derived defaults
```

| Subcommand | Options | Description |
|---|---|---|
| `update` | `--category` (str), `--limit` (int) | Fetch papers from arXiv API and recompute norms |
| `stats` | — | Display current baseline distributions |
| `reset` | — | Restore factory-default thresholds |

#### Global Options

| Option | Description |
|---|---|
| `--version` | Show version and exit |
| `--help` | Show help message and exit |

---

## 6. Architecture History & Roadmap

### Phase 2 ✅ — Completed: Corpus Calibration + RF Classifier

**Goal:** Replace static research-derived thresholds with dynamic baselines computed from a real corpus of human-written academic papers, and add a data-driven classifier.

**What was built:**
- **`corpus/arxiv_fetcher.py`** — Downloads paper abstracts and full texts from arXiv API with rate limiting and caching.
- **`corpus/corpus_db.py`** — Local JSON-based database for paper metadata and analysis results.
- **`corpus/norms.py`** — Computes percentile distributions for all signal metrics from analyzed papers. Produces threshold tables usable by `scoring.py`.
- **`corpus/pipeline.py`** — End-to-end orchestrator: `fetch → analyze → norms`.
- **`classifier/features.py`** — Extracts 14 feature vectors from the 7 analyzer results.
- **`classifier/synthetic_ai.py`** — Rule-based AI text generator that applies AI-typical transformations to real text (uniform sentences, transition inflation, vocabulary injection).
- **`classifier/__init__.py`** — Random Forest classifier with Platt-scaled probability calibration.

**Results:**
- **Corpus:** 516 papers across 10 arXiv categories (cs.AI, cs.CL, cs.LG, cs.IR, cs.CY, cs.HC, stat.ML, stat.AP, eess.AS, eess.IV)
- **Classifier:** 70.5% accuracy, 0.78 ROC-AUC (5-fold CV, 516 human + 516 synthetic AI)
- **Top features:** Readability FK (14.7%), Readability Fog (14.1%), Transition density (12.8%), Vocabulary density (10.3%)
- **Integration:** `papersignals analyze` automatically uses RF scoring when model is available, falls back to weighted average otherwise

**Data flow:**
```
ArXiv API → arxiv_fetcher.py → raw text → analyzer pipeline → feature vectors
                                                                │
                                                                ▼
                                                      corpus/norms.py
                                                (updated percentiles)
                                                
                                                                     Random Forest
Human text → analyzer pipeline → feature vector ───→ ┌───────────┐  classifier  → RF score (0-100)
                                                        │ RF + Platt │
AI text → analyzer pipeline → feature vector ───→     │ calibration │
                                                        └───────────┘
```

### Phase 3 🔜 — Dashboard

**Goal:** Web-based GUI for visual analysis and batch processing.

**Components:**
- **FastAPI backend** — REST API wrapping the analyzer pipeline.
- **Next.js frontend** — Upload UI, interactive score breakdowns, per-signal charts.
- **Deployment** — Docker compose for self-hosted or cloud deployment.

**API endpoints (planned):**
```
POST /api/analyze          Upload document → receive score report
GET  /api/signals          List supported signals + descriptions
GET  /api/corpus/stats     Show current baseline norms
POST /api/corpus/update    Trigger arXiv baseline refresh
```

---

## 7. Design Decisions

### Why No ML Dependencies Initially

- **Install footprint:** NLTK + scikit-learn + numpy + pandas adds ~200MB. Pure Python + NLTK is ~20MB.
- **Reproducibility:** Rule-based scoring is deterministic and auditable. ML models introduce non-determinism and version-dependent results.
- **Explainability:** Every rule-based score can be traced to a specific formula and threshold. ML-based scores require SHAP/LIME for interpretation.
- **V1 pragmatism:** A simple linear model with hand-tuned weights approximates a more complex classifier for this feature space. The RF classifier in Phase 2 adds marginal accuracy but significant complexity.

### Why NLTK for Tokenization

- **Sentence segmentation accuracy:** NLTK's `sent_tokenize` (Punkt tokenizer) is widely tested and achieves >95% accuracy on academic text. Pure-regex approaches miss edge cases (e.g., "Fig. 2", "e.g.", "Dr. Smith", "U.S.").
- **Battle-tested:** Punkt has been the standard for sentence tokenization since 2006. Alternatives (spaCy, Stanza) require larger model downloads.
- **Single dependency:** Using NLTK for both sentence splitting and word tokenization means one dependency serves both needs. `pypdf` and `python-docx` handle file parsing.

### Why Percentile-Based Scoring

- **Scale invariance:** Raw metrics have different units and ranges (SD for burstiness, bits for entropy, counts per 1000 for vocabulary). Percentiles normalize them to a common scale without assuming a distribution shape.
- **Interpretable:** A score of 75 means "this metric is in the 75th percentile of human academic writing" — intuitive and transparent.
- **Corpus-updatable:** When Phase 2 adds real corpus data, the percentile mappings update automatically. The scoring logic doesn't change, only the reference distributions.
- **Robust to outliers:** Percentile-based normalization caps extreme values, preventing a single anomalous signal from dominating the composite.

### Why Weighted Average (Not ML)

- **Low data regime:** With 7 features and no training data, a weighted average with theory-derived weights is more robust than an uncalibrated ML model.
- **Interpretable:** Students and instructors can understand "burstiness counts for 25% of your score." An ML model's decision boundary is opaque.
- **Controllable:** Weight adjustments are explicit and documented. Users can see exactly what drives their score.

### Other Decisions

- **`.txt` and `.docx` first:** These cover >90% of student submissions. `.pdf` support is planned but deferred (PDF parsing is notoriously inconsistent across libraries).
- **No network access required:** All analysis is local. No data leaves the machine.
- **MIT License:** Maximum permissive for academic and commercial use.
- **Python 3.10+:** Modern typing, structural pattern matching, and `match` statement available for cleaner analyzer dispatch.

---

*PaperSignals — Making writing quality transparent. MIT License.*
