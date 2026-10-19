<div align="center">

# AIGC Image Quality Ops

**Quality evaluation and data QC for AIGC image platforms**

Jimeng / Kling / Seedream 4.0 · atomic constraints · human labels · VLM calibration

[![CI](https://github.com/lhh737/aigc-image-quality-ops/actions/workflows/ci.yml/badge.svg)](https://github.com/lhh737/aigc-image-quality-ops/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Data](https://img.shields.io/badge/data-CC%20BY--NC%204.0-lightgrey?style=flat-square)](NOTICE.md)
[![Dashboard](https://img.shields.io/badge/dashboard-live-2a78d6?style=flat-square)](https://lhh737.github.io/aigc-image-quality-ops/dashboard/)

[中文](README.md) | [English](README.en.md)

</div>

---

## Overview

This repository documents a quality evaluation of three AIGC image routes. The pilot generates images from the same prompts on Jimeng, Kling, and Seedream 4.0, then applies watermark removal, blind IDs, human annotation, VLM-assisted scoring, and statistical analysis.

The evaluation asks three questions:

- Are the explicit constraints in the prompt satisfied?
- Does the image reach a deliverable visual and commercial quality?
- How far can a VLM be used for first-pass QC?

The pilot uses 12 prompts covering e-commerce, poster, and portrait scenes. Raw generated images are not included; prompts, annotations, analysis outputs, and reproduction scripts are.

- Live dashboard: <https://lhh737.github.io/aigc-image-quality-ops/dashboard/>
- Result summary: [docs/results.md](docs/results.md)

## Results

![Pilot results](docs/assets/results.png)

| Route | N | Quality | 95% CI | First-pass |
|---|---:|---:|---|---:|
| Jimeng | 12 | 4.51 | 4.38 – 4.65 | 91.7% |
| Seedream 4.0 | 12 | 4.29 | 4.03 – 4.54 | 75.0% |
| Kling | 12 | 4.20 | 3.76 – 4.56 | 66.7% |

- E-commerce: Jimeng 4.75; social/poster: Seedream 4.59; portrait: Kling 4.74.
- The overall difference is not significant (Friedman p=0.75). These results are directional, not a definitive ranking.
- Human–VLM Krippendorff's α is 0.14–0.20. The VLM is suitable for triage, not final acceptance.

## Pipeline

```text
Prompt + atomic constraints
        │
        ▼
Jimeng / Kling / Seedream 4.0
        │
        ▼
watermark crop · blind IDs · shuffle
        │
        ▼
human gold + VLM (two prompt variants)
        │
        ▼
bootstrap · Friedman · α · bad cases
        │
        ▼
static dashboard + result summary
```

## Method

| Part | Approach |
|---|---|
| Evaluation set | 30 prompts (12 in the pilot), 5–8 atomic constraints each |
| Rubric | G1 instruction following, G2 visual quality, G3 commercial usability; text/consistency/safety modules when applicable |
| Annotation | 36 human labels; watermark-cropped blind copies; DeepSeek Flash with two prompt variants |
| Statistics | Prompt-clustered bootstrap, Friedman, Wilcoxon–Holm, Krippendorff's α |
| Bad cases | Failure tags, unmet atomic constraints, lowest-scoring samples |

Details: [methodology](docs/methodology.md) · [rubric](docs/rubric.md) · [annotation SOP](docs/annotation_sop.md).

## Quick start

### View the results

The repository includes the data needed for analysis:

```bash
git clone https://github.com/lhh737/aigc-image-quality-ops.git
cd aigc-image-quality-ops
pip install -r requirements.txt

python -m src.pipeline.analyze --stage pilot --bootstrap 1000
python -m src.pipeline.build_dashboard
```

Open `dashboard/index.html`, or use the live dashboard.

### Full reproduction

Full reproduction requires generating images from `prompts/prompts_v1.csv` and setting API keys in `.env`:

```bash
cp .env.example .env
# fill in DASHSCOPE_API_KEY / ARK_API_KEY / DEEPSEEK_API_KEY

python -m src.providers.standardize_manual --platforms jimeng,kling --apply
python -m src.providers.manual_ingest --platforms jimeng,kling --stage pilot
python -m src.pipeline.validate --stage pilot
python -m src.pipeline.blind --stage pilot --crop-bottom-pct 0.05
python -m src.pipeline.vlm_judge --stage pilot --variant both
python -m src.pipeline.analyze --stage pilot --bootstrap 1000
python -m src.pipeline.build_dashboard
```

## Repository layout

| Path | Contents |
|---|---|
| `prompts/` | 30 prompts, atomic constraints, pilot list |
| `configs/` | Routes, models, parameters |
| `src/providers/` | Manual ingest, Seedream/Qwen adapters, file standardization |
| `src/pipeline/` | Validation, blinding, VLM scoring, analysis, dashboard |
| `tools/annotation/` | Local static annotation tool |
| `dashboard/` | Static dashboard and generated data |
| `data/` | Manifests, human labels, VLM scores, analysis |
| `docs/` | Method, rubric, SOP, results, limitations, video design |

## Docs

| Document | Contents |
|---|---|
| [docs/methodology.md](docs/methodology.md) | Evaluation design and statistics |
| [docs/rubric.md](docs/rubric.md) | Scoring dimensions and anchors |
| [docs/annotation_sop.md](docs/annotation_sop.md) | Annotation and retest workflow |
| [docs/results.md](docs/results.md) | Pilot results and bad cases |
| [docs/limitations.md](docs/limitations.md) | Scope and limitations |
| [docs/video_extension.md](docs/video_extension.md) | Video QC extension design |

## Data

**Included**: prompts, manifests, blind mapping, human labels, VLM scores, analysis outputs, dashboard data.

**Not included**: raw generated images, blinded images, API keys, VLM cache.

Raw images are excluded because of platform terms, image copyright, and privacy. Prompts, labels, and manifests are sufficient to audit the method; regenerating images requires the recorded model versions.

`data/manifests/blind_map.csv` maps `blind_id` back to route and run for analysis. The blinded images themselves are not included.

## Limitations

- 12-prompt pilot; the overall difference is not significant, so the conclusions are directional.
- Product-level evaluation: closed platforms rewrite prompts and post-process images; this is not a bare-model benchmark.
- Platform versions change; results correspond to the 2026-10-19 snapshot.
- One human annotator; the 48-hour retest is not complete. Human–VLM α is low.
- Repeated-generation stability has not been collected yet.

See [docs/limitations.md](docs/limitations.md) for details.

## License

- Code: [MIT](LICENSE)
- Evaluation data and report: [CC BY-NC 4.0](NOTICE.md)

Platform names and generated images belong to their respective owners. This is a non-commercial evaluation. See [NOTICE.md](NOTICE.md).
