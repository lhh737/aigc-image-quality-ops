# Limitations

- **Small sample**: 12 prompts per route in the pilot. Friedman p=0.75; the overall ranking is directional, not statistically significant.
- **Product-level evaluation**: closed platforms rewrite prompts, apply default styles, and post-process. Differences are not attributable to the bare model alone.
- **Version drift**: platform versions change. Results are a snapshot from 2026-10-19; model IDs and dates are recorded in the manifests.
- **Single human annotator**: no human–human IAA in the pilot. A 30% 48-hour retest is planned; until then, human reliability is not fully quantified.
- **VLM calibration is weak**: Krippendorff's α 0.14–0.20. The VLM is a triage channel, not a replacement for human acceptance.
- **No repeated generations**: the stability subset is planned but not complete. Rank stability under repeated generation is unknown.
- **Manual latency/credits missing**: 即梦/可灵 are manual routes; latency and credit cost are not comparable to the Seedream API route.
- **Scene imbalance**: the pilot has four prompts per category; some scene estimates rest on a small number of prompts.
- **Watermark cropping**: blinded copies crop the bottom ~9.75% to remove platform watermarks. This slightly changes composition; originals are preserved privately.
- **No raw images in the public repo**: platform ToS, copyright, and privacy. Prompts, labels, manifests, and aggregates are included so the method can be audited.
- **Safety red-team not run in the pilot**: the six safety prompts are defined but not yet evaluated. No harmful images are published.
- **Qwen side experiment is VLM-only**: Qwen-Image-3.0/2.1-Pro have 10 images each and no human gold labels; their results are a preview, not a main leaderboard.
