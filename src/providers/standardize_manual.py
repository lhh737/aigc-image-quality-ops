"""Standardize manually downloaded 即梦/可灵 images.

The user downloads images with platform-generated names. This script:
1. fuzzy-matches each file to a prompt_id;
2. keeps the newest file whose aspect ratio matches the prompt;
3. moves all originals into data/raw/{platform}/_originals/;
4. copies the selected image to data/raw/{platform}/{prompt_id}_{platform}_r1.png;
5. writes data/manifests/manual_rename_map.csv and manual_runs.csv.

Usage:
    python -m src.providers.standardize_manual --platforms jimeng,kling --dry-run
    python -m src.providers.standardize_manual --platforms jimeng,kling --apply
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from PIL import Image

from .. import config, utils

PLATFORMS = ["jimeng", "kling"]
PILOT_IDS = ["E01", "E02", "E03", "E04", "T01", "T02", "T03", "T04", "H01", "H02", "H03", "H04"]
IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def norm(s: str) -> str:
    s = re.sub(r"^jimeng-\d{4}-\d{2}-\d{2}-\d+-", "", s)
    s = re.sub(r"^kling_\d+_作品_", "", s)
    s = re.sub(r"_\d+_\d+$", "", s)
    s = re.sub(r"[^一-鿿A-Za-z0-9]", "", s)
    return s


def ratio_ok(w: int, h: int, expected: str) -> bool:
    target = {"1:1": 1.0, "3:4": 0.75}.get(expected)
    if not target:
        return True
    return abs(w / h - target) <= 0.03


def match_prompt(file: Path, prompts: dict[str, dict], ids: list[str]) -> tuple[str, float]:
    fn = norm(file.stem)
    best = (0.0, "")
    for pid in ids:
        pn = norm(prompts[pid]["prompt"])
        score = max(
            SequenceMatcher(None, fn, pn).ratio(),
            SequenceMatcher(None, fn[:30], pn[:30]).ratio(),
        )
        if score > best[0]:
            best = (score, pid)
    return best[1], best[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Standardize manual images")
    parser.add_argument("--platforms", default="jimeng,kling")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    prompts = utils.prompt_map()
    platforms = [x.strip() for x in args.platforms.split(",") if x.strip()]
    selection: list[dict] = []

    for platform in platforms:
        folder = config.RAW_DIR / platform
        # top-level only: prevents kling/jimeng copy from contaminating Kling
        files = [
            p for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in IMG_EXTS
            and "contact_sheet" not in p.name.lower()
        ]
        candidates: dict[str, list[dict]] = {pid: [] for pid in PILOT_IDS}
        for f in files:
            pid, score = match_prompt(f, prompts, PILOT_IDS)
            with Image.open(f) as im:
                w, h = im.size
            exp = prompts[pid]["aspect_ratio"]
            candidates[pid].append({
                "file": f, "pid": pid, "score": score, "w": w, "h": h,
                "expected": exp, "ok": ratio_ok(w, h, exp),
                "mtime": f.stat().st_mtime,
            })
        for pid in PILOT_IDS:
            group = candidates[pid]
            good = [c for c in group if c["ok"]]
            pick = None
            if good:
                pick = sorted(good, key=lambda c: c["mtime"], reverse=True)[0]
            elif group:
                pick = sorted(group, key=lambda c: c["mtime"], reverse=True)[0]
            if pick:
                pick["platform"] = platform
                pick["standard"] = f"{pid}_{platform}_r1.png"
                selection.append(pick)

    # Report
    print(f"{'platform':8s} {'id':4s} {'ratio':5s} {'size':12s} {'ok':2s} {'score':5s} file")
    for row in sorted(selection, key=lambda r: (r["platform"], r["pid"])):
        print(f"{row['platform']:8s} {row['pid']:4s} {row['expected']:5s} "
              f"{row['w']}x{str(row['h']):<6s} {str(row['ok']):2s} {row['score']:.2f}  {row['file'].name[:70]}")

    missing = [(p, pid) for p in platforms for pid in PILOT_IDS
               if not any(r["platform"] == p and r["pid"] == pid for r in selection)]
    bad = [r for r in selection if not r["ok"]]
    if missing:
        print("\n缺失：", missing)
    if bad:
        print("\n比例仍不正确：", [(r["platform"], r["pid"], f"{r['w']}x{r['h']}") for r in bad])
    if missing or bad:
        print("\n未执行标准化；请补齐/修正后再跑。")
        return 1

    if not args.apply:
        print("\n[dry-run] 未改动文件。确认无误后加 --apply。")
        return 0

    # Apply: preserve all originals, then copy selected to standard names.
    rename_rows = []
    meta_rows = []
    for platform in platforms:
        folder = config.RAW_DIR / platform
        originals = folder / "_originals"
        incomplete = originals / "incomplete"
        originals.mkdir(exist_ok=True)
        incomplete.mkdir(exist_ok=True)
        # Move the accidental kling/jimeng copy out of the way.
        nested = folder / "jimeng"
        if nested.exists() and nested.is_dir():
            dest = originals / "jimeng_copy"
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(nested), str(dest))
        for f in list(folder.iterdir()):
            if not f.is_file():
                continue
            if f.name.endswith(".crdownload"):
                shutil.move(str(f), str(incomplete / f.name))
            else:
                shutil.move(str(f), str(originals / f.name))
        for row in [r for r in selection if r["platform"] == platform]:
            src = originals / row["file"].name
            dst = folder / row["standard"]
            shutil.copy2(src, dst)
            rename_rows.append({
                "platform": platform,
                "prompt_id": row["pid"],
                "standard_file": str(dst.relative_to(config.ROOT)),
                "original_file": row["file"].name,
                "width": row["w"],
                "height": row["h"],
                "expected_ratio": row["expected"],
                "ratio_ok": row["ok"],
                "mtime": datetime.fromtimestamp(row["mtime"]).isoformat(timespec="seconds"),
            })
            model = "Kling 3.0" if platform == "kling" else "即梦AI（版本未记录）"
            meta_rows.append({
                "prompt_id": row["pid"],
                "platform": platform,
                "repeat": 1,
                "model_version": model,
                "date": "2026-10-19",
                "account_tier": "free",
                "aspect_ratio": row["expected"],
                "resolution": f"{row['w']}x{row['h']}",
                "latency_s": "",
                "credits": "",
                "success": "true",
                "moderation": "",
                "prompt_enhancement": "unknown",
                "file": str(dst.relative_to(config.ROOT)),
                "notes": f"auto-standardized; original={row['file'].name}",
            })

    utils.write_csv(config.MANIFEST_DIR / "manual_rename_map.csv", rename_rows,
                    ["platform", "prompt_id", "standard_file", "original_file",
                     "width", "height", "expected_ratio", "ratio_ok", "mtime"])
    utils.write_csv(config.MANUAL_RUNS_CSV, meta_rows,
                    ["prompt_id", "platform", "repeat", "model_version", "date",
                     "account_tier", "aspect_ratio", "resolution", "latency_s",
                     "credits", "success", "moderation", "prompt_enhancement",
                     "file", "notes"])
    print(f"\n已标准化 {len(rename_rows)} 张。")
    print(f"原图保留：{config.RAW_DIR}/{{jimeng,kling}}/_originals/")
    print(f"映射：{config.MANIFEST_DIR / 'manual_rename_map.csv'}")
    print(f"元数据：{config.MANUAL_RUNS_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
