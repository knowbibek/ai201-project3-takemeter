# TakeMeter — Planning

A fine-tuned text classifier that scores **discourse quality** on r/soccer during the
2026 FIFA World Cup. This document is the spec: it locks the design decisions before any
data is collected or any model is trained.

---

## 1. Community

**Chosen community: [r/soccer](https://www.reddit.com/r/soccer/)**, sampled during the
2026 FIFA World Cup (June–July 2026, hosted across the USA, Canada, and Mexico).

**Why this community.** r/soccer is one of the largest, most active sports communities on
Reddit, and a World Cup is its peak: match threads, post-match threads, and tactics
threads generate tens of thousands of comments per fixture. Crucially, the *quality* of
those comments varies enormously within a single thread — the same goal produces a
keyboard-smash celebration, a confident one-line verdict on a player's career, and a
paragraph breaking down why the defensive line got caught. That variance is exactly what a
discourse-quality classifier needs: if every comment looked the same, there would be
nothing to learn.

**Why it's a good fit for classification.** The community has a *native* vocabulary for
discourse quality. Regulars already distinguish "analysis" (the tactics crowd, often
upvoted to the top of post-match threads) from "hot takes" (bold one-liners that spark
arguments) from "reactions" (the live emotional churn of a match thread). Because the
distinction is real to participants, the labels are grounded in community norms rather than
imposed from outside — which is the difference between a model that learns a real signal
and one that learns my personal taste.

---

## 2. Labels

Three mutually exclusive labels. The ordering below is the **decision priority** used
during annotation: check `analysis` first, then `hot_take`, then default to `reaction`.

### `analysis`
> A comment that makes a **structured argument backed by specific, verifiable evidence** —
> statistics, a tactical observation, a historical comparison, or a causal explanation that
> would still stand if you stripped the opinion away.

- *"Spain are controlling this because Rodri drops between the center-backs, which turns it
  into a 3-v-2 in the first phase and lets both fullbacks push up. England's front two
  can't cover all three, so Spain always have a free man to progress through."*
- *"People blaming the keeper are wrong — he's screened by his own defender until the ball
  is already past him. Watch the replay: the center-back steps out and opens the lane, the
  keeper never had a sightline."*

### `hot_take`
> A **bold, confident opinion stated as a verdict without genuine supporting reasoning** —
> it asserts rather than argues. It may include a decorative stat or name-drop, but the
> evidence is cherry-picked or there to sound credible, not to actually reason.

- *"Mbappé is the most overrated player of his generation, full stop."*
- *"England will never win anything as long as this manager is in charge. Cope all you
  want."*

### `reaction`
> An **immediate emotional response to a moment** — a celebration, groan, joke, or vibe
> check, with little to no argument. The comment is *expressing a feeling*, not making a
> claim about the game.

- *"NOOOO HOW DID HE MISS THAT 😭😭 I can't watch the rest of this"*
- *"scenes. absolute scenes. my voice is gone"*

**Distribution target.** At least ~20% per label (per the brief's guidance). Match threads
skew heavily toward `reaction`, so I will deliberately oversample tactics and post-match
threads to keep `analysis` and `hot_take` above the floor. See §4.

---

## 3. Hard edge cases

### Primary edge case: the **one-stat hot take** (`analysis` vs `hot_take`)
A comment cites a single number but uses it as ammunition for a pre-formed verdict rather
than as part of an argument.

> *"Mbappé is washed — 1 goal in his last 4 knockout games."*

**Decision rule.** If removing the opinion framing leaves evidence that genuinely *supports
and explains* the claim, label it `analysis`. If the evidence is a lone cherry-picked stat
that merely decorates the verdict — selected for effect, not reasoning — label it
`hot_take`. The example above → **`hot_take`** (one selected stat, accusatory framing, no
mechanism explained).

### Secondary edge case: the **emotional verdict** (`hot_take` vs `reaction`)
A comment is emotionally charged *and* makes a claim about the game.

> *"This is the worst defending I have EVER seen, they should all be dropped 🤬"*

**Decision rule.** If the comment's core is a *claim/judgment* ("they should be dropped"),
label `hot_take`. If the core is a *feeling* with the judgment as throwaway venting, label
`reaction`. Tie-breaker: would the comment still make sense as a standalone opinion with
the emoji and caps removed? If yes → `hot_take`; if it collapses into pure noise →
`reaction`. The example above → **`hot_take`** (survives as a standalone opinion).

### Tertiary edge case: **banter / jokes**
r/soccer is famous for jokes that fit none of the three labels cleanly. **Decision: jokes
are folded into `reaction`**, since a joke is an immediate non-argumentative response to a
moment. This keeps the taxonomy at 3 labels and avoids a catch-all "other" bucket. If
jokes turn out to exceed ~15% of the data during the read-through, I will revisit adding a
4th `banter` label (noted in AI Tool Plan as a label-stress-test trigger).

### Hard cases actually encountered during annotation
(Real comments from the dataset; see README for fuller write-ups.)
1. *"Ronaldo hasn't scored a non-penalty goal in a major competition since June 19, 2021."*
   — a lone verifiable stat used as an implied verdict, no mechanism → **`hot_take`**.
2. *"We can literally access the pass maps after the game. This just sounds like a player
   being bitter that they've gotten found out to be a side pass merchant."* — snarky, but
   grounds the claim in verifiable evidence (pass maps) → **`analysis`**.
3. *"More points than in the last 3 world cups."* — a true factoid with no argument, in a
   celebration thread → **`reaction`** (not `analysis`).

---

## 4. Data collection plan

**Source.** Comments (not post titles — titles on r/soccer are mostly match scores and
article links, which carry no discourse) pulled from r/soccer via the official Reddit API
using `praw` with a free "script" OAuth app. Collector lives at
[scripts/collect_reddit.py](scripts/collect_reddit.py).

**Sampling strategy to hit the distribution target:**
- **Match threads** → rich source of `reaction`. Pull top + new comments during live games.
- **Post-match threads** → mix of `hot_take` and `analysis`. Top-sorted comments here are
  often the upvoted tactical breakdowns.
- **Tactics / "Daily Discussion" / dedicated analysis threads** → the densest source of
  `analysis`, which is the scarcest label.

**Target counts.** ~250 raw comments collected (buffer above the 200 minimum to allow
discarding off-topic/removed/non-English/duplicate items), aiming for a labeled set of
**≥200** split roughly **~35% reaction / ~35% hot_take / ~30% analysis** — every class
comfortably above the 20% floor.

**If a label is underrepresented after 200 examples** (most likely `analysis`): targeted
top-up collection — pull more comments specifically from tactics and post-match threads,
sorted by `top`, and filter for length (analysis comments are longer). I will *not*
synthesize examples; if `analysis` cannot reach 20% from real data, I'll document that as a
finding about the community rather than fake the distribution.

**Splits.** Stratified by label into **train (70%) / validation (15%) / test (15%)** with a
fixed random seed. Stratification matters here because the classes are imbalanced and the
test set is small — a non-stratified split could leave a class with almost no test examples.

---

## 5. Evaluation metrics

Accuracy alone is insufficient because the classes are imbalanced (~35/35/30) and a lazy
model could score ~35% by always predicting the majority class while being useless. The
full metric set:

| Metric | Why it's needed for *this* task |
|--------|--------------------------------|
| **Overall accuracy** | Headline number; compared head-to-head against the Groq baseline. |
| **Per-class precision, recall, F1** | The whole point is distinguishing classes. F1 per class catches a model that quietly ignores the scarce `analysis` class even at decent overall accuracy. |
| **Macro-F1** | Single summary that weights all three classes equally, so the rare class can't be hidden by the common ones. This is my **primary** comparison metric. |
| **Confusion matrix** | Shows *which* pairs get confused. I expect the `analysis`↔`hot_take` boundary (the one-stat edge case) to be the dominant confusion — the matrix confirms or refutes that. |

**Both** the fine-tuned DistilBERT and the Groq `llama-3.3-70b-versatile` zero-shot baseline
are scored on the **same held-out test set** with these same metrics.

---

## 6. Definition of success

- **Minimum bar (project works):** fine-tuned model beats the Groq zero-shot baseline on
  **macro-F1** on the test set. If fine-tuning doesn't beat a no-training baseline, the
  exercise didn't add value and that itself is the finding to report honestly.
- **"Good enough for a real community tool":** **macro-F1 ≥ 0.70** with **no single class
  below 0.60 F1**, and the dominant errors concentrated on the genuinely ambiguous
  `analysis`↔`hot_take` boundary (i.e., the model fails where humans also hesitate, not on
  easy cases).
- **Suspicious-if:** test accuracy > 0.95 on this subjective task would trigger a
  leakage/over-easy-labels audit (dedup check between splits, re-read of "too clean"
  examples), per the brief's warning.

These thresholds are deliberately concrete so that at the end I can say objectively "hit"
or "missed" rather than "seems good."

---

## 7. AI Tool Plan

This project generates little code, so AI assistance is concentrated at three specific
points. An explicit decision is recorded for each.

### Label stress-testing — **YES, before annotating**
Feed the §2 definitions and §3 edge cases to an LLM (Claude) and ask it to generate 8–10
comments engineered to sit *on* the `analysis`↔`hot_take` and `hot_take`↔`reaction`
boundaries. If I can't classify the generated borderline comments cleanly with my own
decision rules, the definitions are too loose and get tightened **before** I touch the 200
real examples. These synthetic comments are for *definition testing only* — they never
enter the training set.

### Annotation assistance — **YES, as pre-label + human review**
I will use an LLM to **pre-label** each collected comment, then review and correct every
single one myself (the human label is final). This speeds annotation without outsourcing
judgment. **Disclosure tracking:** the dataset CSV carries a `pre_label` column (the LLM
guess) alongside the final human `label` column, plus a `corrected` boolean, so the
README/AI-usage section can report exactly how often I overrode the model and which
boundaries it struggled with. This doubles as cheap inter-annotator-style signal.

### Failure analysis — **YES, with manual verification**
After evaluation, I'll hand the list of the fine-tuned model's wrong predictions (text +
true label + predicted label + confidence) to an LLM and ask it to propose **systematic
error patterns** (e.g., "misclassifies short sarcastic comments as analysis," "confuses
one-stat hot takes for analysis"). I will then **verify each proposed pattern by hand**
against the actual errors before putting it in the evaluation report — the AI proposes
hypotheses, I confirm them against the data. Unverified patterns don't get reported.

---

## Status / next steps
- [x] M1 — community + labels locked
- [x] M2 — this planning.md
- [x] M3 — collect ~250 comments → annotate ≥200 → stratified train/val/test split
- [x] M4 — fine-tune `distilbert-base-uncased` on Colab (H100); macro-F1 = 0.67
- [x] M5 — Groq zero-shot baseline (llama-3.3-70b-versatile); macro-F1 = 0.86
- [x] M6 — evaluation report complete (README); fine-tuned did not beat baseline
