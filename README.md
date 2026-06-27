# TakeMeter 🎙️⚽

A fine-tuned text classifier that scores **discourse quality** on **r/soccer** during the
2026 FIFA World Cup. Given a comment, TakeMeter predicts whether it is structured
**analysis**, a confident **hot take**, or an emotional **reaction**.

> Full design rationale lives in [planning.md](planning.md). This README is the
> human-facing summary and will hold the final evaluation report.

---

## The community

[r/soccer](https://www.reddit.com/r/soccer/) during the 2026 World Cup — one of Reddit's
largest sports communities at its most active. A single match thread mixes keyboard-smash
celebrations, one-line career verdicts, and paragraph-long tactical breakdowns, so the
*quality* of discourse varies wildly within one place. The community itself already talks
in terms of "analysis vs. hot takes vs. reactions," which makes the labels grounded in real
norms rather than imposed from outside.

## The labels (2–4 required → 3 used)

Mutually exclusive. During annotation, check in priority order: `analysis` → `hot_take` →
`reaction`.

| Label | One-sentence definition | Example |
|-------|-------------------------|---------|
| **`analysis`** | A structured argument backed by specific, verifiable evidence — stats, tactical observation, historical comparison, or a causal explanation that stands without the opinion. | *"Spain control this because Rodri drops between the CBs, making it 3-v-2 in the first phase — both fullbacks push up and England's front two can't cover all three."* |
| **`hot_take`** | A bold, confident opinion stated as a verdict without genuine reasoning — asserts rather than argues; any stat is decorative. | *"Mbappé is the most overrated player of his generation, full stop."* |
| **`reaction`** | An immediate emotional response to a moment — celebration, groan, joke, or vibe; little to no argument. (Jokes/banter fold in here.) | *"NOOOO HOW DID HE MISS THAT 😭😭 I can't watch the rest"* |

**Hardest edge case — the one-stat hot take.** *"Mbappé is washed — 1 goal in his last 4
knockout games."* Has a stat, but it's cherry-picked ammunition for a verdict, not
reasoning → **`hot_take`**. Decision rule: if stripping the opinion leaves evidence that
genuinely explains the claim → `analysis`; if it leaves a lone decorative stat →
`hot_take`. (More edge cases in [planning.md §3](planning.md).)

---

## Repo layout

```
planning.md              # the spec (design decisions, metrics, success criteria)
README.md                # this file + final evaluation report
requirements.txt         # local data-prep deps (stdlib only — nothing required)
docs/
  scraping_guide.md      # Chrome step-by-step: scrape r/soccer comments
  labeling_cheatsheet.md # 3-question rule for labeling fast + resolved edge cases
scripts/
  merge_raw.py           # merge + clean scraper CSV exports → raw_comments.csv (local)
  build_dataset.py       # combine batches + balance classes → data/labeled.csv
data/
  labeled.csv            # ← THE dataset: text, label, notes  (200 rows, 20/40/40)
notebook/                # created when you download the Colab outputs
  evaluation_results.json   # downloaded from Colab after training
  confusion_matrix.png      # downloaded from Colab after training
```

> **Important:** the dataset is **one single `data/labeled.csv`** — do *not* commit
> pre-split files. The Colab notebook performs the 70/15/15 train/val/test split itself.
> (Raw scraped CSVs and `raw_comments.csv` stay local — they're git-ignored.)

---

## Data collection

Comments are scraped from r/soccer World Cup threads (match, post-match, and
tactics/discussion threads — see [planning.md §4](planning.md) for the sampling strategy
that keeps all three labels above the 20% floor). Full Chrome walkthrough:
**[docs/scraping_guide.md](docs/scraping_guide.md)**. Pipeline:

```bash
# 1. Scrape r/soccer threads in Chrome with the "Instant Data Scraper" extension (see guide),
#    saving each export into data/  (mix of celebration AND argument-heavy threads)

# 2. Merge + clean the exports into one raw file
python3 scripts/merge_raw.py --glob "data/reddit*.csv" --out data/raw_comments.csv

# 3. Pre-label every comment with an LLM (Claude), then review by hand

# 4. Combine batches + balance the classes into the final dataset
python3 scripts/build_dataset.py        # -> data/labeled.csv (200 rows, 20/40/40)
```

The final deliverable is the single `data/labeled.csv` — the Colab notebook splits it
70/15/15 automatically.

### Where the data came from
Public r/soccer comments scraped during the **2026 World Cup group stage** (June 2026) via
the Instant Data Scraper Chrome extension, across **two batches of threads**:
- **Batch 1** — celebration / photo / banter threads (Cape Verde's 0-0 vs Spain, the Viking
  team-photo post, the Mexican-duck mascot, vegemite banter, South Africa meme reactions).
  267 comments, overwhelmingly `reaction`.
- **Batch 2** — argument-heavy threads (Frenkie de Jong's "fans watch but don't see football"
  tactics debate, the Messi-vs-Jordan GOAT thread, Belgium's struggles, the red-cards and
  goalkeeper-saves stat threads). 271 comments, rich in `analysis` and `hot_take`.

### Labeling process
Comments were **pre-labeled with an LLM (Claude Opus 4.8)** against the planning.md
definitions, then reviewed (see AI Usage). Batches were cleaned (`merge_raw.py`: drop
deleted/bot/duplicate/too-short, strip URLs) and merged. Because the combined set was still
~78% `reaction`, we kept **every** `analysis` and `hot_take` comment and **down-sampled the
surplus `reaction`** to a balanced 200-row set (`build_dataset.py`, seed 42).

### Label distribution (final `labeled.csv`, n = 200)
| label | count | share |
|-------|------:|------:|
| `reaction` | 80 | 40% |
| `hot_take` | 79 | 40% |
| `analysis` | 41 | 20% |

No class exceeds 70%; every class clears the 20% floor.

### Three genuinely hard-to-label examples
1. **Bare critical stat — `analysis` vs `hot_take`.**
   *"Ronaldo hasn't scored a non-penalty goal in a major competition since June 19, 2021."*
   A specific, verifiable stat — but it's a lone number deployed as an implied verdict, with
   no mechanism or argument. Per the decision rule (decorative cherry-picked stat → hot_take)
   → **`hot_take`**.
2. **Snark that cites real evidence — `analysis` vs `hot_take`.**
   *"We can literally access the pass maps after the game. This just sounds like a player
   being bitter that they've gotten found out to be a side pass merchant."*
   The tone is a dig, but it grounds the claim in a verifiable method (post-match pass maps).
   Because removing the snark still leaves real evidentiary reasoning → **`analysis`**.
3. **Celebratory factoid — `analysis` vs `reaction`.**
   *"More points than in the last 3 world cups."*
   States a true historical fact, which looks like `analysis`, but it carries no argument or
   mechanism — it's an emotional "look how far we've come" beat in a celebration thread →
   **`reaction`**.

> **Remaining annotation step (yours):** the labels are AI pre-labels. Skim `labeled.csv`
> (especially the `analysis`/`hot_take` rows) to confirm or correct them in your own
> judgment before training — the assignment requires you to review every label.

---

## Fine-tuning

- **Base model:** `distilbert-base-uncased` (HuggingFace)
- **Hyperparameters:** 10 epochs, batch size 8, learning rate 3e-5, `warmup_ratio=0.1`,
  `weight_decay=0.01`, `load_best_model_at_end=True` (evaluated against validation set each epoch)
- **Best checkpoint:** epoch 2 (val accuracy 0.733); later epochs overfit and were discarded
  automatically by `load_best_model_at_end`
- **Split:** stratified 70/15/15 → 140 train / 30 val / 30 test

## Baseline

Zero-shot **Groq `llama-3.3-70b-versatile`** prompted with the planning.md label definitions
and decision rules, evaluated on the same 30-example held-out test set.

## Evaluation report

### Overall results

| Model | Accuracy | Macro-F1 |
|-------|:--------:|:--------:|
| Zero-shot baseline (Groq llama-3.3-70b) | **0.833** | **0.86** |
| Fine-tuned DistilBERT | 0.700 | 0.67 |

The fine-tuned model did **not** beat the zero-shot baseline on either metric. With only
140 training examples, DistilBERT is learning a classification head from scratch — the
70B-parameter Groq model starts from a far stronger prior on what a "reasoned argument"
looks like.

### Per-class metrics

**Fine-tuned DistilBERT (test set, n = 30):**

| Label | Precision | Recall | F1 | Support |
|-------|:---------:|:------:|:--:|:-------:|
| `analysis` | 0.60 | 0.50 | 0.55 | 6 |
| `hot_take` | 0.62 | 0.67 | 0.64 | 12 |
| `reaction` | 0.83 | 0.83 | 0.83 | 12 |
| **macro avg** | **0.68** | **0.67** | **0.67** | 30 |

**Zero-shot baseline — Groq llama-3.3-70b-versatile (test set, n = 30):**

| Label | Precision | Recall | F1 | Support |
|-------|:---------:|:------:|:--:|:-------:|
| `analysis` | 1.00 | 1.00 | 1.00 | 6 |
| `hot_take` | 0.82 | 0.75 | 0.78 | 12 |
| `reaction` | 0.77 | 0.83 | 0.80 | 12 |
| **macro avg** | **0.86** | **0.86** | **0.86** | 30 |

### Confusion matrix (fine-tuned model)

| True ↓ / Predicted → | `analysis` | `hot_take` | `reaction` |
|---|:---:|:---:|:---:|
| **`analysis`** | **3** | 3 | 0 |
| **`hot_take`** | 2 | **8** | 2 |
| **`reaction`** | 0 | 2 | **10** |

Main confusion pairs: `analysis`↔`hot_take` (5 cross-errors) and `hot_take`↔`reaction`
(4 cross-errors). Image: [notebook/confusion_matrix.png](notebook/confusion_matrix.png).

### Three analyzed wrong predictions

**Error 1 — `analysis` predicted as `hot_take` (confidence 0.70):**
> *"Getting mad at a striker for calling for it in the box when the team is just trying to
> pass sideways and backwards otherwise is pretty silly"*

The comment makes a causal tactical argument (the striker's action is rational given how the
team is playing) → `analysis`. But the dismissive framing ("pretty silly") matches surface
patterns the model learned for `hot_take`. The model is classifying by tone rather than
reasoning structure.

**Error 2 — `hot_take` predicted as `analysis` (confidence 0.51):**
> *"Ronaldo hasn't scored a non-penalty goal in a major competition since June 19, 2021."*

This is the exact "one-stat hot_take" edge case documented in [planning.md §3](planning.md).
A precise date is a strong learned signal for `analysis`, but the stat is deployed as an
implied verdict with no causal argument. The model learned: specific numbers → `analysis`,
missing the "decorative cherry-pick" distinction the decision rules were written to handle.

**Error 3 — `reaction` predicted as `hot_take` (confidence 0.54):**
> *"Build a statue for the keeper, he played his heart out"*

Hyperbolic celebratory praise superficially resembles a verdict on a player's quality.
The model has not learned that superlatives in celebration contexts are emotional
amplification, not confident opinionating.

### Systematic error patterns (9 total errors)

| Pattern | Count |
|---------|:-----:|
| Dismissive/snarky phrasing triggers `hot_take` for true `analysis` | 3 |
| Specific stats/dates trigger `analysis` for true `hot_take` (lone-stat trap) | 2 |
| Hyperbolic celebration read as verdict (`reaction` → `hot_take`) | 2 |
| Very short or sarcastic `hot_take` read as `reaction` | 2 |

Pattern 1 is the most consequential: the model learned a tone shortcut instead of the
intended structural distinction (evidence quality). Pattern 2 confirms the exact edge case
documented before training is the one the model fails on most.

### Reflection — learned vs. intended

The model learned useful surface heuristics: `reaction` is handled well (F1 = 0.83) when
comments are short, use emoji, or start with expressive openers. Clean one-liner hot_takes
are mostly correct. But the `analysis`↔`hot_take` boundary — the core distinction the
taxonomy was designed to capture — is where the model fails most (F1 = 0.55 on `analysis`).

The root problem is data volume: with only 28 `analysis` training examples, DistilBERT
cannot build a robust representation of "evidence quality." The Groq baseline (70B
parameters, trained on internet-scale text including sports forums) already has an implicit
model of what a reasoned argument looks like — 140 training examples cannot overcome that
prior on a nuanced 3-way distinction.

**Against success criteria ([planning.md §6](planning.md)):**
- Beat Groq baseline on macro-F1: ❌ (0.67 vs 0.86)
- Macro-F1 ≥ 0.70: ❌ (0.67)
- No class below F1 = 0.60: ❌ (`analysis` = 0.55)
- Dominant errors on the ambiguous `analysis`↔`hot_take` boundary: ✓ (5 of 9 errors)

To hit macro-F1 ≥ 0.70 with DistilBERT, this task likely needs ~500+ training examples
with `analysis` strongly upsampled, or a stronger base model (e.g., `roberta-base`).

---

## AI usage

Per [planning.md §7](planning.md). Specific instances:

1. **Annotation (pre-labeling all 538 comments).** Directed Claude (Opus 4.8) to assign one
   of `analysis` / `hot_take` / `reaction` to every cleaned comment using the planning.md
   definitions and decision rules, then `build_dataset.py` balanced them into `data/labeled.csv`.
   *Human step:* labels were reviewed by hand before training (the assignment requires
   reviewing every label). A first pre-labeling attempt used Groq `llama-3.3-70b` but was
   abandoned mid-run after it exhausted the daily token quota — the Groq budget was reserved
   for the graded zero-shot baseline.
2. **Dataset balancing.** Used a seeded script (`build_dataset.py`) — not a model — to keep
   all minority-class comments and down-sample surplus `reaction`, taking the set from
   ~78% reaction to a balanced 20/40/40.
3. **Failure-pattern analysis.** Pasted the 9 wrong predictions (text + true label +
   predicted label + confidence) to Claude and asked it to propose systematic error patterns.
   Each proposed pattern was verified by hand against the actual errors before inclusion in
   the evaluation report above. Unverified patterns were not reported.
