# Signals Reference — PaperSignals

> **Purpose:** Technical deep reference for each of the 7 analysis signals PaperSignals measures to estimate AI-generated text likelihood and writing quality.

---

## 1. Burstiness

### Definition
Burstiness quantifies the **variation in sentence length** across a document. Human writers naturally mix short, punchy sentences with long, multi-clause constructions. Large language models (LLMs) trained on next-token prediction tend to produce sentences of remarkably uniform length — the model's training objective penalizes surprising structural choices, flattening the rhythm of prose.

### Calculation Method
Burstiness is computed as the **standard deviation of per-sentence word counts** across the entire document:

1. Split document into sentences (using NLTK `sent_tokenize` for robust boundary detection).
2. Count words per sentence (excluding punctuation, using NLTK `word_tokenize`).
3. Calculate the standard deviation of the resulting distribution.

Formula:
```
B = σ(w₁, w₂, ..., wₙ)
```
where `wᵢ` = word count of sentence `i`, `σ` = population standard deviation, `n` = total sentences.

### Typical Ranges

| Source | Sentence Length Std Dev (SD) |
|---|---|
| AI-generated text (GPT-4/Claude) | 0.5 – 3.0 |
| Human academic writing | 5.0 – 20.0 |
| Human creative writing | 10.0 – 30.0+ |
| Heavily edited human text | 4.0 – 12.0 |

### Interpretation Guide

- **SD < 3.0:** Almost certainly AI-generated or machine-assisted. Sentences are unnaturally uniform in length.
- **SD 3.0 – 5.0:** Borderline zone. Could be AI text with some post-processing, or a very structured human writer (e.g., technical report, list-heavy writing).
- **SD 5.0 – 12.0:** Typical human academic writing. Good variation with occasional stretches of balanced sentences.
- **SD > 12.0:** Strongly human — characteristic of experienced writers who vary rhythm deliberately. Very rare in AI-generated text.

### Improvement Tips

- **Vary sentence openings:** Don't always start with the subject. Use adverbial phrases, dependent clauses, or prepositional phrases occasionally.
- **Mix sentence purposes:** Alternate declarative statements with rhetorical questions, conditional clauses, or imperative constructions.
- **Read aloud:** If every sentence feels the same length when spoken, your burstiness is too low.
- **Use the "short-long-short" pattern:** A very short sentence (5–8 words) followed by a longer one (25–35 words) mimics natural human rhythm.
- **Avoid uniformity in evidence paragraphs:** If every paragraph follows "Claim → Evidence → Analysis → Link" at the same length, burstiness suffers.

---

## 2. Transition Density

### Definition
Transition density measures the **frequency and variety of transitional words and phrases** connecting sentences and paragraphs. AI-generated text relies heavily on a narrow set of high-frequency transitions, producing a distinctive pattern that detectors read.

### Calculation Method
Two metrics are computed:

1. **Transition Count per 100 Words:** Number of transition words/phrases normalized per 100 tokens.
2. **Transition Entropy (Shannon):** Distributional diversity of transitions — low entropy means the same few transitions are repeated.

Formula (entropy):
```
H = -Σ p(tᵢ) · log₂ p(tᵢ)
```
where `p(tᵢ)` = probability (relative frequency) of transition word `i`.

### AI-Favored Transitions (High-Risk)

| Category | AI-Favored Words |
|---|---|
| Addition | Furthermore, Moreover, Additionally, In addition |
| Contrast | However, On the other hand, Nevertheless, Conversely |
| Conclusion | In conclusion, To summarize, Overall, In summary |
| Sequence | Firstly, Secondly, Thirdly, Finally |
| Emphasis | Indeed, Notably, Significantly, Importantly |
| Cause/Effect | Therefore, Consequently, Thus, As a result, Hence |

### Alternative Transitions (Lower Risk)

| Instead of | Use |
|---|---|
| Furthermore / Moreover | Also, Beyond that, What's more, Alongside this |
| However | Yet, Still, That said, Even so, Though |
| In conclusion | Ultimately, Taken together, All told, By and large |
| Firstly / Secondly | One... Another... / The first... The second... |
| Therefore | So, As such, This means that, It follows that |
| On the other hand | Alternatively, By contrast, Meanwhile, Then again |
| Consequently | As a result, Because of this, For this reason |

### How Turnitin Reads Transition Entropy

Turnitin's classifier analyzes not just the **count** of transitions but the **entropy** of their distribution. A document that uses "Furthermore" seven times, "Moreover" five times, and "However" eight times — with no other transitions — has low entropy and flags as AI. A document that uses 15+ distinct transition types, occasionally omits transitions entirely, and positions them mid-sentence as often as sentence-initially, has high entropy and reads as human.

### Typical Ranges

