"""Analyze human + VLM annotations and build dashboard data.

Usage:
    python -m src.pipeline.analyze --stage pilot --bootstrap 1000
    python -m src.pipeline.build_dashboard
"""
from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from .. import config, utils

warnings.filterwarnings("ignore", category=RuntimeWarning)

DIMS = ["g1", "g2", "g3"]
DIM_LABELS = {"g1": "指令遵循", "g2": "视觉质量", "g3": "商业可用性"}


def load_human() -> pd.DataFrame:
    files = sorted(config.ANNOTATION_DIR.glob("human_*.csv"))
    if not files:
        raise SystemExit(
            f"没有人工标注文件。请把标注工具导出的 CSV 放到 {config.ANNOTATION_DIR}/human_*.csv"
        )
    frames = []
    for path in files:
        df = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
        df["_file"] = path.name
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True)

    blind_map_path = config.BLIND_MAP_CSV
    if not blind_map_path.exists():
        blind_map_path = config.MANIFEST_DIR / "blind_map.csv"
    if not blind_map_path.exists():
        raise SystemExit("缺少 blind_map.csv，无法把 blind_id 映射回平台。")
    blind_map = pd.read_csv(blind_map_path, dtype=str, encoding="utf-8-sig").fillna("")
    df = raw.merge(blind_map[["blind_id", "run_id", "platform", "model", "repeat"]], on="blind_id", how="left")
    for col in DIMS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # constraint pass rate
    rates = []
    for value in df["constraint_checks"]:
        try:
            checks = json.loads(value) if value else {}
            rates.append(sum(1 for v in checks.values() if str(v) in {"1", "True", "true"}) / len(checks) if checks else np.nan)
        except Exception:
            rates.append(np.nan)
    df["constraint_pass_rate"] = rates
    df["quality"] = 0.35 * df["g1"] + 0.30 * df["g2"] + 0.35 * df["g3"]
    df["first_pass"] = ((df["g2"] >= 4) & (df["g3"] >= 4) & (df["constraint_pass_rate"] >= 0.8)).astype(float)
    df.loc[df[["g1", "g2", "g3"]].isna().any(axis=1), "first_pass"] = np.nan
    return df.dropna(subset=["platform"])


def load_vlm() -> pd.DataFrame:
    path = config.ANNOTATION_DIR / "vlm_scores.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    for col in DIMS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["quality"] = 0.35 * df["g1"] + 0.30 * df["g2"] + 0.35 * df["g3"]
    return df


def cluster_bootstrap_ci(df: pd.DataFrame, value: str, cluster: str = "prompt_id", n: int = 1000, seed: int = 42) -> list[float]:
    sub = df[[cluster, value]].dropna()
    if sub.empty:
        return [np.nan, np.nan]
    clusters = sub[cluster].unique()
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(n):
        sample = rng.choice(clusters, size=len(clusters), replace=True)
        vals = []
        for c in sample:
            vals.extend(sub.loc[sub[cluster] == c, value].tolist())
        if vals:
            means.append(float(np.mean(vals)))
    if not means:
        return [np.nan, np.nan]
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def leaderboard(df: pd.DataFrame, runs: pd.DataFrame, n_boot: int) -> list[dict]:
    out = []
    for platform, g in df.groupby("platform"):
        r = runs[runs["platform"] == platform]
        lat = pd.to_numeric(r["latency_s"], errors="coerce").mean() if not r.empty else float("nan")
        cost = pd.to_numeric(r["cost"], errors="coerce").mean() if not r.empty else float("nan")
        out.append({
            "platform": platform,
            "n": int(g["quality"].notna().sum()),
            "quality_mean": round(float(g["quality"].mean()), 3) if g["quality"].notna().any() else None,
            "quality_ci": [round(x, 3) if pd.notna(x) else None for x in cluster_bootstrap_ci(g, "quality", n=n_boot)],
            "constraint_pass": round(float(g["constraint_pass_rate"].mean()), 3) if g["constraint_pass_rate"].notna().any() else None,
            "first_pass": round(float(g["first_pass"].mean()), 3) if g["first_pass"].notna().any() else None,
            "latency_s": round(float(lat), 1) if pd.notna(lat) else None,
            "cost_raw": round(float(cost), 3) if pd.notna(cost) else None,
        })
    return sorted(out, key=lambda x: (x["quality_mean"] is None, -(x["quality_mean"] or 0)))


