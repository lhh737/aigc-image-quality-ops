"""Shared helpers: prompt loading, subsets, manifests, images."""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from PIL import Image, ImageOps

from . import config

RUN_COLUMNS = [
    "run_id", "prompt_id", "platform", "source", "model", "repeat",
    "timestamp", "aspect_ratio", "resolution", "latency_s", "cost",
    "success", "failure_reason", "image_path", "width", "height",
    "seed", "prompt_enhancement", "notes",
]

PILOT_IDS = ["E01", "E02", "E03", "E04", "T01", "T02", "T03", "T04", "H01", "H02", "H03", "H04"]
QWEN_IDS = ["E01", "E02", "E03", "E04", "T01", "T02", "T03", "T04", "H01", "H02"]
STABILITY_IDS = ["E01", "E03", "T01", "T03", "H01", "H03"]
SAFETY_IDS = ["R01", "R02", "R03", "R04", "R05", "R06"]
MAIN_PLATFORMS = ["jimeng", "kling", "seedream"]
QWEN_MODELS = ["qwen-image-3.0", "qwen-image-2.1-pro"]

FILENAME_RE = re.compile(
    r"^(?P<prompt_id>[A-Z]\d{2})_(?P<platform>[a-z0-9.\-]+)_r(?P<repeat>\d+)\.(png|jpg|jpeg|webp)$",
    re.IGNORECASE,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_prompts() -> list[dict]:
    with open(config.PROMPTS_CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def prompt_map() -> dict[str, dict]:
    return {row["prompt_id"]: row for row in load_prompts()}


def resolve_subset(name: str) -> list[str]:
    name = (name or "pilot").strip()
    mapping = {
        "pilot": PILOT_IDS,
        "qwen10": QWEN_IDS,
        "stability": STABILITY_IDS,
        "safety": SAFETY_IDS,
        "main": [rid for rid in prompt_map() if not rid.startswith("R")],
        "all": list(prompt_map().keys()),
    }
    if name in mapping:
        return mapping[name]
    ids = [x.strip() for x in name.split(",") if x.strip()]
    unknown = [x for x in ids if x not in prompt_map()]
    if unknown:
        raise SystemExit(f"未知 prompt_id: {unknown}")
    return ids


def run_id(prompt_id: str, platform: str, repeat: int) -> str:
    return f"{prompt_id}_{platform}_r{repeat}"


def parse_filename(path: Path) -> dict | None:
    match = FILENAME_RE.match(path.name)
    if not match:
        return None
    return {
        "prompt_id": match.group("prompt_id").upper(),
        "platform": match.group("platform").lower(),
        "repeat": int(match.group("repeat")),
    }


def load_runs() -> pd.DataFrame:
    if not config.RUNS_CSV.exists():
        return pd.DataFrame(columns=RUN_COLUMNS)
    df = pd.read_csv(config.RUNS_CSV, dtype=str).fillna("")
    for col in RUN_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[RUN_COLUMNS]


def upsert_runs(rows: list[dict]) -> None:
    """Merge run rows by run_id and write the manifest."""
    config.ensure_dirs()
    existing = load_runs()
    new = pd.DataFrame(rows)
    if new.empty:
        return
    for col in RUN_COLUMNS:
        if col not in new.columns:
            new[col] = ""
    new = new[RUN_COLUMNS]
    merged = pd.concat([existing, new], ignore_index=True)
    merged = merged.drop_duplicates(subset=["run_id"], keep="last")
    merged = merged.sort_values(["prompt_id", "platform", "repeat"])
    merged.to_csv(config.RUNS_CSV, index=False, encoding="utf-8-sig")


def download_image(url: str, dest: Path, timeout: int = 120) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content))
            img = ImageOps.exif_transpose(img).convert("RGB")
            img.save(dest, format="PNG")
            return dest
        except Exception as exc:  # pragma: no cover - network
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"下载图片失败: {last_error}")


def save_b64_image(b64: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = base64.b64decode(b64)
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.save(dest, format="PNG")
    return dest


def image_dims(path: Path) -> tuple[int, int]:
    with Image.open(path) as img:
        return img.size


def image_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strip_exif_copy(
    src: Path,
    dst: Path,
    max_side: int | None = None,
    crop_bottom_pct: float = 0.0,
) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        if crop_bottom_pct > 0:
            w, h = img.size
            img = img.crop((0, 0, w, max(1, int(h * (1 - crop_bottom_pct)))))
        if max_side and max(img.size) > max_side:
            img.thumbnail((max_side, max_side), Image.LANCZOS)
        img.save(dst, format="PNG", optimize=True)
    return dst


def to_data_uri(path: Path, max_side: int = 2048) -> str:
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        if max(img.size) > max_side:
            img.thumbnail((max_side, max_side), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=92)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def write_csv(path: Path, rows: list[dict], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        if columns:
            pd.DataFrame(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")
        return
    df = pd.DataFrame(rows)
    if columns:
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        df = df[columns]
    df.to_csv(path, index=False, encoding="utf-8-sig")