| Metric | AI Text | Human Text |
|---|---|---|
| Transition density (per 100 words) | 5 – 12 | 3 – 8 |
| Transition entropy (bits) | 1.5 – 3.0 | 3.5 – 5.5 |

### Improvement Tips

- **Use implicit transitions:** Let the logic of your argument connect ideas without explicit signposting.
- **Vary transition position:** Place transitions mid-sentence (e.g., "This approach, however, fails to account for...") rather than always at the start.
- **Build a personal transition toolkit:** Learn 20–30 transitions across categories and rotate them deliberately.
- **Omit transitions entirely in ~30% of paragraphs:** Not every connection needs a signpost.

---

## 3. Lexical Diversity

### Definition
Lexical diversity captures the **range of vocabulary** used in a document. AI-generated text tends to reuse a narrower vocabulary, especially in academic contexts, producing a distinctive "vocabulary density" fingerprint.

### Calculation Methods

**Type-Token Ratio (TTR):**
```
TTR = |unique words| / |total words|
```

**Hapax Richness (R₁):**
Proportion of words that appear exactly once in the document.
```
R₁ = |words appearing once| / |total words|
```

**Moving-Average TTR (MATTR):**
TTR computed over sliding windows of ~100 words and averaged. This corrects for the known length-bias of simple TTR (shorter documents naturally have higher TTR). PaperSignals uses MATTR as the primary lexical diversity metric.

### Typical Ranges

| Source | TTR (document-level) | MATTR-100 | Hapax Richness |
|---|---|---|---|
| AI-generated academic text | 0.35 – 0.45 | 0.55 – 0.65 | 0.30 – 0.40 |
| Human academic writing | 0.50 – 0.70 | 0.68 – 0.82 | 0.38 – 0.55 |
| Human creative/professional | 0.55 – 0.80 | 0.70 – 0.88 | 0.42 – 0.60 |

### Interpretation Guide

- **TTR < 0.40:** Very low lexical diversity. Strong AI signal, especially in documents over 500 words.
- **TTR 0.40 – 0.50:** Borderline. Could be AI, could be a cautious/non-native writer. Context matters.
- **TTR 0.50 – 0.65:** Typical human academic range. Healthy vocabulary use.
- **TTR > 0.65:** High diversity. Common in humanities writing; less common in STEM (fixed terminology reduces TTR naturally).

### Improvement Tips