def matrix(df: pd.DataFrame, index: str, n_boot: int) -> dict:
    categories = sorted(df[index].dropna().unique().tolist())
    platforms = sorted(df["platform"].dropna().unique().tolist())
    out = {"categories": categories, "platforms": platforms, "matrix": {}}
    for p in platforms:
        out["matrix"][p] = {}
        for c in categories:
            sub = df[(df["platform"] == p) & (df[index] == c)]
            out["matrix"][p][c] = round(float(sub["quality"].mean()), 3) if sub["quality"].notna().any() else None
    return out


def win_rate(df: pd.DataFrame, n_boot: int) -> dict:
    platforms = sorted(df["platform"].dropna().unique().tolist())
    by_prompt = df.groupby(["prompt_id", "platform"])["quality"].mean().unstack()
    by_prompt = by_prompt.dropna()
    if by_prompt.empty or len(platforms) < 2:
        return {"platforms": platforms, "matrix": {}, "n_prompts": 0}
    matrix = {}
    for a in platforms:
        matrix[a] = {}
        for b in platforms:
            if a == b:
                matrix[a][b] = None
                continue
            wins = (by_prompt[a] > by_prompt[b]).sum() + 0.5 * (by_prompt[a] == by_prompt[b]).sum()
            matrix[a][b] = round(float(wins / len(by_prompt)), 3)
    return {"platforms": platforms, "matrix": matrix, "n_prompts": int(len(by_prompt))}


def friedman_test(df: pd.DataFrame) -> dict:
    by_prompt = df.groupby(["prompt_id", "platform"])["quality"].mean().unstack().dropna()
    if by_prompt.shape[0] < 3 or by_prompt.shape[1] < 3:
        return {"available": False}
    stat, p = stats.friedmanchisquare(*[by_prompt[c].values for c in by_prompt.columns])
    return {"available": True, "stat": round(float(stat), 3), "p": float(p), "n_prompts": int(by_prompt.shape[0]), "platforms": list(by_prompt.columns)}


def holm_wilcoxon(df: pd.DataFrame) -> list[dict]:
    by_prompt = df.groupby(["prompt_id", "platform"])["quality"].mean().unstack().dropna()
    if by_prompt.shape[0] < 3 or by_prompt.shape[1] < 2:
        return []
    pairs = []
    platforms = list(by_prompt.columns)
    for i in range(len(platforms)):
        for j in range(i + 1, len(platforms)):
            a, b = platforms[i], platforms[j]
            try:
                stat, p = stats.wilcoxon(by_prompt[a], by_prompt[b], zero_method="wilcox")
            except Exception:
                continue
            pairs.append({"a": a, "b": b, "p_raw": float(p), "median_diff": round(float((by_prompt[a] - by_prompt[b]).median()), 3)})
    # Holm correction
    pairs.sort(key=lambda x: x["p_raw"])
    m = len(pairs)
    for i, row in enumerate(pairs):
        row["p_holm"] = round(min(1.0, row["p_raw"] * (m - i)), 4)
    return pairs


def agreement(human: pd.DataFrame, vlm: pd.DataFrame) -> dict:
    if vlm.empty:
        return {"available": False}
    # Use variant A for the primary comparison; average variants does not make sense for agreement.
    v = vlm[vlm["variant"] == "A"].copy()
    if v.empty:
        return {"available": False}
    h = human.groupby("run_id")[DIMS].mean().reset_index()
    m = h.merge(v[["run_id"] + DIMS], on="run_id", suffixes=("_human", "_vlm"))
    if m.empty:
        return {"available": False}
    out = {"available": True, "n": int(len(m)), "by_dim": {}}
    for dim in DIMS:
        a = m[f"{dim}_human"]
        b = m[f"{dim}_vlm"]
        mask = a.notna() & b.notna()
        diff = (a[mask] - b[mask]).abs()
        entry = {
            "n": int(mask.sum()),
            "exact": round(float((diff == 0).mean()), 3) if mask.any() else None,
            "adjacent": round(float((diff <= 1).mean()), 3) if mask.any() else None,
            "mae": round(float(diff.mean()), 3) if mask.any() else None,
        }
        try:
            import krippendorff
            arr = np.vstack([a[mask].values, b[mask].values]).astype(float)
            entry["alpha"] = round(float(krippendorff.alpha(reliability_data=arr, level_of_measurement="ordinal")), 3)
        except Exception:
            entry["alpha"] = None
        out["by_dim"][dim] = entry
    return out


