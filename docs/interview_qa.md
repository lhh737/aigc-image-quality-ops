# Interview Q&A

## Q1. Why evaluate products/platforms instead of bare models?

Because the business buys a **delivery route**, not a checkpoint. Closed platforms rewrite prompts, apply default styles, and post-process images. A bare-model benchmark would miss the product layer that determines first-pass yield. The trade-off is that I cannot attribute every difference to the model; I state that as a limitation and separate product-level from model-level claims.

## Q2. Why atomic constraints before holistic scores?

Holistic 1–5 scores alone have low reliability, especially for aesthetics. Atomic constraints turn “did it follow the brief?” into a set of 0/1 checks: count, color, spatial relation, Chinese text, brand logo, material. This gives an objective backbone; G1–G3 then capture the overall impression. It also makes Bad Case analysis actionable: I can say exactly which constraint failed.

## Q3. Your overall p-value is 0.75. Can you still recommend 即梦?

Yes, but only as a **directional** recommendation, not a significant one. With 12 prompts, the confidence intervals overlap and Friedman p=0.75. The honest conclusion is: “即梦 has the highest mean and first-pass yield in this pilot, but the sample cannot establish a significant overall difference.” The more useful signal is scene-level: 即梦 wins e-commerce, Seedream wins social/poster, 可灵 wins portrait. I would not claim a universal winner.

## Q4. Why is Krippendorff's α so low when ±1 agreement is 94–97%?

Because α corrects for chance and is sensitive to the score distribution. Human and VLM scores are concentrated in 4–5, so many “agreements” are easy to get by chance. Exact agreement is 52.8–77.8%, and α is 0.14–0.20. The practical conclusion is: VLM is useful for triage and pre-annotation, but not for final acceptance. Reporting only ±1 would overstate automation readiness.

## Q5. Why does 可灵 have the highest constraint pass rate but the lowest quality?

Because constraints and visual quality are different constructs. 可灵 followed the explicit checklist (98.8%), but its product images looked less commercially usable: flat lighting, weak material rendering, less realistic product presentation. That is exactly why the rubric has separate G2/G3 dimensions and why “constraint satisfied” is not the same as “ship it”.

## Q6. How would you extend this to video QC?

Add temporal metrics: subject consistency across frames, background/lighting flicker, motion naturalness, text stability, and shot-language/narrative fit. Sample frames at scene cuts plus fixed intervals, annotate timecodes, and compare VLM frame-sequence judgments to human labels. The image rubric becomes the first-frame layer; the video layer adds temporal and narrative checks. See `docs/video_extension.md`.

## Q7. What would you do with 10× the budget?

- Expand to 100–200 prompts, stratified by scene and difficulty.
- Add 2–3 human annotators and compute human–human IAA, not just human–VLM.
- Add 3–5 repeats per prompt to estimate within-platform variance and rank stability.
- Add a second VLM and a position-bias test.
- Add cost/latency at scale and a proper selection matrix with sensitivity analysis.
- Pre-register the prompt set and analysis plan.

## Q8. What would you change in this pilot?

- Increase the number of prompts before making any overall ranking claim.
- Collect latency/credits for manual routes; the current comparison only has API latency.
- Add a second human annotator for human–human IAA.
- Use more failure tags during annotation; the current labels are sparse, so I relied on constraint failures and low scores.
- Add a dedicated “ratio compliance” check, because aspect-ratio mismatches were a real collection issue.

## Q9. How did you handle API quotas and data collection?

I used a hard quota guard (`src/quota.py`) that counts successful runs and refuses to exceed free-tier limits. I recorded model IDs, versions, parameters, latency, and failures in a manifest. For manual routes, I standardized platform-generated filenames, matched them to prompt IDs, selected the correct-aspect-ratio version, and preserved originals in `_originals/`. This is the unglamorous part of data operations, and it is where most quality problems appear.

## Q10. What did you learn about AI data quality operations?

Three things:

1. **Definitions beat models.** A clear atomic constraint and a stable anchor are worth more than a fancy judge.
2. **Collection discipline is part of quality.** Aspect ratio, watermark, filename, and model version can invalidate a comparison before any model is evaluated.
3. **Automation needs a boundary.** VLM is useful, but the α results show exactly where human judgment remains necessary.
