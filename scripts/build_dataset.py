"""
Build the final balanced labeled.csv from both scrape batches.

Both batches were pre-labeled by Claude (Opus 4.8) against the planning.md definitions.
Batch 1 (raw_comments.csv, 267) was celebration/banter-heavy -> mostly reaction.
Batch 2 (raw_new_dedup.csv, 271) targeted post-match/tactics/debate threads -> rich in
analysis and hot_take.

Combined the classes are still reaction-heavy, so we keep EVERY analysis + hot_take and
DOWN-SAMPLE the surplus reaction to a target total, yielding a dataset where no class
exceeds ~70% and each clears the ~20% floor (planning.md §4). The reaction down-sampling is
a deliberate curation choice (we had a surplus) and is disclosed in the README.

Writes data/labeled.csv — the balanced dataset (text, label, notes).
"""
import csv
import random

EXPAND = {"a": "analysis", "h": "hot_take", "r": "reaction"}
TARGET_TOTAL = 200          # final dataset size
SEED = 42

# a=analysis h=hot_take r=reaction, paired by row order with each raw file.
ORIG_CHUNKS = [
    "rrrrrrrrrr", "rrrrrrrrrr", "rrrrhrrrrr", "rhrrrrrrhr", "rrrhharhha",
    "aaharrahhh", "aahaarrrrr", "arrrrrrrrr", "rrrrrrrhrr", "rrrrrrrrrr",
    "rrrrrrrarr", "hhrrrarrrr", "rhrrrrrrrr", "rrrarrrrrr", "rrrrhrrhrr",
    "rrrrrrrrrr", "rrrrrrrrrr", "hrrrrarhrr", "rrrrrrrrrr", "rrrrrrrhrr",
    "hrrrrrrrrr", "rrrrrrrrrr", "rrrrrrrhrr", "rrrrrrrrrr", "rhrhrrrrrr",
    "rrrrrrrrrr", "rrrrrrr",
]
NEW_CHUNKS = [
    "rarhrrrrra", "rrrrrrrrrr", "rrrrrrrrrr", "rrrrrrrrrr", "hrahrarhra",
    "rrrrrrrhah", "rrrrrhrhhr", "rrrrrrhrrr", "hrrrrrrrhr", "rrrrhhrarh",
    "rarhrarrhr", "rrrarrrrhr", "arharhrarr", "rrahaarrrr", "rrrhrrrhhr",
    "rhrhrrarrh", "hhrrrhhhrh", "rrrrrrrrrr", "arhrhrhrhr", "hrhhrrrrhr",
    "hraaarrhra", "hhrarhrhah", "rrhhhrrrhr", "rrrrrrrarr", "rrrrrhrrrr",
    "rrrrarrrrr", "rrrrrhrrrrr",
]


def load(path, chunks):
    code = "".join(chunks)
    with open(path, newline="", encoding="utf-8") as f:
        texts = [r["text"] for r in csv.DictReader(f) if (r.get("text") or "").strip()]
    assert len(texts) == len(code), f"{path}: {len(texts)} texts vs {len(code)} labels"
    return [{"text": t, "label": EXPAND[code[i]], "notes": ""} for i, t in enumerate(texts)]


def main():
    rows = load("data/raw_comments.csv", ORIG_CHUNKS) + load("data/raw_new_dedup.csv", NEW_CHUNKS)

    rng = random.Random(SEED)
    keep = [r for r in rows if r["label"] in ("analysis", "hot_take")]
    reactions = [r for r in rows if r["label"] == "reaction"]
    n_react = max(0, TARGET_TOTAL - len(keep))
    rng.shuffle(reactions)
    final = keep + reactions[:n_react]
    rng.shuffle(final)

    write("data/labeled.csv", final)

    from collections import Counter
    for name, data in [("FULL", rows), ("BALANCED labeled.csv", final)]:
        dist = Counter(r["label"] for r in data)
        n = len(data)
        print(f"\n{name}: {n} rows")
        for lbl in ("analysis", "hot_take", "reaction"):
            print(f"  {lbl:9} {dist[lbl]:3}  ({100*dist[lbl]/n:.0f}%)")


def write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["text", "label", "notes"])
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
