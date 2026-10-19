"""Qwen-MT-Image translation QC module (optional side experiment).

Important: qwen-mt-image-2.0 is IMAGE TRANSLATION, not text-to-image generation.
Use it to translate Chinese poster text into EN/JA and evaluate layout/text quality.
Quota: 100 free images.

Usage:
    python -m src.providers.qwen_mt_image --probe
    python -m src.providers.qwen_mt_image --source-platforms jimeng,kling,seedream --target-langs en,ja
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import requests

from .. import config, quota, utils

API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-synthesis"
MODEL = "qwen-mt-image-2.0"


def translate_one(image_path: Path, target_lang: str, dry_run: bool = False) -> dict:
    data_uri = utils.to_data_uri(image_path, max_side=2048)
    body = {
        "model": MODEL,
        "input": {
            "image_url": data_uri,
            "source_lang": "zh",
            "target_lang": target_lang,
            "config": {"imageSegment": False},
        },
    }
    if dry_run:
        return {"dry_run": True, "request": {**body, "input": {**body["input"], "image_url": "<data-uri>"}}}

    key = config.env("DASHSCOPE_API_KEY", required=True)
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    started = time.time()
    resp = requests.post(API_URL, headers=headers, json=body, timeout=180)
    latency = round(time.time() - started, 2)
    if resp.status_code >= 400:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:800]}")
    data = resp.json()
    url = (data.get("output") or {}).get("image_url", "")
    if not url:
        raise RuntimeError(f"响应中没有 image_url: {str(data)[:800]}")
    return {
        "url": url,
        "latency_s": latency,
        "response_id": data.get("request_id") or "",
        "raw": data,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Qwen-MT-Image translation side experiment")
    parser.add_argument("--source-platforms", default="jimeng,kling,seedream")
    parser.add_argument("--subset", default="T01,T02,T03,T04")
    parser.add_argument("--target-langs", default="en,ja")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--max-images", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--sleep", type=float, default=1.0)
    args = parser.parse_args()

    config.ensure_dirs()
    requested = args.max_images
    if not args.dry_run:
        args.max_images = quota.check("qwen-mt-image-2.0", requested)
    prompts = utils.prompt_map()
    ids = ["T01"] if args.probe else [x.strip() for x in args.subset.split(",") if x.strip()]
    platforms = [x.strip() for x in args.source_platforms.split(",") if x.strip()]
    if args.probe:
        platforms = ["jimeng"]
    langs = [x.strip() for x in args.target_langs.split(",") if x.strip()]
    made = 0

    for prompt_id in ids:
        for platform in platforms:
            src = config.RAW_DIR / platform / f"{utils.run_id(prompt_id, platform, args.repeat)}.png"
            if not src.exists():
                print(f"skip missing {src}")
                continue
            for lang in langs:
                if made >= args.max_images:
                    print(f"达到 --max-images={args.max_images}，停止。")
                    return 0
                rid = f"{prompt_id}_{platform}_mt_{lang}"
                dest = config.RAW_DIR / "qwen-mt" / f"{rid}.png"
                try:
                    result = translate_one(src, lang, args.dry_run)
                    if args.dry_run:
                        print(f"[dry-run] {rid}: {result['request']}")
                        made += 1
                        continue
                    utils.download_image(result["url"], dest)
                    w, h = utils.image_dims(dest)
                    utils.upsert_runs([{
                        "run_id": rid,
                        "prompt_id": prompt_id,
                        "platform": f"qwen-mt-{lang}",
                        "source": "api",
                        "model": MODEL,
                        "repeat": args.repeat,
                        "timestamp": utils.now_iso(),
                        "aspect_ratio": prompts[prompt_id]["aspect_ratio"],
                        "resolution": f"{w}x{h}",
                        "latency_s": result.get("latency_s", ""),
                        "cost": 0,
                        "success": True,
                        "failure_reason": "",
                        "image_path": str(dest.relative_to(config.ROOT)),
                        "width": w,
                        "height": h,
                        "seed": "",
                        "prompt_enhancement": "translation",
                        "notes": f"source={src.relative_to(config.ROOT)};target={lang}",
                    }])
                    made += 1
                    print(f"ok {rid} -> {dest}")
                except Exception as exc:  # noqa: BLE001
                    print(f"FAIL {rid}: {exc}", file=sys.stderr)
                finally:
                    time.sleep(args.sleep)
    if not args.dry_run:
        quota.log("qwen-mt-image-2.0", requested, made, "qwen_mt_image")
    print(f"完成：新增 {made} 张翻译图；免费额度剩余约 {quota.remaining('qwen-mt-image-2.0')} 张。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
