"""Hard quota guards for free-tier image generation.

The user explicitly asked: only call the models with free quota, never exceed it.
This module counts successful runs in data/manifests/runs.csv and refuses to start
a batch that would exceed the configured free quota.
"""
from __future__ import annotations

import csv
from pathlib import Path

from . import config, utils

QUOTAS = {
    "seedream": 200,
    "qwen-image-3.0": 10,
    "qwen-image-2.1-pro": 10,
    "qwen-mt-image-2.0": 100,
}

QUOTA_LOG = config.MANIFEST_DIR / "quota_log.csv"


def _platform_matches(row_platform: str, platform: str) -> bool:
    if platform == "qwen-mt-image-2.0":
        return str(row_platform).startswith("qwen-mt")
    return str(row_platform) == platform


def used(platform: str) -> int:
    runs = utils.load_runs()
    if runs.empty:
        return 0
    ok = runs["success"].astype(str).str.lower().isin(["true", "1"])
    return int(sum(1 for p, good in zip(runs["platform"], ok) if good and _platform_matches(p, platform)))


def remaining(platform: str) -> int:
    quota = QUOTAS.get(platform)
    if quota is None:
        raise SystemExit(f"未知平台配额: {platform}")
    return max(0, quota - used(platform))


def check(platform: str, requested: int) -> int:
    """Return the allowed number of images, or exit if none remain."""
    quota = QUOTAS.get(platform)
    if quota is None:
        raise SystemExit(f"未知平台配额: {platform}，拒绝调用。")
    already = used(platform)
    left = max(0, quota - already)
    if left <= 0:
        raise SystemExit(
            f"配额已用完：{platform} 已用 {already}/{quota}。"
            "不会继续调用；如需继续，请先明确授权或更换模型。"
        )
    allowed = min(requested, left)
    if allowed < requested:
        print(f"配额保护：{platform} 剩余 {left} 张，本次最多 {allowed} 张（请求 {requested}）。")
    return allowed


def log(platform: str, requested: int, generated: int, note: str = "") -> None:
    config.MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    new = not QUOTA_LOG.exists()
    with open(QUOTA_LOG, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if new:
            writer.writerow(["timestamp", "platform", "requested", "generated", "used_after", "quota", "note"])
        writer.writerow([utils.now_iso(), platform, requested, generated, used(platform), QUOTAS.get(platform, ""), note])
