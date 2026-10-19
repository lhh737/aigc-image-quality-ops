# Project Plan

## 1. Business context

A content/e-commerce team needs to choose an AIGC image route and run pre-launch quality checks. The decision is not “which model has the highest benchmark score”; it is:

- Which route delivers the highest **first-pass yield** for our scenes?
- Where does it fail, and can we catch failures before delivery?
- Can a VLM reduce human QC cost without hiding errors?

## 2. Scope

### Pilot (completed)

- 12 prompts × 3 routes × 1 generation = 36 images.
- Human gold labels + VLM double-variant scoring.
- Analysis, dashboard, 1–2 page report.

### Main set (planned)

- 24 main prompts × 3 routes.
- 6 stability prompts × 3 repeats.
- 6 safety red-team prompts.
- 42 images per route (24 + 12 + 6).

### Side experiments

- Qwen-Image-3.0 and Qwen-Image-2.1-Pro: 10 prompts each (free-tier limits).
- Qwen-MT-Image: 12 Chinese posters × EN/JA translation QC (optional).
- Video QC extension: design only; no video data yet.

## 3. Routes and parameters

| Route | Type | Model/version | Parameters |
|---|---|---|---|
| 即梦 | Product | Platform default; record displayed version | Text-to-image; highest resolution; default style; no reference; no edit |
| 可灵 | Product | Kling Image 3.0/O1; record displayed version | Text-to-image; 1K/2K; default style; no reference; no edit |
| Seedream 4.0 | API | `doubao-seedream-4-0-20260415` | 1:1 `2048x2048`; 3:4 `1728x2304`; watermark false; sequential disabled |
| Qwen-Image-3.0 | API | `qwen-image-3.0` | 10 free images; 1024×1024 / 1152×1536 |
| Qwen-Image-2.1-Pro | API | `qwen-image-2.1-pro` | 10 free images; same prompts |
| Qwen-MT-Image | API | `qwen-mt-image-2.0` | Translation only; `source_lang=zh`, `target_lang=en/ja` |

### Fixed settings

- Same prompt text and aspect ratio per prompt across routes.
- Highest available resolution.
- Default style; no reference image; no editing; no cherry-picking.
- Record platform version, date, latency, credits, moderation, prompt-enhancement state.

## 4. Prompt design

- 24 main prompts, 6 categories × 4:
  - 商品/电商
  - 中文文字/海报
  - 人像/模特
  - 数量/空间
  - 风格/品牌
  - 一致性/组图
- 6 safety prompts: public figure, IP character, violence, stereotype, medical misinformation, minor endorsement.
- Each prompt: 5–8 atomic constraints, 1 easy / 2 medium / 1 hard per category.
- Prompt set frozen before generation; hash stored.

## 5. Annotation

- Human gold: 100%.
- Blind: random IDs, EXIF stripped, watermarks cropped from blinded copies.
- Human retest: 30% after 48 hours.
- VLM: DeepSeek Flash, two prompt variants.
- Adjudication: disagreements ≥2 points or constraint disagreements.

## 6. Analysis

- Cluster bootstrap by prompt (95% CI).
- Friedman + Wilcoxon/Holm.
- Constraint pass rate, first-pass yield, quality score.
- Human–VLM exact/±1 agreement, Krippendorff's α.
- Bad Case taxonomy and low-score cases.
- Scene-weighted selection matrix (e-commerce 40 / social 35 / portrait 25) with sensitivity check.

## 7. Deliverables

- Reproducible Python pipeline.
- Prompt set and rubric.
- Human and VLM annotations.
- Analysis outputs and static dashboard.
- 6–8 page report + 1-page summary.
- Interview notes and resume bullets (not part of the public repo).

## 8. Timeline

| Phase | Work |
|---|---|
| D1 | Scope, routes, prompt set v1, rubric v0.1 |
| D2 | Pipeline, annotation tool, pilot |
| D3 | 36-image pilot, ingest, blind |
| D4–D5 | Human annotation, VLM scoring |
| D6 | Analysis, dashboard, report |
| D7+ | 24-prompt main set, stability, safety, video design |

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Platform version drift | Record date/version; label results as a snapshot |
| Free-tier quotas | Hard quota guard; prioritize the 72-image main comparison |
| Single human annotator | 48h retest; VLM as a second channel; report limitations |
| Subjective aesthetics | Atomic constraints + anchors + calibration |
| VLM overconfidence | Calibrate against human; report α; use only for triage |
| Image ToS/copyright | Do not publish raw images; publish prompts, labels, aggregates |

## 10. Definition of done (pilot)

- 36/36 images, 36/36 human labels, 72 VLM scores.
- Analysis + dashboard + report.
- Limitations documented.
- Repo public and reproducible.
