"""Qwen-Image text-to-image via DashScope OpenAI-compatible endpoint.

Quota note: qwen-image-3.0 and qwen-image-2.1-pro each have only 10 free images.
Use --subset qwen10 and never exceed --max-images 10.

Usage:
    python -m src.providers.qwen_image --model qwen-image-3.0 --probe
    python -m src.providers.qwen_image --model qwen-image-3.0 --subset qwen10 --repeat 1
    python -m src.providers.qwen_image --model qwen-image-2.1-pro --subset qwen10 --repeat 1
"""
from __future__ import annotations

import argparse
import sys
import time

import requests

from .. import config, quota, utils

API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
DEFAULT_MODEL = "qwen-image-3.0"


def size_for_ratio(ratio: str) -> str:
    # Native DashScope uses W*H, not WxH.
    return {"1:1": "1024*1024", "3:4": "1152*1536"}.get(ratio, "1024*1024")


def generate_one(prompt: str, model: str, size: str, dry_run: bool = False) -> dict:
    body = {
        "model": model,
        "input": {
            "messages": [
                {"role": "user", "content": [{"text": prompt}]}
            ]
        },
        "parameters": {
            "size": size,
            "n": 1,
            "prompt_extend": False,
            "watermark": False,
        },
    }
    if dry_run:
        return {"dry_run": True, "request": body}

    key = config.env("DASHSCOPE_API_KEY", required=True)
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    started = time.time()
    resp = requests.post(API_URL, headers=headers, json=body, timeout=600)
    latency = round(time.time() - started, 2)
    if resp.status_code >= 400:
        raise RuntimeError(
            f"HTTP {resp.status_code}: {resp.text[:1200]}\n"
            "当前使用 DashScope 原生 multimodal-generation 端点；"
            "若仍 404，请确认模型已在百炼控制台开通。"
        )
    data = resp.json()
    url = ""
    output = data.get("output") or {}
    choices = output.get("choices") or []
    if choices:
        content = (choices[0].get("message") or {}).get("content") or []
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("image"):
                    url = item["image"]
                    break
    if not url:
        results = output.get("results") or []
        if results:
            url = results[0].get("url", "")
    if not url:
        raise RuntimeError(f"响应中没有图片 URL: {str(data)[:1200]}")
    return {
        "url": url,
        "latency_s": latency,
        "response_id": data.get("request_id") or data.get("id") or "",
        "raw": data,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Qwen-Image batch generation (limited quota)")
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=["qwen-image-3.0", "qwen-image-2.1-pro"])
    parser.add_argument("--subset", default="qwen10")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--size", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--max-images", type=int, default=10)
    parser.add_argument("--sleep", type=float, default=1.5)
    parser.add_argument("--skip-existing", action="store_true", default=True)
    args = parser.parse_args()

    config.ensure_dirs()
    requested = args.max_images
    if not args.dry_run:
        args.max_images = quota.check(args.model, requested)
    prompts = utils.prompt_map()
    ids = ["E01"] if args.probe else utils.resolve_subset(args.subset)
    existing = utils.load_runs()
    done = set(existing.loc[existing["success"].astype(str).str.lower().isin(["true", "1"]), "run_id"])
    made = 0

    for prompt_id in ids:
        if made >= args.max_images:
            print(f"达到 --max-images={args.max_images}，停止（保护免费额度）。")
            break
        row_prompt = prompts[prompt_id]
        rid = utils.run_id(prompt_id, args.model, args.repeat)
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
            dest = config.RAW_DIR / args.model / f"{rid}.png"
            utils.download_image(result["url"], dest)
            w, h = utils.image_dims(dest)
            utils.upsert_runs([{
                "run_id": rid,
                "prompt_id": prompt_id,
                "platform": args.model,
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
                "seed": "",
                "prompt_enhancement": "prompt_extend=false",
                "notes": result.get("response_id", ""),
            }])
            made += 1
            print(f"ok {rid} -> {dest}")
        except Exception as exc:  # noqa: BLE001
            utils.upsert_runs([{
                "run_id": rid,
                "prompt_id": prompt_id,
                "platform": args.model,
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
                "prompt_enhancement": "prompt_extend=false",
                "notes": "",
            }])
            print(f"FAIL {rid}: {exc}", file=sys.stderr)
        finally:
            time.sleep(args.sleep)

    if not args.dry_run:
        quota.log(args.model, requested, made, "qwen_image")
    print(f"完成：新增 {made} 张（模型 {args.model}）；免费额度剩余约 {quota.remaining(args.model)} 张。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
