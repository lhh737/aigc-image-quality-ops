# Annotation SOP

## 1. Before you start

- Use Chrome/Edge.
- Open `tools/annotation/index.html`.
- Enter rater ID (`r1` for the pilot).
- Read `docs/rubric.md` once.
- Do not open `data/private/blind_map.csv` before annotating.

## 2. Per-image workflow

1. Read the prompt and the atomic constraints.
2. Check each atomic constraint (satisfied = checked).
3. Score G1 / G2 / G3 (1–5).
4. Fill module scores only when applicable:
   - M1 for text/poster prompts.
   - M2 for group/multi-panel prompts.
   - M3 for safety prompts.
5. Add failure tags for clear defects.
6. Add a short note for boundary cases.
7. Click “下一条”.

Aim for 60–90 seconds per image. Do not spend 5 minutes on one image; consistency matters more than perfection.

## 3. Scoring discipline

- Score the delivered image, not the prompt.
- Constraints first, holistic scores second.
- If the image is beautiful but ignores the prompt, G1 must be low.
- If the image satisfies every constraint but looks cheap, G3 must be low.
- Use the full 1–5 range; do not cluster everything at 4–5.
- If unsure between two scores, choose the lower one and explain in notes.

## 4. Fatigue control

- Annotate in blocks of 20–30 minutes.
- Take a 5-minute break every 30 minutes.
- Do not annotate more than 2 hours in one day.
- If you notice drift, re-read the anchors.

## 5. Export

Click “导出 CSV”. Save as:

```text
data/annotations/human_r1.csv
```

Do not edit the CSV by hand unless you document the change.

## 6. 重测（48h 或短期一致性）

严格口径是至少间隔 48 小时。也可以先做一次短期重测，但报告里要写清楚间隔；`analyze.py` 会记录 `interval_hours`，并在不足 48 小时时标注说明。

1. 生成分层重测子集：

```bash
python -m src.pipeline.make_retest_manifest
```

2. 打开 `tools/annotation/index_retest.html`（不是 `index.html`）。
3. rater ID 用 `r1_retest`。
4. 标 11 张（36 张的 30%）。
5. 导出为：

```text
data/annotations/human_r1_retest.csv
```

6. 不要先看 `human_r1.csv` 或第一轮的分数；重测工具使用独立的 localStorage，不会显示第一轮评分。
7. 分析时，`human_retest` 会单独报告完全一致、±1 和 MAE，并把重测文件排除在主榜之外。

## 7. Adjudication

- Differences of ≥2 points on G1–G3, or disagreements on atomic constraints, go to a second pass.
- A second annotator (if available) resolves independently; otherwise the first annotator re-checks after 24 hours.
- Record the final label and the reason in the notes.

## 8. Common mistakes

| Mistake | Fix |
|---|---|
| Scoring the prompt instead of the image | Look at the image first; then compare to the prompt |
| Giving 4–5 to everything | Use the anchors; a 5 means “ship it” |
| Ignoring text errors | Zoom in and count characters |
| Penalizing style when no style was requested | G3 is about business fit, not personal taste |
| Marking constraints without checking | Check each constraint explicitly |
| Skipping notes on boundary cases | Write one sentence; it becomes a training case |

## 9. What the analysis needs

- All G1/G2/G3 values.
- Atomic constraint checks for every image.
- Failure tags where applicable.
- Notes for any score ≤2 or any constraint disagreement.
