"""Project paths and environment loading."""
from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

PROMPTS_CSV = ROOT / "prompts" / "prompts_v1.csv"
CONFIG_YAML = ROOT / "configs" / "platforms.yaml"

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
MANIFEST_DIR = DATA_DIR / "manifests"
ANNOTATION_DIR = DATA_DIR / "annotations"
PRIVATE_DIR = DATA_DIR / "private"
ANALYSIS_DIR = DATA_DIR / "analysis"
BLINDED_DIR = DATA_DIR / "blinded"

RUNS_CSV = MANIFEST_DIR / "runs.csv"
MANUAL_RUNS_CSV = MANIFEST_DIR / "manual_runs.csv"

BLIND_MAP_CSV = PRIVATE_DIR / "blind_map.csv"
VLM_CACHE = PRIVATE_DIR / "vlm_cache.jsonl"
ANNOTATION_MANIFEST_JS = ROOT / "tools" / "annotation" / "manifest.js"

DASHBOARD_DATA_JS = ROOT / "dashboard" / "data.js"
SUMMARY_JSON = ANALYSIS_DIR / "summary.json"


def env(name: str, default: str = "", required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise SystemExit(
            f"缺少环境变量 {name}。请复制 .env.example 为 .env 并填写，"
            f"路径：{ROOT / '.env'}"
        )
    return value


def load_config() -> dict:
    with open(CONFIG_YAML, encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs() -> None:
    for path in (
        RAW_DIR,
        MANIFEST_DIR,
        ANNOTATION_DIR,
        PRIVATE_DIR,
        ANALYSIS_DIR,
        BLINDED_DIR,
        RAW_DIR / "jimeng",
        RAW_DIR / "kling",
        RAW_DIR / "seedream",
        RAW_DIR / "qwen-image-3.0",
        RAW_DIR / "qwen-image-2.1-pro",
        RAW_DIR / "qwen-mt",
    ):
        path.mkdir(parents=True, exist_ok=True)
