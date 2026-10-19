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
