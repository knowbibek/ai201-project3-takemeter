# Scraping r/soccer in Chrome — step by step

Goal: get ~250 raw r/soccer comments into a CSV **without copy-pasting one by one**, then
pre-label them with an LLM and review. No coding, no Reddit API key. Works because you're
scraping from **your own Chrome (residential IP)**, which Reddit doesn't block — unlike a
server.

We use **old.reddit.com** (not new reddit) because its HTML is simple and scrapers read it
cleanly.

---

## Tool: "Instant Data Scraper" (free Chrome extension)

### A. Install (1 min)
1. Open Chrome → go to the **Chrome Web Store**.
2. Search **"Instant Data Scraper"** (by webrobots.io). Click **Add to Chrome → Add extension**.
3. Pin it: click the puzzle-piece 🧩 icon in the toolbar → pin **Instant Data Scraper**.

### B. Open good threads (the source of variety)
You want a MIX of thread types so all three labels show up (see [planning.md §4](../planning.md)):

1. Go to **https://old.reddit.com/r/soccer/**.
2. In the search bar (top right), search and open a few of each, opening each in its own tab:
   - **"Post Match Thread"** → lots of `hot_take` + `analysis`
   - **"Match Thread"** → lots of `reaction`
   - **"Tactics"** or **"Daily Discussion"** → the scarce `analysis`
3. In each open thread: set the comment **sort to "top"** (dropdown near the top of comments),
   then scroll down and click **"load more comments"** a few times so ~50–100 comments are loaded.

### C. Scrape one thread (30 sec each)
1. With the thread page loaded, click the **Instant Data Scraper** 🧩 icon.
2. It auto-highlights the biggest repeating block. You want the one where the **comment text**
   shows up as a column. If it grabbed the wrong block, click **"Try another table"** until the
   comment bodies appear in the preview.
3. Click **"Download CSV"**. Name it `thread1.csv`, `thread2.csv`, etc.
4. Repeat B–C for ~5–8 threads until you have well over 250 rows total.

> If Instant Data Scraper's auto-detect is messy on a thread, skip that thread — match and
> post-match threads detect most cleanly.

### D. Merge + clean into one raw file
Put all the downloaded `threadN.csv` files into the repo's `data/` folder, then run:

```bash
python3 scripts/merge_raw.py --glob "data/thread*.csv" --out data/raw_comments.csv
```

This finds the comment-text column automatically, drops junk (deleted/removed/too-short/
duplicates/bot posts), and writes a clean single-column `text` file: `data/raw_comments.csv`.

---

## Alternative tool: Web Scraper (webscraper.io)
More reliable but more setup. Only switch to this if Instant Data Scraper keeps grabbing the
wrong block. Install the **Web Scraper** extension → open DevTools (F12) → "Web Scraper" tab →
Create sitemap → start URL = the thread → add a **Text** selector with CSS
`div.usertext-body div.md`, check **multiple** → Scrape → Export as CSV.

---

## Next: merge, pre-label, then REVIEW (this is the part you can't skip)
Scraping only gives raw text — you still need a `label` on each row.

```bash
# 1. clean + merge all the scraped exports
python3 scripts/merge_raw.py --glob "data/reddit*.csv" --out data/raw_comments.csv

# 2. an LLM (Claude) pre-labels every comment against the planning.md definitions,
#    then 3. combine batches + balance the classes into the final dataset
python3 scripts/build_dataset.py        # -> data/labeled.csv
```

Then open `data/labeled.csv` and **review every label by hand** (the brief requires it),
using [labeling_cheatsheet.md](labeling_cheatsheet.md) for the fast 3-question rule. Focus
your attention on the `analysis` and `hot_take` rows — those are the genuinely borderline
ones; the `reaction` rows are usually obvious. Jot tricky cases in the `notes` column (these
become your "3 hard cases" for planning.md).
