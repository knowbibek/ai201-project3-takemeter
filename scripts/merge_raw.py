"""
Merge + clean the CSVs exported by a Chrome scraper (Instant Data Scraper / Web Scraper)
into a single clean `data/raw_comments.csv` with one `text` column.

The scraper's column names vary, so this auto-detects the column most likely to hold
comment bodies (the one with the longest average text), then filters out junk.

Usage:
    python3 scripts/merge_raw.py --glob "data/thread*.csv" --out data/raw_comments.csv
"""
import argparse
import csv
import glob as globmod
import re

URL_RE = re.compile(r"https?://\S+")
WS_RE = re.compile(r"\s+")
BOT_HINTS = ("i am a bot", "this submission has been removed", "your post was removed")

# Comment-body column names produced by the Chrome scrapers, in priority order.
KNOWN_TEXT_COLS = ("py-0", "tablescraper-selected-row")

# Substrings that mark a value as scraper junk rather than a real comment.
JUNK_SUBSTR = ("SML.load(", "[object Object]", "styles.redditmedia.com")
# Non-comment UI / mod boilerplate to drop outright.
JUNK_EXACT = {
    "more replies", "moderator announcement", "mirrors / alternative angles",
    "reply", "share", "report", "save",
}


def clean(text):
    text = URL_RE.sub("", text or "")
    text = WS_RE.sub(" ", text).strip()
    return text


def usable(t):
    if not t:
        return False
    low = t.lower()
    if t in ("[removed]", "[deleted]") or low in JUNK_EXACT:
        return False
    if any(h in low for h in BOT_HINTS) or any(j in t for j in JUNK_SUBSTR):
        return False
    n = len(t)
    return 20 <= n <= 1000


def pick_text_column(fieldnames):
    """Use a known comment-text column if present; otherwise None (skip the file)."""
    for col in KNOWN_TEXT_COLS:
        if col in (fieldnames or []):
            return col
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default="data/thread*.csv", help="glob for scraper CSVs")
    ap.add_argument("--out", default="data/raw_comments.csv")
    args = ap.parse_args()

    files = sorted(globmod.glob(args.glob))
    if not files:
        raise SystemExit(f"No files matched {args.glob!r}. Download some thread CSVs into data/ first.")

    seen = set()
    out_rows = []
    for path in files:
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if not rows:
                print(f"  {path}: empty, skipped")
                continue
            col = pick_text_column(reader.fieldnames)
            if col is None:
                print(f"  {path}: no known comment-text column -> SKIPPED (likely off-topic/contaminated scrape)")
                continue
            kept = 0
            for r in rows:
                t = clean(r.get(col, ""))
                if not usable(t):
                    continue
                key = t.lower()[:120]
                if key in seen:
                    continue
                seen.add(key)
                out_rows.append(t)
                kept += 1
            print(f"  {path}: text column = {col!r}, kept {kept}")

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["text"])
        for t in out_rows:
            w.writerow([t])

    print(f"\nWrote {len(out_rows)} unique comments to {args.out}")
    if len(out_rows) < 250:
        print("Tip: scrape a few more threads to comfortably clear the 200-labeled minimum after review.")


if __name__ == "__main__":
    main()
