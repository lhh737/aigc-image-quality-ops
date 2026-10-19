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

## 6. 48-hour retest

- Wait at least 48 hours.
- Re-open the tool.
- Re-score about 30% of images (11 for the 36-image pilot).
- Export as:

```text
data/annotations/human_r1_retest.csv
```

This measures intra-rater reliability. Do not look at the first-pass scores before retesting.

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
