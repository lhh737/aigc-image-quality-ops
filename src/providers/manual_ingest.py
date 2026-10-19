"""Ingest manually generated 即梦/可灵 images into the unified runs manifest.

Usage:
    python -m src.providers.manual_ingest --platforms jimeng,kling --stage pilot
    python -m src.providers.manual_ingest --platforms jimeng --stage stability
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

from .. import config, utils

FAIL_RE = re.compile(
    r"^(?P<prompt_id>[A-Z]\d{2})_(?P<platform>[a-z0-9.\-]+)_r(?P<repeat>\d+)_fail\.txt$",
    re.IGNORECASE,
)
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def load_manual_meta() -> dict[tuple[str, str, int], dict]:
    if not config.MANUAL_RUNS_CSV.exists():
        return {}
    df = pd.read_csv(config.MANUAL_RUNS_CSV, dtype=str).fillna("")
    out: dict[tuple[str, str, int], dict] = {}
    for _, row in df.iterrows():
        try:
            key = (str(row["prompt_id"]).upper(), str(row["platform"]).lower(), int(row["repeat"]))
        except Exception:
            continue
        out[key] = row.to_dict()
    return out


def expected_cells(stage: str, platforms: list[str]) -> list[tuple[str, str, int]]:
    prompts = utils.prompt_map()
    if stage == "pilot":
        ids, repeats = utils.PILOT_IDS, [1]
    elif stage == "main":
        ids, repeats = [x for x in prompts if not x.startswith("R")], [1]
    elif stage == "stability":
        ids, repeats = utils.STABILITY_IDS, [1, 2, 3]
    elif stage == "safety":
        ids, repeats = utils.SAFETY_IDS, [1]
    else:
        ids, repeats = list(prompts.keys()), [1]
    return [(pid, plat, rep) for pid in ids for plat in platforms for rep in repeats]


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest manual 即梦/可灵 images")
    parser.add_argument("--platforms", default="jimeng,kling")
    parser.add_argument("--stage", default="pilot", choices=["pilot", "main", "stability", "safety", "all"])
    args = parser.parse_args()

    config.ensure_dirs()
    prompts = utils.prompt_map()
    platforms = [x.strip().lower() for x in args.platforms.split(",") if x.strip()]
    meta = load_manual_meta()
    rows: list[dict] = []

    for platform in platforms:
        folder = config.RAW_DIR / platform
        folder.mkdir(parents=True, exist_ok=True)
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() in IMAGE_EXTS:
                parsed = utils.parse_filename(path)
                if not parsed:
                    print(f"WARN 命名不符合规范，跳过: {path.name}")
                    continue
                pid, rep = parsed["prompt_id"], parsed["repeat"]
                if pid not in prompts:
                    print(f"WARN 未知 prompt_id，跳过: {path.name}")
                    continue
                m = meta.get((pid, platform, rep), {})
                w, h = utils.image_dims(path)
                success = str(m.get("success", "true")).lower() not in {"false", "0", "no"}
                if str(m.get("moderation", "")).strip():
                    success = False
                rows.append({
                    "run_id": utils.run_id(pid, platform, rep),
                    "prompt_id": pid,
                    "platform": platform,
                    "source": "manual",
                    "model": m.get("model_version", "") or "unknown",
                    "repeat": rep,
                    "timestamp": m.get("date", "") or utils.now_iso(),
                    "aspect_ratio": prompts[pid]["aspect_ratio"],
                    "resolution": f"{w}x{h}",
                    "latency_s": m.get("latency_s", ""),
                    "cost": m.get("credits", ""),
                    "success": success,
                    "failure_reason": "" if success else (m.get("moderation") or "manual_failed"),
                    "image_path": str(path.relative_to(config.ROOT)),
                    "width": w,
                    "height": h,
                    "seed": "",
                    "prompt_enhancement": m.get("prompt_enhancement", ""),
                    "notes": " | ".join(x for x in [m.get("account_tier", ""), m.get("notes", "")] if x),
                })
            elif path.name.endswith("_fail.txt"):
                match = FAIL_RE.match(path.name)
                if not match:
                    continue
                pid, rep = match.group("prompt_id").upper(), int(match.group("repeat"))
                if pid not in prompts:
                    continue
                rows.append({
                    "run_id": utils.run_id(pid, platform, rep),
                    "prompt_id": pid,
                    "platform": platform,
                    "source": "manual",
                    "model": meta.get((pid, platform, rep), {}).get("model_version", "") or "unknown",
                    "repeat": rep,
                    "timestamp": utils.now_iso(),
                    "aspect_ratio": prompts[pid]["aspect_ratio"],
                    "resolution": "",
                    "latency_s": "",
                    "cost": "",
                    "success": False,
                    "failure_reason": path.read_text(encoding="utf-8", errors="ignore")[:500],
                    "image_path": "",
                    "width": "",
                    "height": "",
                    "seed": "",
                    "prompt_enhancement": "",
                    "notes": "failure file",
                })

    utils.upsert_runs(rows)
    print(f"已写入/更新 {len(rows)} 条手动记录。")

    # Coverage report
    runs = utils.load_runs()
    ok = runs.loc[runs["success"].astype(str).str.lower().isin(["true", "1"])]
    have = set(ok["run_id"])
    expected = expected_cells(args.stage, platforms)
    missing = [utils.run_id(pid, plat, rep) for pid, plat, rep in expected if utils.run_id(pid, plat, rep) not in have]
    print(f"\n覆盖检查（stage={args.stage}, platforms={platforms}）：")
    print(f"  期望 {len(expected)} 格，已有 {len(expected) - len(missing)} 格，缺 {len(missing)} 格")
    if missing:
        print("  缺失：" + ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
