# AIGC Image Quality Ops

> A business-oriented evaluation of AIGC image generation platforms: **即梦 / 可灵 / Seedream 4.0**.
> 从评测集、判定规则、人工金标、VLM 校准到 Bad Case 归因的最小闭环。

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/code-MIT-green.svg)](LICENSE)
[![Data: CC BY-NC 4.0](https://img.shields.io/badge/data-CC%20BY--NC%204.0-lightgrey.svg)](NOTICE.md)

**Live dashboard**: <https://lhh737.github.io/aigc-image-quality-ops/>

---

## Why this project

AIGC 评测岗位真正关心的不是“哪个模型跑分高”，而是：

- 如何把“好看/能用”拆成可检查的**原子约束**和评分维度；
- 如何做**双盲标注、抽检、仲裁、信度分析**；
- 如何用 **VLM 做初筛**，同时知道它在哪些维度不可靠；
- 如何从 Bad Case 反推**规则迭代和平台选型**。

本项目以电商商品图、社媒海报、人像为业务场景，对三条生产通路做同提示词实测，产出一套可复现的评测流水线、静态看板和 1–2 页评测摘要。

---

## Key findings (pilot: 12 prompts × 3 routes)

| 平台 | 综合质量 | 95% CI | 约束满足率 | 一次通过率 |
|---|---:|---|---:|---:|
| 即梦 | **4.51** | 4.38 – 4.65 | 97.2% | **91.7%** |
| Seedream 4.0 | 4.29 | 4.03 – 4.54 | 95.7% | 75.0% |
| 可灵 | 4.20 | 3.76 – 4.56 | **98.8%** | 66.7% |

- **没有全能赢家，只有场景赢家**：电商即梦 4.75、社媒/海报 Seedream 4.59、人像可灵 4.74。
- 总榜即梦领先，但 **Friedman p=0.75**，12 条 prompt 下差异不显著；这是方向性 pilot，不是“即梦显著更好”的结论。
- **约束满足 ≠ 商业可用**：可灵约束满足率最高（98.8%），综合质量却最低（4.20）。
- **VLM 不能替代人工**：精确一致率 52.8%–77.8%，Krippendorff's α 仅 0.14–0.20；适合初筛，不适合最终判定。

完整摘要：[`report/pilot_summary.md`](report/pilot_summary.md)

---

## Method

### 1. Evaluation set

- 30 prompts：24 主集 + 6 安全红队（pilot 使用其中 12 条主集）。
- 6 类能力：商品、海报、人像、空间/数量、风格、组图一致性。
- 每条 prompt 5–8 个**可判定的原子约束**，例如“左边三个红苹果”“中文标签‘晨光’”“无品牌标志”。
- 难度分层：easy / medium / hard；prompt 集在生成前冻结。

### 2. Rubric

| 层级 | 维度 | 评分 |
|---|---|---|
| 全局 | G1 指令遵循 | 1–5 |
| 全局 | G2 视觉质量 | 1–5 |
| 全局 | G3 商业可用性 | 1–5 |
| 模块 | M1 文字准确率 | 0–100% |
| 模块 | M2 一致性 | 1–5 |
| 模块 | M3 安全合规 | pass/fail/na |
| 客观 | 原子约束 | 每条 0/1 |

综合质量 = `0.35×G1 + 0.30×G2 + 0.35×G3`。
一次通过 = `G2≥4` 且 `G3≥4` 且 `约束满足率≥80%`。

### 3. Annotation

- 人工金标：36 张，100% 覆盖。
- 盲化：随机 ID、去 EXIF、裁掉底部平台水印。
- VLM 第二通道：DeepSeek Flash，双 prompt 变体（约束优先 / 整体优先）。
- 信度：Human–VLM 精确/±1 一致率、Krippendorff's α；人工 48h 重测（待完成）。
- 统计：按 prompt 聚类 bootstrap 95% CI、Friedman、Wilcoxon + Holm。

### 4. Bad Case

- 失败标签 + 原子约束未满足 + 最低分样本三条线。
- 归因到：指令遗漏、属性错误、空间错误、文字乱码、手部畸形、风格漂移、过度美化、安全违规。

---

## Results

### 场景差异

| 场景 | 即梦 | 可灵 | Seedream | 建议 |
|---|---:|---:|---:|---|
| 电商商品图 | **4.75** | 3.50 | 4.35 | 即梦优先 |
| 社媒/海报 | 4.28 | 4.35 | **4.59** | Seedream 优先 |
| 人像 | 4.50 | **4.74** | 3.93 | 可灵优先 |

按电商 40% / 社媒 35% / 人像 25% 加权：即梦 4.52 > Seedream 4.33 > 可灵 4.11。

### Human–VLM calibration

| 维度 | 完全一致 | ±1 | α |
|---|---:|---:|---:|
| G1 指令遵循 | 77.8% | 97.2% | 0.14 |
| G2 视觉质量 | 58.3% | 94.4% | 0.20 |
| G3 商业可用性 | 52.8% | 97.2% | 0.18 |

α 偏低说明 VLM 的排序信息不足，不能替代人工最终判定；±1 高一致率容易高估自动评测能力。

### 主要 Bad Case

| 平台 | Prompt | 质量 | 问题 |
|---|---|---:|---|
| 可灵 | E03 运动鞋 | 2.65 | 视觉质量/商业可用性低，但约束全满足 |
| 可灵 | E01 保温杯 | 3.00 | 商品图质感不足 |
| Seedream | H02 工匠 | 3.35 | 人像/手部/质感弱 |
| Seedream | H04 两位女性 | 3.65 | 缺两杯拿铁、缺拉花 |
| 可灵 | T04 科技海报 | 3.70 | 海报文字/整体质感弱 |

---

## Repo structure

```text
.
├─ README.md
├─ NOTICE.md
├─ LICENSE
├─ requirements.txt
├─ prompts/
│  ├─ prompts_v1.csv            # 30 prompts + atomic constraints
│  └─ pilot_12.txt              # pilot copy-paste list
├─ configs/platforms.yaml       # routes, models, params, quotas
├─ src/
│  ├─ providers/                # manual ingest, Seedream, Qwen, standardization
│  ├─ pipeline/                 # validate, blind, vlm_judge, analyze, dashboard
│  └─ quota.py                  # hard free-tier quota guard
├─ tools/annotation/index.html  # local annotation tool
├─ dashboard/
│  ├─ index.html                # static dashboard
│  └─ data.js                   # generated dashboard data
├─ data/
│  ├─ manifests/                # runs, manual metadata, rename map
│  ├─ annotations/              # human_r1.csv + vlm_scores.csv
│  └─ analysis/                 # summary.json + CSV exports
├─ report/pilot_summary.md      # 1–2 page pilot report
└─ docs/
   ├─ methodology.md
   ├─ rubric.md
   ├─ annotation_sop.md
   ├─ project_plan.md
   ├─ video_extension.md
   ├─ interview_qa.md
   └─ limitations.md
```

**Not included**: raw generated images (`data/raw/`), blinded images (`data/blinded/`), private mappings and VLM cache (`data/private/`). See [Data availability](#data-availability).

---

## Reproduce

### 1. Install

```bash
git clone https://github.com/lhh737/aigc-image-quality-ops.git
cd aigc-image-quality-ops
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configure

```dotenv
DASHSCOPE_API_KEY=...
ARK_API_KEY=...
ARK_SEEDREAM_MODEL=doubao-seedream-4-0-20260415
DEEPSEEK_API_KEY=...
DEEPSEEK_MODEL=deepseek-flash
```

### 3. Run the pipeline

```bash
# manual images standardized
python -m src.providers.standardize_manual --platforms jimeng,kling --apply

# ingest + validate
python -m src.providers.manual_ingest --platforms jimeng,kling --stage pilot
python -m src.pipeline.validate --stage pilot

# blind + annotation manifest
python -m src.pipeline.blind --stage pilot --crop-bottom-pct 0.05

# open tools/annotation/index.html, export human_r1.csv

# VLM judge
python -m src.pipeline.vlm_judge --stage pilot --variant both

# analysis + dashboard
python -m src.pipeline.analyze --stage pilot --bootstrap 1000
python -m src.pipeline.build_dashboard
```

Open `dashboard/index.html`. For a local server:

```bash
python -m http.server 8000
# http://localhost:8000/dashboard/
```

---

## Data availability

- **Included**: prompts, rubric, manifests, human annotations, VLM scores, analysis outputs, dashboard data, report, code.
- **Excluded**: raw generated images, blinded images, private blind mapping, API keys, VLM cache.
- Why: platform Terms of Service, image copyright, and privacy. The evaluation data is sufficient to audit the method; raw images can be regenerated from the prompts and platform versions recorded in `data/manifests/runs.csv`.
- Generated images remain subject to the respective platform terms. This project is a **non-commercial evaluation**.

---

## Limitations

- 12-prompt pilot; no statistically significant overall difference; conclusions are directional.
- Product-level evaluation: closed platforms rewrite prompts and apply post-processing; this is not a bare-model benchmark.
- Platform versions drift; results are a snapshot (2026-10-19).
- VLM calibration is weak (α 0.14–0.20); human gold remains the primary channel.
- 48h human retest and repeated-generation stability are not yet complete.
- Manual routes (即梦/可灵) do not expose latency/credits in the same way as the API route.

---

## Roadmap

- [ ] 48h human retest (11 images) for intra-rater reliability.
- [ ] 24 main prompts + 6 stability prompts × 3 + 6 safety prompts.
- [ ] Qwen-MT-Image translation QC side module (100 free images).
- [ ] Video QC extension: first-frame fidelity, temporal consistency, flicker, text stability.
- [ ] 6–8 page full report.

---

## License

- Code: [MIT](LICENSE).
- Evaluation data and report: [CC BY-NC 4.0](NOTICE.md).

## Contact

GitHub: [@lhh737](https://github.com/lhh737)