def human_retest(human: pd.DataFrame) -> dict:
    files = human["_file"].unique().tolist()
    if len(files) < 2:
        return {"available": False, "reason": "只有一个标注文件"}
    first = human[human["_file"] == files[0]].set_index("blind_id")
    second = human[human["_file"] == files[1]].set_index("blind_id")
    common = first.index.intersection(second.index)
    if len(common) == 0:
        return {"available": False, "reason": "两个文件没有重叠 blind_id"}
    out = {"available": True, "n": int(len(common)), "by_dim": {}}
    for dim in DIMS:
        a, b = first.loc[common, dim], second.loc[common, dim]
        mask = a.notna() & b.notna()
        diff = (a[mask] - b[mask]).abs()
        out["by_dim"][dim] = {
            "exact": round(float((diff == 0).mean()), 3) if mask.any() else None,
            "adjacent": round(float((diff <= 1).mean()), 3) if mask.any() else None,
        }
    return out


def stability(human: pd.DataFrame) -> dict:
    if "repeat" not in human.columns:
        return {"available": False}
    h = human.copy()
    h["repeat"] = pd.to_numeric(h["repeat"], errors="coerce")
    sub = h.dropna(subset=["repeat", "quality"])
    groups = sub.groupby(["prompt_id", "platform"])["quality"]
    within = groups.std().dropna()
    if within.empty:
        return {"available": False}
    # rank flip across repeats
    ranks = sub.groupby(["prompt_id", "repeat", "platform"])["quality"].mean().reset_index()
    flips, total = 0, 0
    for pid, g in ranks.groupby("prompt_id"):
        per_repeat = []
        for rep, gg in g.groupby("repeat"):
            if gg["quality"].notna().any():
                per_repeat.append(gg.sort_values("quality", ascending=False)["platform"].iloc[0])
        if len(per_repeat) >= 2:
            total += 1
            flips += int(len(set(per_repeat)) > 1)
    return {
        "available": True,
        "within_sd_mean": round(float(within.mean()), 3),
        "within_sd_by_platform": {k: round(float(v), 3) for k, v in within.groupby(level=1).mean().items()},
        "rank_flip_rate": round(flips / total, 3) if total else None,
        "rank_flip_n": total,
    }


def badcases(human: pd.DataFrame) -> list[dict]:
    rows = []
    for _, row in human.iterrows():
        for tag in str(row.get("failure_tags", "")).split(";"):
            tag = tag.strip()
            if tag:
                rows.append({"platform": row["platform"], "tag": tag})
    if not rows:
        return []
    df = pd.DataFrame(rows)
    counts = df.groupby(["platform", "tag"]).size().reset_index(name="count")
    totals = human.groupby("platform").size().to_dict()
    counts["rate"] = counts.apply(lambda r: round(r["count"] / totals.get(r["platform"], 1), 3), axis=1)
    return counts.sort_values(["platform", "count"], ascending=[True, False]).to_dict("records")


def constraint_failures(df: pd.DataFrame) -> dict:
    details = []
    for _, row in df.iterrows():
        try:
            checks = json.loads(row.get("constraint_checks", ""))
        except Exception:
            checks = {}
        if not isinstance(checks, dict):
            continue
        for check, value in checks.items():
            if str(value) not in {"1", "True", "true"}:
                details.append({
                    "platform": row.get("platform", ""),
                    "prompt_id": row.get("prompt_id", ""),
                    "blind_id": row.get("blind_id", ""),
                    "check": check,
                    "g1": row.get("g1"),
                    "g2": row.get("g2"),
                    "g3": row.get("g3"),
                    "quality": round(float(row["quality"]), 3) if pd.notna(row.get("quality")) else None,
                    "failure_tags": row.get("failure_tags", ""),
                    "notes": row.get("notes", ""),
                })
    by = []
    if details:
        d = pd.DataFrame(details)
        by = (d.groupby(["platform", "check"]).size().reset_index(name="count")
              .sort_values(["platform", "count"], ascending=[True, False]).to_dict("records"))
    return {"total": len(details), "by_platform_check": by, "details": details}


def low_scores(df: pd.DataFrame, n: int = 12) -> list[dict]:
    out = []
    for _, row in df.sort_values("quality").head(n).iterrows():
        try:
            checks = json.loads(row.get("constraint_checks", ""))
        except Exception:
            checks = {}
        failed = [k for k, v in checks.items() if str(v) not in {"1", "True", "true"}] if isinstance(checks, dict) else []
        out.append({
            "platform": row.get("platform", ""),
            "prompt_id": row.get("prompt_id", ""),
            "blind_id": row.get("blind_id", ""),
            "g1": row.get("g1"),
            "g2": row.get("g2"),
            "g3": row.get("g3"),
            "quality": round(float(row["quality"]), 3) if pd.notna(row.get("quality")) else None,
            "failed_checks": failed,
            "failure_tags": row.get("failure_tags", ""),
            "notes": row.get("notes", ""),
        })
    return out


