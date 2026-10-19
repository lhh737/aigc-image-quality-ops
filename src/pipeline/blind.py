"""Create blinded copies and the annotation manifest.

Usage:
    python -m src.pipeline.blind --stage pilot
    python -m src.pipeline.blind --stage main
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

import pandas as pd

from .. import config, utils

QWEN_MODELS = ["qwen-image-3.0", "qwen-image-2.1-pro"]


def stage_runs(stage: str) -> pd.DataFrame:
    runs = utils.load_runs()
    if runs.empty:
        return runs
    ok = runs[runs["success"].astype(str).str.lower().isin(["true", "1"])].copy()
    ok = ok[ok["image_path"].astype(str).str.len() > 0]
    main = ["jimeng", "kling", "seedream"]
    if stage == "pilot":
        return ok[ok["prompt_id"].isin(utils.PILOT_IDS) & ok["platform"].isin(main) & (ok["repeat"].astype(int) == 1)]
    if stage == "main":
        ids = [x for x in utils.prompt_map() if not x.startswith("R")]
        return ok[ok["prompt_id"].isin(ids) & ok["platform"].isin(main) & (ok["repeat"].astype(int) == 1)]
    if stage == "stability":
        return ok[ok["prompt_id"].isin(utils.STABILITY_IDS) & ok["platform"].isin(main) & ok["repeat"].astype(int).isin([1, 2, 3])]
    if stage == "safety":
        return ok[ok["prompt_id"].isin(utils.SAFETY_IDS) & ok["platform"].isin(main) & (ok["repeat"].astype(int) == 1)]
    if stage == "qwen":
        return ok[ok["prompt_id"].isin(utils.QWEN_IDS) & ok["platform"].isin(QWEN_MODELS) & (ok["repeat"].astype(int) == 1)]
    if stage == "all":
        return ok[~ok["platform"].astype(str).str.startswith("qwen-mt")]
    raise SystemExit(f"未知 stage: {stage}")


def blind_id_for(run_id: str, seed: int) -> str:
    digest = hashlib.sha1(f"{run_id}|{seed}".encode("utf-8")).hexdigest()
    return "B" + digest[:10].upper()


def main() -> int:
    parser = argparse.ArgumentParser(description="Blind images and build annotation manifest")
    parser.add_argument("--stage", default="pilot", choices=["pilot", "main", "stability", "safety", "qwen", "all"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-side", type=int, default=2048)
    parser.add_argument("--crop-bottom-pct", type=float, default=0.05,
                        help="crop bottom fraction to remove platform watermarks; 0 disables")
    args = parser.parse_args()

    config.ensure_dirs()
    prompts = utils.prompt_map()
    runs = stage_runs(args.stage)
    if runs.empty:
        print("没有可盲化的成功图片。先跑图并执行 validate。")
        return 1

    rows = []
    for _, row in runs.iterrows():
        src = config.ROOT / row["image_path"]
        if not src.exists():
            continue
        bid = blind_id_for(row["run_id"], args.seed)
        dst = config.BLINDED_DIR / f"{bid}.png"
        utils.strip_exif_copy(src, dst, max_side=args.max_side, crop_bottom_pct=args.crop_bottom_pct)
        rows.append({
            "blind_id": bid,
            "run_id": row["run_id"],
            "prompt_id": row["prompt_id"],
            "platform": row["platform"],
            "model": row["model"],
            "repeat": row["repeat"],
            "source_image": row["image_path"],
            "blind_image": str(dst.relative_to(config.ROOT)),
        })

    # Stable mapping, update existing
    new_map = pd.DataFrame(rows)
    if config.BLIND_MAP_CSV.exists():
        old = pd.read_csv(config.BLIND_MAP_CSV, dtype=str).fillna("")
        merged = pd.concat([old, new_map], ignore_index=True).drop_duplicates("blind_id", keep="last")
    else:
        merged = new_map
    merged.to_csv(config.BLIND_MAP_CSV, index=False, encoding="utf-8-sig")

    # Manifest for the annotation tool. No platform/model fields.
    items = []
    for row in rows:
        p = prompts[row["prompt_id"]]
        items.append({
            "blind_id": row["blind_id"],
            "prompt_id": row["prompt_id"],
            "prompt": p["prompt"],
            "checks": [x.strip() for x in p["key_checks"].split(";") if x.strip()],
            "aspect_ratio": p["aspect_ratio"],
            "category": p["category"],
            "image": f"../../data/blinded/{row['blind_id']}.png",
        })
    random.Random(args.seed).shuffle(items)
    config.ANNOTATION_MANIFEST_JS.parent.mkdir(parents=True, exist_ok=True)
    with open(config.ANNOTATION_MANIFEST_JS, "w", encoding="utf-8") as f:
        f.write("window.ANNOTATION_META = ")
        json.dump({"crop_bottom_pct": args.crop_bottom_pct, "stage": args.stage}, f, ensure_ascii=False)
        f.write(";\n")
        f.write("window.ANNOTATION_ITEMS = ")
        json.dump(items, f, ensure_ascii=False, indent=2)
        f.write(";\n")

    print(f"已盲化 {len(items)} 张；映射：{config.BLIND_MAP_CSV}")
    print(f"标注清单：{config.ANNOTATION_MANIFEST_JS}")
    print("打开 tools/annotation/index.html 开始标注。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
