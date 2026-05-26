# PaperSignals Playbook — Writing Guide for Students

> **Purpose:** Actionable strategies to write original, high-quality academic work that scores under 20% on both Turnitin AI detection and similarity checks — without resorting to gimmicks, humanizers, or unethical shortcuts.

---

## 1. Introduction

### The Two-Threshold Problem

Every submitted paper faces **two independent scans**:

1. **AI Writing Indicator:** Scores the percentage of prose predicted to be AI-generated (threshold: <20% to avoid flagging).
2. **Similarity Report:** Scores the percentage of text matching Turnitin's database (threshold: <20–25%, varies by institution).

These are **separate systems** with **separate detection logics**. A paper can score 1% on AI but 40% on similarity (e.g., a literature review with block quotes), or 80% AI but 2% similarity (e.g., original analysis written by ChatGPT). You need to pass **both**.

### The Core Principle

> The best way to beat AI detection is to write like a human who deeply understands their subject. The best way to beat similarity detection is to write like a scholar who synthesizes sources rather than copying them.

These two goals converge on the same strategy: **authentic, thoughtful academic writing**.

---

## 2. AI Detection Avoidance

PaperSignals identifies four layers where AI text differs from human writing. Each layer must be addressed independently.

### Layer 1: Structural Variation

**The problem:** AI text has uniform structure — same sentence lengths, same paragraph lengths, same organizational pattern every time.

**The fix — structural variation strategies:**

| Strategy | Do This | Don't Do This |
|---|---|---|
| Vary paragraph length | Mix 2-sentence and 10-sentence paragraphs | All paragraphs 4–6 sentences |
| Change paragraph structure | Some paragraphs: claim → evidence → analysis. Others: data → question → interpretation | Every paragraph follows the same template |
| Use section-level rhythm | Alternate dense sections with lighter ones | Every section has identical depth/density |
| Break the "three-part" mold | Occasionally use one-paragraph sections or long block paragraphs | Introduction/Body/Conclusion always evenly split |

**Quick check:** Count the words in each paragraph. If the standard deviation is below 35% of the mean, your structure is too uniform.

### Layer 2: Sentence Rhythm

**The problem:** AI sentences all feel the same length because they are. Token prediction naturally converges on a narrow sentence-length band.

**The fix — sentence rhythm strategies:**

- **The Short-Embedding Pattern:** Place a 5–10 word sentence between two 20–35 word sentences. This creates a "rhythm break" that feels natural.
- **Vary Sentence Openings:** Track your first 3 words of each sentence across a paragraph. If more than 2 start with the subject, rewrite some to start with adverbials ("In contrast," "Building on this," "Unlike prior work").
- **Use the Grammar Toolkit:** Intersperse simple sentences (SVO), compound sentences (coordinating conjunctions), complex sentences (subordinate clauses), and compound-complex sentences.
- **Punctuation Pattern Variation:** Alternate between sentences with commas, dashes, colons, semicolons, and no internal punctuation.

**Metric target:** Aim for a sentence length standard deviation >5.0 for any document over 500 words.

### Layer 3: Vocabulary and Transitions

**The problem:** AI text relies on a narrow set of transition words and "favorite" vocabulary that creates a statistical fingerprint.

**The fix — vocabulary strategies:**

**Transition Management:**
- Build a personal list of 25+ transitions across 6 categories.
- Rotate through them deliberately — never use the same transition twice in a 10-sentence window.
- Place ~30% of transitions mid-sentence or parenthetically.
- Omit transitions entirely in ~20% of paragraphs (let content logic carry the connection).

**Vocabulary Management:**
- Run a search for these high-risk words: *delve, leverage, pivotal, robust, comprehensive, navigate, multifaceted, nuanced, paradigm, foster, underscore, facilitate, intricate, synthesize, testament, tapestry, realm.* Replace every instance.
- Use domain-specific vocabulary where appropriate — it's harder for AI to generate convincing specialized language.
- If you use the same abstract noun three times in a paragraph, find alternatives for at least two.

### Layer 4: Personal Voice

**The problem:** AI text is editorially neutral — it has no stance, no personality, no judgment beyond what's explicitly prompted.

**The fix — voice strategies:**

- **State your position:** Use first-person judgment ("I argue," "We contend," "This analysis demonstrates") rather than passive observation ("It can be argued").
- **Include your reasoning process:** Show how you arrived at a conclusion, not just the conclusion itself ("At first glance, this seems to support X, but further analysis reveals Y").
- **Use field-specific evaluative language:** Express qualitative judgments about your sources ("a particularly compelling framework," "a more limited approach").
- **Acknowledge uncertainty naturally:** Human writers hedge, qualify, and concede limitations. AI text tends to over-assert or over-hedge.

---

## 3. Similarity Avoidance

### The Read-Close-Write Method

This three-step method prevents similarity flags while building genuine understanding:

