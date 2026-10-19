"""Validate dataset coverage and image metadata.

Usage:
    python -m src.pipeline.validate --stage pilot
    python -m src.pipeline.validate --stage main
    python -m src.pipeline.validate --stage all
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .. import config, utils

MAIN_PLATFORMS = ["jimeng", "kling", "seedream"]
QWEN_MODELS = ["qwen-image-3.0", "qwen-image-2.1-pro"]


def expected_cells(stage: str) -> list[tuple[str, str, int]]:
    prompts = utils.prompt_map()
    main_ids = [x for x in prompts if not x.startswith("R")]
    if stage == "pilot":
        return [(p, plat, r) for p in utils.PILOT_IDS for plat in MAIN_PLATFORMS for r in [1]]
    if stage == "main":
        return [(p, plat, r) for p in main_ids for plat in MAIN_PLATFORMS for r in [1]]
    if stage == "stability":
        return [(p, plat, r) for p in utils.STABILITY_IDS for plat in MAIN_PLATFORMS for r in [1, 2, 3]]
    if stage == "safety":
        return [(p, plat, r) for p in utils.SAFETY_IDS for plat in MAIN_PLATFORMS for r in [1]]
    if stage == "qwen":
        return [(p, model, r) for p in utils.QWEN_IDS for model in QWEN_MODELS for r in [1]]
    if stage == "all":
        cells: list[tuple[str, str, int]] = []
        for s in ("main", "stability", "safety"):
            cells.extend(expected_cells(s))
        return sorted(set(cells))
    raise SystemExit(f"未知 stage: {stage}")


def ratio_ok(w: int, h: int, ratio: str) -> bool:
    if not w or not h:
        return False
    actual = w / h
    target = {"1:1": 1.0, "3:4": 0.75}.get(ratio, actual)
    return abs(actual - target) <= 0.03


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate dataset coverage")
    parser.add_argument("--stage", default="pilot", choices=["pilot", "main", "stability", "safety", "qwen", "all"])
    args = parser.parse_args()

    prompts = utils.prompt_map()
    runs = utils.load_runs()
    if runs.empty:
        print("runs.csv 为空：先跑图并执行 manual_ingest / API 生成脚本。")
        return 1

    runs["_ok"] = runs["success"].astype(str).str.lower().isin(["true", "1"])
    for idx, row in runs.iterrows():
        path = config.ROOT / row["image_path"] if row["image_path"] else None
        if row["_ok"] and (not path or not path.exists()):
            runs.at[idx, "_ok"] = False
            runs.at[idx, "failure_reason"] = "image file missing"

    ok = runs[runs["_ok"]]
    have = set(ok["run_id"])
    expected = expected_cells(args.stage)
    missing = [utils.run_id(p, plat, r) for p, plat, r in expected if utils.run_id(p, plat, r) not in have]
    attempted = set(runs["run_id"])
    failed = [utils.run_id(p, plat, r) for p, plat, r in expected if utils.run_id(p, plat, r) in attempted and utils.run_id(p, plat, r) not in have]

    print(f"stage={args.stage}  期望={len(expected)}  成功={len(expected)-len(missing)-len(failed)}  失败={len(failed)}  缺失={len(missing)}")
    if failed:
        print("\n失败格：")
        for rid in failed[:50]:
            reason = runs.loc[runs["run_id"] == rid, "failure_reason"].iloc[0]
            print(f"  {rid}: {str(reason)[:160]}")
    if missing:
        print("\n缺失格：")
        for i in range(0, len(missing), 8):
            print("  " + ", ".join(missing[i:i+8]))

    # Per-platform summary
    print("\n按平台：")
    for plat in sorted(set(runs["platform"])):
        sub = ok[ok["platform"] == plat]
        print(f"  {plat:24s} ok={len(sub):3d}")

    # Aspect ratio warnings
    bad_ratio = []
    for _, row in ok.iterrows():
        try:
            w, h = int(row["width"]), int(row["height"])
        except Exception:
            continue
        ratio = prompts.get(row["prompt_id"], {}).get("aspect_ratio", "")
        if ratio in {"1:1", "3:4"} and not ratio_ok(w, h, ratio):
            bad_ratio.append((row["run_id"], f"{w}x{h}", ratio))
    if bad_ratio:
        print(f"\n比例异常 {len(bad_ratio)} 条（警告，不阻塞）：")
        for rid, res, ratio in bad_ratio[:20]:
            print(f"  {rid}: {res} vs {ratio}")

    # Duplicates
    dup = runs[runs.duplicated("run_id", keep=False)]
    if not dup.empty:
        print(f"\n重复 run_id {len(dup)} 条：")
        print(dup[["run_id", "platform"]].to_string(index=False))

    return 0 if not missing and not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
