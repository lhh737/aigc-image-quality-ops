# Video QC Extension

This is a design for extending the image QC framework to **image-to-video / video generation quality inspection**. No video data is included in the pilot.

## 1. Why video QC

Video QC is not “image QC × N frames”. It adds temporal failure modes:

- subject identity drifts across frames;
- background and lighting flicker;
- motion is physically implausible;
- text on signs/logos changes or melts;
- shot language and narrative do not match the brief.

These map directly to video caption/acceptance roles: 画面内容、镜头语言、叙事逻辑、场景特征.

## 2. Prompt set (suggested)

| Code | Prompt type | What it tests |
|---|---|---|
| V01 | Product 360° rotation | Product identity, label stability, reflections |
| V02 | Person walking / turning | Face/body consistency, hands, gait |
| V03 | Camera pan across a scene | Background consistency, parallax, flicker |
| V04 | Text motion / sign reveal | Text stability, layout, readability |
| V05 | Multi-shot mini-story | Shot language, narrative logic, continuity |
| V06 | Safety red-team clip | Refusal, compliance, over-refusal |

## 3. Metrics

| Layer | Metric | How to measure |
|---|---|---|
| First frame | Prompt fidelity, visual quality | Same G1–G3 rubric on frame 0 |
| Temporal | Subject consistency | Human 1–5 + optional face/object embedding similarity |
| Temporal | Background/lighting consistency | Frame-to-frame difference; flicker detection |
| Motion | Motion naturalness | Human 1–5; physics/anatomy checklist |
| Text | Text stability | OCR/character accuracy per sampled frame |
| Shot | Shot language / narrative | Human 1–5 against a shot list |
| Product | Duration, resolution, watermark, cost, latency | API/manual metadata |

## 4. Sampling

- Sample frames at 0%, 25%, 50%, 75%, 100% + any detected scene cut.
- For text clips, sample every 0.5s in the text region.
- For consistency, compare the first frame to the last frame and to the midpoint.

## 5. Annotation protocol

- Watch the full clip once without pausing.
- Then pause at sampled frames and score.
- Score temporal consistency with the clip playing, not from stills alone.
- Record the timecode of each failure.
- Use the same failure taxonomy plus video-specific tags:
  - 主体漂移
  - 背景闪烁
  - 运动不自然
  - 文字抖动/变形
  - 镜头语言不符
  - 叙事断裂

## 6. VLM judge

- Feed the VLM a sequence of 4–8 frames, not a single frame.
- Ask for a timeline of failures with timecodes.
- Compare VLM labels to human labels; expect lower agreement on motion and narrative than on first-frame quality.
- Do not use VLM for final acceptance; use it for clip triage.

## 7. Deliverables

- 4–6 prompt video set × 2 platforms × 1–2 generations.
- Frame-level and clip-level scores.
- A one-page “video QC extension” section in the main report.
- A short demo: 4 clips, annotated timeline, pass/fail.

## 8. Job mapping

| Job requirement | Artifact |
|---|---|
| Caption/description acceptance | Shot-by-shot description rubric |
| 画面内容/镜头语言/叙事逻辑/场景特征 | Four-dimension video rubric |
| Boundary cases and adjudication | Timecoded failure cases |
| Training and mentoring | Annotation SOP + anchor clips |
| Rule iteration | Failure taxonomy + rule change log |
