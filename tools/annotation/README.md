# Annotation tool

1. Generate a blinded manifest:

```bash
python -m src.pipeline.blind --stage pilot --crop-bottom-pct 0.05
```

2. Open `index.html` in Chrome/Edge.
3. Enter a rater ID, score each image, export CSV.

`manifest.js` is generated locally and is gitignored because it points at
private blinded images. The tool itself is intentionally static: no server,
no external dependencies, no data leaves the browser.

Export format:

```text
data/annotations/human_<rater>.csv
```

## Retest subset

Generate a stratified retest subset (11 images by default):

```bash
python -m src.pipeline.make_retest_manifest
```

Open `index_retest.html` instead of `index.html`, enter a separate rater ID
(for example `r1_retest`), and score the 11 images. Export as:

```text
data/annotations/human_r1_retest.csv
```

The retest tool uses its own localStorage key, so the first-pass scores are not
visible while retesting. `analyze.py` excludes retest files from the main
leaderboard and reports retest agreement separately.
