# Methodology

## 1. Research questions

1. **RQ1 — Platform differences**: Under identical prompts, how do 即梦, 可灵, and Seedream 4.0 differ on instruction following, visual quality, and commercial usability?
2. **RQ2 — Scene fit**: Is there a universal winner, or does the best platform depend on the business scene (e-commerce, social/poster, portrait)?
3. **RQ3 — Robustness**: How stable is the ranking under repeated generation? Is the between-platform difference larger than within-platform variance?
4. **RQ4 — Automation**: Can a VLM replace human judgment for first-pass QC? On which dimensions does it fail?

The pilot answers RQ1, RQ2, and RQ4 directionally. RQ3 needs the repeated-generation subset.

## 2. Scope and unit of analysis

The unit is a **production route**, not a bare model:

| Route | Type | What it represents |
|---|---|---|
| 即梦 App/Web | Product | What a content operator gets from the consumer product |
| 可灵 App/Web | Product | What a content operator gets from the consumer product |
| Seedream 4.0 API | API | What a team gets from an automated API pipeline |

This distinction matters: closed products may rewrite prompts, apply default styles, and post-process images. The project therefore measures **product-level delivery quality**, not a controlled model benchmark.

### Fixed generation settings

- Same prompt text across routes.
- Same aspect ratio per prompt: `1:1` for product/spatial prompts, `3:4` for poster/portrait prompts.
- Highest available resolution.
- Default style; no reference image; no manual editing; no cherry-picking.
- One generation per prompt in the pilot; repeat generations are reserved for the stability subset.

## 3. Prompt set

- 30 prompts: 24 main + 6 safety red-team.
- Pilot uses 12 main prompts: `E01–E04`, `T01–T04`, `H01–H04`.
- Six capability categories:

| Code | Category | Business scene | Example constraint |
|---|---|---|---|
| E | 商品/电商 | E-commerce | “两片柠檬”, “无品牌标志” |
| T | 中文文字/海报 | Social/poster | “今日开业”, “2026.11.08” |
| H | 人像/模特 | Portrait | “浅色毛衣”, “手部自然” |
| Q | 数量/空间 | Cross-scene | “左边三个红苹果” |
| Y | 风格/品牌 | Social/brand | “水墨与工笔结合” |
| C | 一致性/组图 | Cross-scene | “同一只橘猫，毛色一致” |

Each prompt has 5–8 **atomic, checkable constraints**. The prompt set and rubric are frozen before generation to avoid post-hoc selection.

## 4. Rubric

### Global dimensions (all images)

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| G1 指令遵循 | 完全跑偏 | 部分约束缺失 | 全部约束满足 |
| G2 视觉质量 | 明显畸形/伪影 | 可用但需修 | 无明显瑕疵 |
| G3 商业可用性 | 不可用 | 需明显返工 | 可直接交付 |

### Module dimensions (conditional)

| Dimension | When enabled | Scale |
|---|---|---|
| M1 文字准确率 | Text/poster prompts | 0–100% |
| M2 一致性 | Group/multi-panel prompts | 1–5 |
| M3 安全合规 | Safety red-team prompts | pass / fail / na |

### Composite metrics

```text
quality = 0.35 × G1 + 0.30 × G2 + 0.35 × G3
first_pass = (G2 ≥ 4) AND (G3 ≥ 4) AND (constraint_pass_rate ≥ 0.80)
constraint_pass_rate = satisfied_atomic_constraints / total_atomic_constraints
```

Atomic constraints are scored **before** holistic dimensions. This separates objective instruction following from subjective visual judgment.

## 5. Annotation protocol

- Human gold labels: 100% of pilot images.
- Blind: random IDs, EXIF stripped, platform watermarks cropped from blinded copies.
- VLM channel: DeepSeek Flash, two prompt variants (constraints-first and holistic-first).
- Human retest: 30% of images after 48 hours (planned).
- Adjudication: disagreements of ≥2 points or constraint disagreements go to a second pass.

### Reliability

- Human–VLM: exact agreement, adjacent agreement (±1), mean absolute error, Krippendorff's α (ordinal).
- Human–human: intra-rater retest (planned).
- Report α alongside percent agreement; high ±1 agreement can coexist with low α when scores are concentrated in a narrow range.

## 6. Statistical analysis

### Cluster bootstrap

Images within the same prompt are correlated. We resample **prompts**, not images:

```text
for b in 1..B:
    sample prompts with replacement
    compute mean quality over all images of sampled prompts
report 2.5th and 97.5th percentiles
```

### Omnibus and post-hoc tests

- Friedman test across the three routes (one mean per prompt per route).
- Wilcoxon signed-rank for pairwise comparisons.
- Holm correction for multiple comparisons.
- Effect size: median difference; report with p-values.

### Stability

For the stability subset:

- Within-platform standard deviation across repeats.
- Rank flip rate: share of prompts where the top platform changes across repeats.
- Compare within-platform variance to between-platform differences.

### Win rate

For each prompt, compare platform means; count wins (ties = 0.5). Report the share of prompts won and the number of prompts.

## 7. VLM calibration

- Model: `deepseek-flash` (vision-capable).
- Input: blinded, watermark-cropped image + prompt + atomic constraints + rubric.
- Output: JSON with constraint checks, G1/G2/G3, module scores, failure tags, confidence, rationale.
- Two variants:
  - Variant A: constraints first, then holistic scores.
  - Variant B: holistic impression first, then constraints.
- `thinking` disabled; temperature 0; JSON response format where supported.
- The VLM is a **second scoring channel**, not a second human annotator.

## 8. Bad Case analysis

Three parallel views:

1. Human failure tags (sparse in the pilot).
2. Atomic constraints marked as unmet.
3. Lowest-scoring images, even when all constraints are met.

The third view captures “constraint satisfied but not commercially usable” cases, which are the most useful for training and rule iteration.

## 9. Selection matrix

Base weights:

| Factor | Weight |
|---|---:|
| Quality | 50% |
| Cost | 15% |
| Latency | 15% |
| Controllability | 10% |
| Compliance | 10% |

For a specific business, adjust weights and run a sensitivity check (±10%). If the recommendation flips, report it rather than hiding it.

## 10. Limitations

See [`limitations.md`](limitations.md). The most important: 12 prompts cannot establish statistical significance; results are directional and version-specific.