1. **Read:** Read the source material until you understand it well enough to explain it to a peer without notes.
2. **Close the source:** Physically close the browser window or tab. No peeking.
3. **Write:** Write your synthesis from memory and understanding, not from the source text.

This forces you to reconstruct ideas in your own words and structure, dramatically reducing string-matching similarity.

### Structure-Level Paraphrasing

Don't paraphrase at the sentence level — paraphrase at the **structure level:**

| Level | What to change | Example |
|---|---|---|
| Sentence | Word choice, syntax | "The study found X" → "X was observed in the study" |
| Paragraph | Order of claims, evidence flow | Rearrange the claim-evidence-analysis sequence |
| Section | Organizational logic | If the source starts with method → results → discussion, you might start with the research question → hypothesis → evidence |

### Source Synthesis

Instead of treating each source independently (which leads to "According to Smith... According to Jones..."), **synthesize**:

**Weak (high similarity risk):**
> Smith (2023) found that students who use AI detectors show increased anxiety. Jones (2024) found that AI detection accuracy varies by discipline.

**Strong (low similarity risk):**
> The psychological impact of AI detection systems, documented by Smith (2023), intersects with the technical variability Jones (2024) identified across disciplines — suggesting that the same system may cause disproportionate anxiety in fields where it performs least reliably.

### Citation Best Practices

- **Cite early, cite often:** Every claim that isn't common knowledge or your original analysis needs a citation.
- **Use signal phrases varied by verb:** Instead of "Smith states," rotate through "Smith argues," "Smith contends," "Smith observes," "Smith emphasizes," "Smith demonstrates."
- **Paraphrase quotations:** Only use direct quotes when the exact wording matters (e.g., legal language, definitions, memorable phrasing). Paraphrase everything else.
- **Check the "exclude bibliography" setting:** Ensure your reference list isn't inflating similarity — most institutions exclude it, but verify.

---

## 4. What NOT to Do

### Ineffective Techniques (Evidence-Based)

| Technique | Why It Fails | Evidence |
|---|---|---|
| **QuillBot / Paraphrasing tools** | AIR-1 (July 2024) specifically targets paraphraser artifacts. The substitution pattern is statistically detectable. | Perkins et al. 2024: Simple editing reduced detectability by 44%, but automated paraphrasing introduces new detectable signals. Turnitin July 2024 update closed this gap. |
| **"AI Humanizer" services** | August 2025 update specifically targets contradictory signals — low perplexity with artificially inflated burstiness/TTR. Cross-sentence semantic bleed gives them away. | Turnitin claims <10% bypass rate post-update vs. ~60% pre-update. |
| **Synonym-swapping** | Replacing individual words with thesaurus alternatives leaves the original sentence architecture intact. Detectors read structure, not just word choice. | Goulart et al. 2024: Surface edits don't change underlying statistical distribution. |
| **Adding typos / misspellings** | Deliberate typos are themselves detectable — they follow predictable "error" patterns. Detectors can distinguish organic errors from intentional ones. | Turnitin's model is trained on adversarial examples including artificial typos. |
| **Hidden text / white font** | Turnitin's parser strips formatting. Hidden text is invisible in the similarity report but doesn't affect AI detection at all. | HTML/CSS tricks don't survive .docx → plain text conversion. |
| **Empty or rearranged filler** | Adding empty sentences ("It is important to note that...") increases word count but doesn't change the underlying statistical profile; the added sentences themselves score as AI. | Word-count padding is transparent to sentence-level scoring. |

### The Only Strategies That Work

1. Write original content.
2. Edit and revise your own writing.
3. Document your process (see Section 6).
4. Use AI as a research assistant, not a ghostwriter.

---

## 5. Recommended Writing Workflow

A 7-step process designed to produce authentic, low-risk academic writing.

### Step 1: Research Phase (1–2 days)

- Read 8–12 sources for background understanding.
- Take handwritten notes on key arguments, evidence, and gaps.
- Do **not** copy-paste anything into your document yet.

### Step 2: Outline Phase (2–4 hours)

- Structure your argument on paper or in an outliner.
- For each section, note: (a) the claim you're making, (b) the evidence you'll use, (c) the source of that evidence.
- Do **not** write full sentences in the outline.

### Step 3: First Draft — Write Hot (4–8 hours)

- Write the entire draft without consulting sources (use your notes only).
- Don't worry about style, grammar, or transitions — just get the ideas down.
- Target: get the argument structure solid, even if the prose is rough.

### Step 4: Source Integration (2–3 hours)

- Go back and add citations where you drew on source material.
- Read the original source for each citation; if your paraphrase is too close, rewrite it.
- Ensure every cited claim has appropriate context.

### Step 5: Structural Editing (2–3 hours)

- Check paragraph length variation — the longest paragraph should be at least 2x the shortest.
- Check sentence length variation — aim for SD > 5.0.
- Vary your transitions and sentence openings.

### Step 6: Line Editing (2–3 hours)