def per_prompt(df: pd.DataFrame) -> dict:
    p = df.groupby(["prompt_id", "platform"])["quality"].mean().unstack().round(3)
    return {
        "prompts": p.index.tolist(),
        "platforms": p.columns.tolist(),
        "matrix": {
            pl: {pid: (None if pd.isna(p.loc[pid, pl]) else float(p.loc[pid, pl])) for pid in p.index}
            for pl in p.columns
        },
    }


def scene_weighted(scene_matrix: dict, weights: dict | None = None) -> dict:
    weights = weights or {"ecommerce": 0.40, "social": 0.35, "portrait": 0.25}
    scores = {}
    for platform, values in (scene_matrix.get("matrix") or {}).items():
        total, wsum = 0.0, 0.0
        for scene, weight in weights.items():
            value = values.get(scene)
            if value is not None:
                total += float(value) * weight
                wsum += weight
        scores[platform] = round(total / wsum, 3) if wsum else None
    return {"weights": weights, "scores": scores}


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze annotations")
    parser.add_argument("--stage", default="pilot")
    parser.add_argument("--bootstrap", type=int, default=1000)
    args = parser.parse_args()

    config.ensure_dirs()
    human = load_human()
    vlm = load_vlm()
    runs = utils.load_runs()
    prompts = pd.DataFrame(utils.load_prompts())
    human = human.merge(prompts[["prompt_id", "category", "scene"]], on="prompt_id", how="left")
    human = human[human["quality"].notna()]
    if human.empty:
        raise SystemExit("人工标注里没有有效的 g1/g2/g3，无法分析。")

    scene_matrix = matrix(human, "scene", args.bootstrap)
    summary = {
        "meta": {
            "project": "AIGC 多模态数据质量评估与运营复现",
            "generated_at": utils.now_iso(),
            "n_human": int(len(human)),
            "n_vlm": int(len(vlm)),
            "platforms": sorted(human["platform"].dropna().unique().tolist()),
            "stage": args.stage,
        },
        "leaderboard": leaderboard(human, runs, args.bootstrap),
        "category": matrix(human, "category", args.bootstrap),
        "scene": scene_matrix,
        "scene_weighted": scene_weighted(scene_matrix),
        "per_prompt": per_prompt(human),
        "win_rate": win_rate(human, args.bootstrap),
        "friedman": friedman_test(human),
        "wilcoxon": holm_wilcoxon(human),
        "stability": stability(human),
        "human_vlm": agreement(human, vlm),
        "human_retest": human_retest(human),
        "badcases": badcases(human),
        "constraint_failures": constraint_failures(human),
        "low_scores": low_scores(human),
        "limitations": [
            "pilot 规模小，结论是方向性的，不是公开 benchmark。",
            "闭源平台会改写提示词/做后处理，本项目测的是产品交付质量。",
            "平台版本会漂移，结论只代表测试日期。",
            "VLM 是第二评分通道，不是第二个人工标注者。",
            "可灵/即梦为手动采集，延迟与积分为空；Seedream 为 API 延迟。",
        ],
    }

    config.ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    config.DASHBOARD_DATA_JS.parent.mkdir(parents=True, exist_ok=True)
    with open(config.DASHBOARD_DATA_JS, "w", encoding="utf-8") as f:
        f.write("window.DASHBOARD_DATA = ")
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write(";\n")

    # CSV exports
    pd.DataFrame(summary["leaderboard"]).to_csv(config.ANALYSIS_DIR / "leaderboard.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(summary["badcases"]).to_csv(config.ANALYSIS_DIR / "badcases.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(summary["wilcoxon"]).to_csv(config.ANALYSIS_DIR / "wilcoxon.csv", index=False, encoding="utf-8-sig")

    print(f"分析完成：{config.SUMMARY_JSON}")
    print(f"看板数据：{config.DASHBOARD_DATA_JS}")
    print("\nLeaderboard:")
    for row in summary["leaderboard"]:
        print(f"  {row['platform']:24s} quality={row['quality_mean']} ci={row['quality_ci']} first_pass={row['first_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
