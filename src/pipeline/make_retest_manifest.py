"""Build a small retest manifest for intra-rater reliability.

Usage:
    python -m src.pipeline.make_retest_manifest
    python -m src.pipeline.make_retest_manifest --n 11 --seed 42

The retest subset is stratified by platform and category. It writes
`tools/annotation/manifest_retest.js` and `tools/annotation/index_retest.html`.
The retest tool uses its own localStorage key, so the first-pass scores are not
visible while retesting.
"""
from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path

import pandas as pd

from .. import config, utils

CATEGORIES = ["商品", "海报", "人像"]
PLATFORMS = ["jimeng", "seedream", "kling"]
PLATFORM_QUOTA = {"jimeng": 4, "seedream": 4, "kling": 3}


def load_full_manifest() -> list[dict]:
    path = config.ROOT / "tools" / "annotation" / "manifest.js"
    text = path.read_text(encoding="utf-8")
    match = re.search(r"window\.ANNOTATION_ITEMS\s*=\s*(\[.*\]);", text, re.S)
    if not match:
        raise SystemExit(f"无法解析 {path}")
    return json.loads(match.group(1))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build retest manifest")
    parser.add_argument("--n", type=int, default=11)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    items = load_full_manifest()
    blind_map = pd.read_csv(config.MANIFEST_DIR / "blind_map.csv", dtype=str, encoding="utf-8-sig").fillna("")
    platform_of = dict(zip(blind_map["blind_id"], blind_map["platform"]))
    for item in items:
        item["_platform"] = platform_of.get(item["blind_id"], "")

    rng = random.Random(args.seed)
    selected: list[dict] = []
    used: set[str] = set()

    # Pass 1: one item per platform/category.
    for platform in PLATFORMS:
        for category in CATEGORIES:
            candidates = [x for x in items if x["_platform"] == platform and x["category"] == category and x["blind_id"] not in used]
            if candidates:
                pick = rng.choice(sorted(candidates, key=lambda x: x["blind_id"]))
                selected.append(pick)
                used.add(pick["blind_id"])

    # Pass 2: fill each platform quota with remaining items.
    for platform in PLATFORMS:
        quota = PLATFORM_QUOTA[platform]
        candidates = [x for x in items if x["_platform"] == platform and x["blind_id"] not in used]
        need = max(0, quota - sum(1 for x in selected if x["_platform"] == platform))
        for pick in rng.sample(sorted(candidates, key=lambda x: x["blind_id"]), min(need, len(candidates))):
            selected.append(pick)
            used.add(pick["blind_id"])

    # Trim / fill to exact n.
    if len(selected) < args.n:
        remaining = [x for x in items if x["blind_id"] not in used]
        selected.extend(rng.sample(remaining, min(args.n - len(selected), len(remaining))))
    selected = selected[:args.n]
    rng.shuffle(selected)

    # Strip internal field and write the retest manifest.
    clean = [{k: v for k, v in item.items() if not k.startswith("_")} for item in selected]
    out = config.ROOT / "tools" / "annotation" / "manifest_retest.js"
    with open(out, "w", encoding="utf-8") as f:
        f.write("window.ANNOTATION_META = ")
        json.dump({"stage": "retest", "subset_size": len(clean), "seed": args.seed}, f, ensure_ascii=False)
        f.write(";\n")
        f.write("window.ANNOTATION_ITEMS = ")
        json.dump(clean, f, ensure_ascii=False, indent=2)
        f.write(";\n")

    # Build a retest copy of the tool with a separate localStorage namespace.
    src = config.ROOT / "tools" / "annotation" / "index.html"
    html = src.read_text(encoding="utf-8")
    html = html.replace('<script src="manifest.js"></script>', '<script src="manifest_retest.js"></script>')
    html = html.replace('AIGC 图像质检标注工具', 'AIGC 图像质检重测')
    html = html.replace('AIGC 图像质检标注', 'AIGC 图像质检重测')
    html = html.replace('const LS_KEY = "aigc_eval_annotations_v1";', 'const LS_KEY = "aigc_eval_annotations_retest_v1";')
    html = html.replace('const RATER_KEY = "aigc_eval_rater";', 'const RATER_KEY = "aigc_eval_rater_retest";')
    html = html.replace('没有找到 manifest.js。先运行：python -m src.pipeline.blind --stage pilot',
                        '没有找到 manifest_retest.js。先运行：python -m src.pipeline.make_retest_manifest')
    retest_html = config.ROOT / "tools" / "annotation" / "index_retest.html"
    retest_html.write_text(html, encoding="utf-8")

    print(f"重测子集：{len(clean)} 张")
    for item in clean:
        print(f"  {item['blind_id']}  {item['prompt_id']:4s}  {platform_of.get(item['blind_id'],''):8s}  {item['category']}")
    print(f"\n已生成：{out}")
    print(f"已生成：{retest_html}")
    print("打开 index_retest.html，输入 rater ID（例如 r1_retest），标注后导出 CSV。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