- Search for AI-favored words and replace them.
- Read every sentence aloud to catch unnatural rhythm.
- Check for vocabulary repetition (same word used within 3-sentence window).
- Add your personal voice — judgment, stance, reasoning.

### Step 7: Verification (30 minutes)

- Run PaperSignals (or another analyzer) on your draft.
- Address any signals in the yellow/orange range.
- Run a similarity check if available.
- **Do not** obsess over getting every signal to "perfect human" — the composite is what matters.

---

## 6. Engineering-Specific Tips (STEM / FYP / Thesis)

### The STEM Writing Challenge

Engineering and scientific writing has characteristics that **overlap with AI-generated text**:
- Standardized terminology
- Short, declarative sentences
- Passive voice prevalence
- Formulaic structure (IMRaD: Introduction, Methods, Results, and Discussion)

This means STEM writing is **more likely to trigger AI detection at baseline**.

### Adaptations for STEM Writers

**For the Introduction section:**
- Avoid the "In recent years, X has become increasingly important" opener (AI cliché).
- Start with a specific problem or observation instead.
- Use active voice where appropriate: "We investigated X" rather than "X was investigated."

**For the Methods section:**
- Include specific details that show hands-on knowledge (e.g., "We calibrated the spectrometer using..."), not generic description.
- Add remarks about why you chose one method over another — this reasoning is hard for AI to simulate convincingly.
- Use the past tense consistently (AI often defaults to present tense in methods).

**For the Results section:**
- Let figures and tables carry the detailed data; use text for interpretation and patterns.
- Avoid repeating figure captions in the body text.
- Include unexpected or null results — AI tends to report only expected findings.

**For the Discussion section:**
- Acknowledge limitations in specific, personal terms ("We were unable to control for X because..." rather than "Further research is needed").
- Draw connections to your own prior work or course material.
- Propose specific next steps, not generic future directions.

### FYP / Thesis-Specific Tips

- **Write the literature review from synthesis, not summary.** Group sources by theme, not by author.
- **Document your design decisions.** Engineering theses benefit from "why" explanations at each decision point — these are uniquely human.
- **Include personal reflections.** An engineering reflection paragraph (what went wrong, what you'd do differently) is almost impossible for AI to fake convincingly.
- **Use your experimental data as a structural anchor.** Let your results dictate the narrative flow rather than imposing a template.

---

## 7. Paper Trail — Building Your Evidence Base for False Positive Appeals

Even the best writing can trigger a false positive. If your institution's Turnitin flags your paper, you need **evidence that you wrote it**.

### What to Save During Your Writing Process

| Evidence Type | How to Generate It | Why It Helps |
|---|---|---|
| **Version history** | Save drafts at each phase (outline, first draft, edited draft, final). Google Docs/Overleaf version history is ideal. | Shows progressive development, not a single AI generation event. |
| **Timestamped notes** | Take research notes in a dated file or notebook. | Shows that you engaged with sources before writing. |
| **Outlines and diagrams** | Save your pre-writing outline, concept maps, or whiteboard photos. | Demonstrates planning and structure development. |
| **Source annotations** | Annotated PDFs, marginal notes, or reading journals. | Shows engagement with source material. |
| **Peer review comments** | Drafts with track changes or comments from peers/supervisors. | Shows collaborative revision process. |
| **Lab notebooks / design journals** | For engineering projects, your lab notebook is the strongest evidence. | Demonstrates hands-on work that produced the reported results. |

### What NOT to Say in an Appeal

- "I used an AI writing assistant but only for grammar." (This undermines your claim.)
- "The detector is biased against non-native speakers." (Often true, but it sounds like an excuse.)
- "I don't know how the AI got into my document." (Implies carelessness or dishonesty.)

### How to Approach Your Instructor

1. **Be proactive:** If you know your paper might trigger detection (e.g., you write in a concise, formulaic style), mention it when you submit.
2. **Present evidence, not excuses:** Show your draft history, notes, and outline. Let the work speak.
3. **Request a conversation:** "I'd like to walk through my writing process for this paper" is more effective than "The detector is wrong."
4. **Know your signals:** If your PaperSignals report shows human-range scores, reference it. If it shows borderline scores, acknowledge the concern and explain the structural/professional factors that may be causing it.

---

## Final Checklist

Before submitting, verify:

- [ ] PaperSignals composite score > 60 (or at least above 40 with an acknowledged reason)
- [ ] Sentence length SD > 5.0
- [ ] No AI-favored words (*delve, leverage, pivotal, robust*, etc.)
- [ ] Paragraph CV > 0.50
- [ ] Transition entropy > 3.5 bits
- [ ] Personal voice markers present (judgment, stance, reasoning)
- [ ] All direct quotes properly cited and enclosed in quotation marks
- [ ] All paraphrased passages use structure-level (not sentence-level) rewriting
- [ ] Draft history or version trail saved

---

*PaperSignals — Making writing quality transparent. MIT License.*