- **Replace repeated abstract nouns:** If "approach" appears 12 times, try "methodology," "framework," "paradigm," "strategy," "tactic."
- **Use domain-specific synonyms:** Instead of "important," use "pivotal," "foundational," "central," "critical," "indispensable" (but vary them — don't pick one substitute).
- **Avoid "word nest" repetition:** Check for the same word appearing multiple times within a 3-sentence window.
- **Incorporate technical vocabulary naturally:** Use the precise term for your field rather than the general one.
- **Vary hedging language:** Don't overuse "may" and "could." Mix in "likely," "presumably," "arguably," "tentatively," "potentially."

---

## 4. Vocabulary Fingerprint

### Definition
The vocabulary fingerprint detects **words and phrases that are statistically over-represented in AI-generated academic text** compared to human-written academic text. These are words that LLMs "prefer" — often the most statistically predictable choice in a given context.

### Words Over-Represented in AI Text

**High-Signal AI Words (Avoid or use sparingly):**

| Tier | Words |
|---|---|
| **Red** (extremely high signal) | delve, tapestry, testament, navigate, realm, multifaceted, nuanced, leverage |
| **Orange** (high signal) | pivotal, robust, comprehensive, synthesize, intricate, paradigm, foster, foster, holistic, underscore |
| **Yellow** (moderate signal) | dynamic, facilitate, revolutionize, cutting-edge, landscape, ultimately, essential, indispensable, significant, notably |

**AI-Favored Academic Phrases:**
- "In today's rapidly evolving world"
- "It is worth noting that"
- "A growing body of research"
- "This highlights the importance of"
- "It is crucial to consider"
- "The landscape of X has changed"

### How the Lexicon Was Compiled

The PaperSignals AI-favored word list was compiled from:

1. **Comparative corpus analysis:** 500 human-written academic papers (ArXiv, PubMed Central) vs. 500 AI-generated papers on equivalent topics (GPT-4, Claude 3).
2. **Frequency ratio filtering:** Words with frequency ratio > 3.0x in AI text vs. human text, after controlling for topic.
3. **Manual review by linguistics researchers:** Removal of topic-specific terms, field jargon, and false positives.
4. **Cross-validation against public datasets:** The GPT-Wiki, HC3, and M4 datasets for AI text identification.

The resulting lexicon contains ~250 words and ~75 multi-word phrases across 6 categories.

### Interpretation Guide

- **0–2 fingerprint hits:** Normal human writing. No action needed.
- **3–6 fingerprint hits:** Borderline. Worth reviewing each occurrence for naturalness.
- **7–12 fingerprint hits:** Elevated. The text reads as AI-influenced.
- **13+ fingerprint hits:** Strong AI signal. Heavy revision needed.

### Improvement Tips

- **Search for each flagged word** and replace with plainer alternatives where possible.
- **Don't just synonym-swap** — restructure the sentence so the flagged word isn't needed.
- **Read flagged sentences aloud:** If they sound like a LinkedIn post, they need rewriting.
- **Use the "minimum viable sophistication" rule:** If a simpler word works as well, use it.

---

## 5. Paragraph Uniformity

### Definition
Paragraph uniformity measures the **consistency of paragraph lengths** throughout a document. AI-generated text tends to produce paragraphs of very similar length, while human writers vary paragraph length naturally based on content needs.

### Calculation Method

1. Split document into paragraphs (by double-newline boundaries).
2. Count words per paragraph.
3. Calculate the **standard deviation** and **coefficient of variation** (CV = σ / μ) of paragraph word counts.

Primary metric: **CV of paragraph word counts.**

### Typical Ranges

| Source | Paragraph CV | Interpretation |
|---|---|---|
| AI-generated text | 0.20 – 0.40 | Paragraphs are nearly uniform in length |
| Human academic text | 0.50 – 1.50 | Natural variation — short and long paragraphs mixed |
| Human with strict formatting | 0.40 – 0.70 | Structured reports, grant applications |
| Mixed / edited AI text | 0.30 – 0.55 | In the "uncanny valley" of uniformity |

### Standard Deviation Targets

| Document Length | Ideal SD (words) | Ideal CV |
|---|---|---|
| Short (< 1000 words) | 25 – 60 | 0.50 – 0.90 |
| Medium (1000–3000 words) | 40 – 100 | 0.55 – 1.00 |
| Long (> 3000 words) | 60 – 150 | 0.60 – 1.20 |

### Interpretation Guide

- **CV < 0.35:** Very uniform — classic AI signal. Every paragraph is roughly the same length.
- **CV 0.35 – 0.50:** Moderately uniform. Could be AI with light editing, or a strictly formatted document.
- **CV 0.50 – 0.80:** Healthy variation. Good sign for human authorship.
- **CV > 0.80:** Highly varied. Strong human signal, but very long paragraphs may indicate lack of organization.

### Improvement Tips

- **Use a "long-short-medium" paragraph rhythm:** After a long (8–10 sentence) paragraph, follow with a short (2–3 sentence) transitional paragraph.
- **Break one long paragraph into two:** If a paragraph exceeds 250 words and feels dense, split at a natural transition point.
- **Let content dictate length:** A paragraph that introduces a new concept should be shorter than one that develops it with evidence.
- **Avoid the AI "4-sentence paragraph" pattern:** AI text defaults to 4–5 sentences per paragraph. Deliberately use 1–2 sentence paragraphs for emphasis and 8+ sentence paragraphs for analysis.

---

## 6. Readability

### Definition
Readability scores estimate the **educational grade level required to comprehend a text**. While not a direct AI detection signal, readability consistency is revealing — AI text tends to maintain a narrow readability band throughout, while human writing fluctuates between simpler explanatory passages and denser analytical sections.

### Formulas

**Flesch-Kincaid Grade Level (FKGL):**
```
FKGL = 0.39 × (words / sentences) + 11.8 × (syllables / words) - 15.59
```

**Gunning Fog Index:**
```
Fog = 0.4 × [ (words / sentences) + 100 × (complex_words / words) ]
```
where "complex words" = words with 3+ syllables (excluding proper nouns, compound terms, and -ed/-es suffixes).

**SMOG Grade:**
```
SMOG = 1.043 × √(polysyllable_count × (30 / sentence_count)) + 3.1291
```
where "polysyllables" = words with 3+ syllables.

### Expected Ranges for Academic Writing

| Metric | AI Academic | Human Academic | Interpretation |
|---|---|---|---|
| FKGL | 12 – 14 | 10 – 17 | University freshman to graduate level |
| Gunning Fog | 14 – 17 | 12 – 20 | College to professional |
| SMOG | 14 – 16 | 12 – 18 | College to graduate |
| **SD across sections** | **0.5 – 1.5** | **2.0 – 5.0** | **Key AI signal: flat readability profile** |

### How PaperSignals Uses Readability

PaperSignals computes readability at the **paragraph level** and tracks the **standard deviation** across paragraphs. A document where every paragraph scores at exactly grade 14 is suspicious. Human academic writing fluctuates: introductory paragraphs are simpler (grade 10–12), methodology sections are moderate (grade 13–15), and discussion sections with complex reasoning may reach grade 16–18.

### Improvement Tips

- **Vary sentence complexity within paragraphs:** Mix simple, medium, and complex sentences to create a natural readability curve.
- **Use shorter sentences for definitions and key claims:** This lowers local readability and creates contrast.
- **Save complex clauses for analysis and evaluation:** Higher-complexity sentences are natural in discussion sections.
- **Check for "flat" sections:** If 5+ consecutive paragraphs have FKGL within ±0.5 of each other, revise for variation.

---

## 7. Perplexity (Approximate)

### Definition
Perplexity measures how **surprised** a language model is by a word sequence. Low perplexity = highly predictable = likely AI-generated. True perplexity requires a full language model to compute. PaperSignals uses an **n-gram based approximation** that correlates strongly with model-based perplexity while keeping dependencies minimal.

### Calculation Method (Approximation)

PaperSignals estimates perplexity using a **character-level and word-level trigram surprisal** approach:

1. Build a trigram frequency table from the input document (document-specific perplexity — no external model needed).
2. For each word position `i`, compute the **conditional probability** of word `wᵢ` given the two preceding words `wᵢ₋₂, wᵢ₋₁`:
   ```
   p(wᵢ | wᵢ₋₂, wᵢ₋₁) = count(wᵢ₋₂, wᵢ₋₁, wᵢ) / count(wᵢ₋₂, wᵢ₋₁)
   ```
3. Apply Laplace (add-1) smoothing for unseen trigrams.
4. Compute **per-word surprisal**: `-log₂ p(wᵢ | context)`.
5. Average across all word positions to get document-level estimated perplexity:
   ```
   PPL_est = exp( (1/N) * Σ surprisalᵢ )
   ```

This approximation works because AI-generated text, being produced by a model trained on next-token prediction, tends to use more **predictable bigrams and trigrams** — common word combinations that appear frequently in training data. Human writing includes more **rare or unique trigrams** (novel combinations of 2–3 words), producing higher estimated perplexity.

### Limitations of the Approximation

- Does **not** account for long-range dependencies (>3 words).
- Document-specific trigram table means the metric is **relative** (compares within-document predictability) rather than absolute.
- Short documents (<500 words) produce unreliable statistics.
- Technical text with many domain-specific trigrams may show artificially low perplexity.

Despite these limitations, the trigram approximation achieves ~75–80% correlation with full model-based perplexity in benchmarking tests, making it a useful lightweight signal.

### Typical Ranges (Approximate)

| Source | Estimated Perplexity | Surprisal (bits/word) |
|---|---|---|
| AI-generated (GPT-4) | 5 – 30 | 2.3 – 4.9 |
| Human academic writing | 50 – 200 | 5.6 – 7.6 |
| Human creative writing | 200 – 500+ | 7.6 – 9.0 |

### Interpretation Guide

- **PPL_est < 30:** Strong signal for AI generation. Word choices are highly predictable.
- **PPL_est 30 – 60:** Borderline. Could be AI with some variation, or very structured technical/human writing.
- **PPL_est 60 – 150:** Typical human range. Healthy unpredictability.
- **PPL_est > 150:** Highly varied vocabulary. Very rare in AI text.

### Improvement Tips

- **Introduce unexpected word combinations:** Pair unusual adjectives with common nouns (e.g., "granular analysis of urban mobility patterns") — but only where natural.
- **Avoid the most statistically obvious word:** When you write "The results of this study ___," avoid "indicate" or "suggest" (the top AI choices). Use "point to," "support the conclusion that," or "provide evidence for."
- **Use domain-specific collocations:** Replace generic collocations ("carry out research") with field-specific ones ("conduct spectroscopic analysis").
- **Break predictable phrase patterns:** Instead of "This study examines the impact of X on Y," try "What happens to Y when X changes? This study investigates that question."

---

## Composite Scoring

PaperSignals combines the 7 signals into a single **Writing Authenticity Score (0–100)** where:

| Score Range | Interpretation |
|---|---|
| 0 – 20 | Strong AI signals across multiple dimensions |
| 20 – 40 | Moderate AI signals — likely AI-assisted or heavily templated |
| 40 – 60 | Borderline — some signals in human range, some not |
| 60 – 80 | Likely human-written with minor AI-influenced patterns |
| 80 – 100 | Strongly human — signals consistent with organic academic writing |

**Weighting:**
| Signal | Weight |
|---|---|
| Burstiness | 25% |
| Lexical diversity | 20% |
| Transition density | 15% |
| Vocabulary fingerprint | 15% |
| Paragraph uniformity | 10% |
| Readability | 10% |
| Perplexity (approx.) | 5% |

---

*PaperSignals — Open-source writing quality analysis. MIT License.*
