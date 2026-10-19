"""Regenerate dashboard/data.js from data/analysis/summary.json.

Usage:
    python -m src.pipeline.build_dashboard
"""
from __future__ import annotations

import json

from .. import config


def main() -> int:
    if not config.SUMMARY_JSON.exists():
        raise SystemExit(f"缺少 {config.SUMMARY_JSON}，先运行 python -m src.pipeline.analyze")
    with open(config.SUMMARY_JSON, encoding="utf-8") as f:
        summary = json.load(f)
    config.DASHBOARD_DATA_JS.parent.mkdir(parents=True, exist_ok=True)
    with open(config.DASHBOARD_DATA_JS, "w", encoding="utf-8") as f:
        f.write("window.DASHBOARD_DATA = ")
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write(";\n")
    print(f"已生成 {config.DASHBOARD_DATA_JS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
