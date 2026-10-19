"""Seedream 4.0 image generation via Volcano Ark.

Usage:
    python -m src.providers.ark_seedream --probe
    python -m src.providers.ark_seedream --subset pilot --repeat 1
    python -m src.providers.ark_seedream --subset main --repeat 1 --max-images 200
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import requests

from .. import config, quota, utils

API_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
DEFAULT_MODEL = "doubao-seedream-4-0-20260415"


def size_for_ratio(ratio: str) -> str:
    return {"1:1": "2048x2048", "3:4": "1728x2304"}.get(ratio, "2048x2048")


def generate_one(
    prompt: str,
    model: str,
    size: str,
    dry_run: bool = False,
) -> dict:
    body = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "response_format": "url",
        "watermark": False,
        "sequential_image_generation": "disabled",
        "stream": False,
        "optimize_prompt_options": {"mode": "fast"},
    }
    if dry_run:
        return {"dry_run": True, "request": body}

    key = config.env("ARK_API_KEY", required=True)
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    started = time.time()
    resp = requests.post(API_URL, headers=headers, json=body, timeout=180)
    latency = round(time.time() - started, 2)
    if resp.status_code >= 400:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:800]}")
    data = resp.json()
    items = data.get("data") or []
    if not items:
        raise RuntimeError(f"响应中没有图片: {str(data)[:800]}")
    item = items[0]
    return {
        "url": item.get("url"),
        "b64_json": item.get("b64_json"),
        "latency_s": latency,
        "response_id": data.get("id") or data.get("request_id") or "",
        "seed": item.get("seed") or data.get("seed") or "",
        "raw": data,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Seedream 4.0 batch generation")
    parser.add_argument("--subset", default="pilot", help="pilot | main | stability | safety | comma IDs")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--model", default=config.env("ARK_SEEDREAM_MODEL", DEFAULT_MODEL) or DEFAULT_MODEL)
    parser.add_argument("--size", default="", help="override size, e.g. 2048x2048")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--probe", action="store_true", help="run only E01")
    parser.add_argument("--max-images", type=int, default=200)
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--skip-existing", action="store_true", default=True)
    args = parser.parse_args()

    config.ensure_dirs()
    requested = args.max_images
    if not args.dry_run:
        args.max_images = quota.check("seedream", requested)
    prompts = utils.prompt_map()
    ids = ["E01"] if args.probe else utils.resolve_subset(args.subset)
    existing = utils.load_runs()
    done = set(existing.loc[existing["success"].astype(str).str.lower().isin(["true", "1"]), "run_id"])
    made = 0
    rows: list[dict] = []

    for prompt_id in ids:
        if made >= args.max_images:
            print(f"达到 --max-images={args.max_images}，停止。")
            break
        row_prompt = prompts[prompt_id]
        rid = utils.run_id(prompt_id, "seedream", args.repeat)
        if args.skip_existing and rid in done:
            print(f"skip existing {rid}")
            continue
        size = args.size or size_for_ratio(row_prompt["aspect_ratio"])
        try:
            result = generate_one(row_prompt["prompt"], args.model, size, args.dry_run)
            if args.dry_run:
                print(f"[dry-run] {rid}: {result['request']}")
                made += 1
                continue
            dest = config.RAW_DIR / "seedream" / f"{rid}.png"
            if result.get("url"):
                utils.download_image(result["url"], dest)
            elif result.get("b64_json"):
                utils.save_b64_image(result["b64_json"], dest)
            else:
                raise RuntimeError("没有 url 或 b64_json")
            w, h = utils.image_dims(dest)
            rows.append({
                "run_id": rid,
                "prompt_id": prompt_id,
                "platform": "seedream",
                "source": "api",
                "model": args.model,
                "repeat": args.repeat,
                "timestamp": utils.now_iso(),
                "aspect_ratio": row_prompt["aspect_ratio"],
                "resolution": f"{w}x{h}",
                "latency_s": result.get("latency_s", ""),
                "cost": 0,
                "success": True,
                "failure_reason": "",
                "image_path": str(dest.relative_to(config.ROOT)),
                "width": w,
                "height": h,
                "seed": result.get("seed", ""),
                "prompt_enhancement": "ark optimize_prompt_options=fast",
                "notes": result.get("response_id", ""),
            })
            made += 1
            print(f"ok {rid} -> {dest}")
        except Exception as exc:  # noqa: BLE001
            rows.append({
                "run_id": rid,
                "prompt_id": prompt_id,
                "platform": "seedream",
                "source": "api",
                "model": args.model,
                "repeat": args.repeat,
                "timestamp": utils.now_iso(),
                "aspect_ratio": row_prompt.get("aspect_ratio", ""),
                "resolution": "",
                "latency_s": "",
                "cost": 0,
                "success": False,
                "failure_reason": str(exc)[:1000],
                "image_path": "",
                "width": "",
                "height": "",
                "seed": "",
                "prompt_enhancement": "ark optimize_prompt_options=fast",
                "notes": "",
            })
            print(f"FAIL {rid}: {exc}", file=sys.stderr)
        finally:
            utils.upsert_runs(rows)
            rows = []
            time.sleep(args.sleep)

    if not args.dry_run:
        quota.log("seedream", requested, made, f"model={args.model}")
    print(f"完成：新增 {made} 张；免费额度剩余约 {quota.remaining('seedream')} 张。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
