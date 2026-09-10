"""
Operating-region characterization for WiFi-CSI fall-alert robustness.

Analysis only. Reads existing per-window CSV exports; does not train, attack,
load checkpoints, or edit thesis files.

Command:
    python scripts/analysis/operating_region_characterization.py
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import argparse
import math
import re

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from sklearn.metrics import roc_auc_score
except Exception:
    roc_auc_score = None

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
SG = RESULTS / "safety_guided_defense"
OUT = RESULTS / "operating_region_characterization"
FALL_LABEL = 1
EXPECTED_FALL = 45
EXPECTED_NONFALL = 455
TARGET_RECALL = 0.80
FAR_CAPS = (0.10, 0.20)
EPSILON_REQUESTED = (0.000, 0.005, 0.010, 0.015, 0.020, 0.025, 0.030)
LABEL_COLS = ("fall_true_binary", "true_binary", "y_true_binary", "is_fall", "true_label", "y_true", "label")
SCORE_COLS = ("fall_probability", "prob_fall", "p_fall", "fall_prob", "score_fall", "fall_score", "logit_fall")
HARD_COLS = ("fall_pred_binary", "predicted_label", "prediction", "pred", "attacked_predicted_label")


def rel(p: Path) -> str:
    return p.resolve().relative_to(ROOT).as_posix()


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.strip().lower()).strip("_")


def find_col(df: pd.DataFrame, names) -> str | None:
    lookup = {norm(c): c for c in df.columns}
    for name in names:
        hit = lookup.get(norm(name))
        if hit is not None:
            return hit
    return None


def expand(pattern: str, family: str, priority: int, note: str = ""):
    out = []
    for p in sorted(SG.glob(pattern)):
        if p.is_file() and "_pgd20_" not in p.name:
            out.append({"family": family, "path": p, "priority": priority, "note": note})
    return out


def candidate_files():
    cands = []
    cands += expand("variantG_targeted_hardneg/seed44/test_eval/*_pgd_probabilities_test_epsilon_0_03.csv", "Variant G/G1 seed44", 10, "primary G1 test score export")
    cands += expand("variantG_targeted_hardneg/seed42/test_eval/G_G1_*_pgd_probabilities_test_epsilon_0_03.csv", "Variant G/G1 seed42", 20, "G1 seed42 test score export")
    cands += expand("variantH_dual_tail_budget/adaptive_lagrangian_far_constrained/optionB/seed42/test_eval/optionB_*_pgd_probabilities_test_epsilon_0_03.csv", "Option B seed42", 30, "maxrec/maxscore/minFA test score exports")
    cands += expand("dual_specialist_safety_gate/A1/seed42/probabilities/*_pgd_probabilities_test_epsilon_0_03.csv", "Option B/Gate reference seed42", 35, "earlier gate probability exports")
    cands += expand("variantF_motion_margin/seed44/test_eval/*_pgd_probabilities_test_epsilon_0_03.csv", "Variant F seed44 reference", 40, "high-recall/high-FP reference")
    cands += expand("variantF_motion_margin/seed42/test_eval/*_pgd_probabilities_test_epsilon_0_03.csv", "Variant F seed42 reference", 45, "high-recall/high-FP reference")
    cands += expand("boundary_aware_selective_at/seed42/*/val_eval/*_pgd_probabilities_val_epsilon_0_03.csv", "BASAT/Stage1 validation seed42", 60, "validation-only score export")
    cands += expand("boundary_aware_selective_at/sat/seed42/*/val_eval/*_pgd_probabilities_val_epsilon_0_03.csv", "SAT validation seed42", 65, "validation-only score export")
    cands += expand("boundary_aware_selective_at/gairat/seed42/*/val_eval/*_pgd_probabilities_val_epsilon_0_03.csv", "GAIRAT validation seed42", 66, "validation-only score export")
    cands += expand("variantG_bilstm_representation_test/seed42/g1_finetune_cleaninit/val_eval/*_pgd_probabilities_val_epsilon_0_03.csv", "BiLSTM G1 validation seed42", 70, "validation-only representation test")
    seen = set()
    out = []
    for cand in cands:
        key = cand["path"].resolve()
        if key not in seen:
            seen.add(key)
            out.append(cand)
    return out


def parse_meta(path: Path, df: pd.DataFrame):
    m = re.search(r"_(clean|fgsm|pgd)_probabilities_(test|val|legacy)_epsilon_([0-9_]+)\.csv$", path.name)
    if m:
        return m.group(1), m.group(2), float(m.group(3).replace("_", "."))
    condition = str(df.get("condition", pd.Series(["unknown"])).dropna().iloc[0]).lower() if "condition" in df else "unknown"
    split = "test" if "_test_" in path.name else "val" if "_val_" in path.name else "unknown"
    epsilon = float(df.get("epsilon", pd.Series([math.nan])).dropna().iloc[0]) if "epsilon" in df else math.nan
    return condition, split, epsilon


def candidate_name(path: Path) -> str:
    m = re.search(r"(.+)_(clean|fgsm|pgd)_probabilities_(test|val|legacy)_epsilon_", path.name)
    stem = m.group(1) if m else path.stem
    sm = re.search(r"/(seed\d+)/", rel(path))
    seed = sm.group(1) if sm else "seed?"
    return f"{stem} ({seed})"


def labels_and_scores(df: pd.DataFrame):
    label_col = find_col(df, LABEL_COLS)
    score_col = find_col(df, SCORE_COLS)
    if label_col is None:
        raise ValueError("missing label column")
    if score_col is None:
        hard_col = find_col(df, HARD_COLS)
        if hard_col:
            raise ValueError(f"hard predictions only via {hard_col}; no fall score column")
        raise ValueError("missing fall score column")
    raw = pd.to_numeric(df[label_col], errors="raise").astype(int).to_numpy()
    if norm(label_col) in {"fall_true_binary", "true_binary", "y_true_binary", "is_fall"}:
        y = (raw == 1).astype(int)
    elif set(raw.tolist()).issubset({0, 1}) and norm(label_col) not in {"true_label", "y_true"}:
        y = (raw == 1).astype(int)
    else:
        y = (raw == FALL_LABEL).astype(int)
    scores = pd.to_numeric(df[score_col], errors="raise").to_numpy(float)
    return y, scores, score_col


def auc(y, scores):
    n_pos = int(y.sum())
    n_neg = int(len(y) - n_pos)
    if n_pos == 0 or n_neg == 0:
        return math.nan
    if roc_auc_score is not None:
        return float(roc_auc_score(y, scores))
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=float)
    i = 0
    while i < len(scores):
        j = i + 1
        while j < len(scores) and scores[order[j]] == scores[order[i]]:
            j += 1
        ranks[order[i:j]] = (i + 1 + j) / 2.0
        i = j
    return float((ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def curve(y, scores):
    thresholds = sorted(set(scores.tolist()), reverse=True)
    if thresholds:
        thresholds = [np.nextafter(thresholds[0], math.inf)] + thresholds
    rows = []
    n_fall = int(y.sum())
    n_nonfall = int(len(y) - n_fall)
    for t in thresholds:
        pred = scores >= t
        tp = int(np.sum(pred & (y == 1)))
        fp = int(np.sum(pred & (y == 0)))
        fn = n_fall - tp
        tn = n_nonfall - fp
        rows.append({"threshold": float(t), "TP": tp, "FN": fn, "FP": fp, "TN": tn, "FAR": fp / n_nonfall, "recall": tp / n_fall})
    return pd.DataFrame(rows)


def best_point(curve_df: pd.DataFrame, cap: float):
    feasible = curve_df[curve_df["FAR"] <= cap].copy()
    feasible = feasible.sort_values(["recall", "FP", "threshold"], ascending=[False, True, False], kind="mergesort")
    row = feasible.iloc[0].to_dict()
    row["far_cap"] = cap
    return row


def analyze():
    rows = []
    curves = {}
    errors = []
    for cand in candidate_files():
        try:
            df = pd.read_csv(cand["path"])
            y, scores, score_col = labels_and_scores(df)
            condition, split, epsilon = parse_meta(cand["path"], df)
            c = curve(y, scores)
            au = auc(y, scores)
            name = candidate_name(cand["path"])
            curves[name] = c.assign(candidate=name)
            warnings = []
            n_fall = int(y.sum())
            n_nonfall = int(len(y) - n_fall)
            if split == "test" and n_fall != EXPECTED_FALL:
                warnings.append(f"expected {EXPECTED_FALL} test fall rows, found {n_fall}")
            if split == "test" and n_nonfall != EXPECTED_NONFALL:
                warnings.append(f"expected {EXPECTED_NONFALL} test non-fall rows, found {n_nonfall}")
            for cap in FAR_CAPS:
                op = best_point(c, cap)
                rows.append({
                    "family": cand["family"], "candidate": name, "split": split, "condition": condition,
                    "epsilon": epsilon, "far_cap": cap, "auroc": au, "recall": op["recall"], "FAR": op["FAR"],
                    "TP": int(op["TP"]), "FN": int(op["FN"]), "FP": int(op["FP"]), "TN": int(op["TN"]),
                    "threshold": op["threshold"], "target_recall_ge_0_80": bool(op["recall"] >= TARGET_RECALL),
                    "n_rows": len(df), "n_fall": n_fall, "n_nonfall": n_nonfall,
                    "unique_scores": len(set(scores.tolist())), "score_column": score_col,
                    "score_file": rel(cand["path"]), "note": cand["note"], "warnings": "; ".join(warnings)
                })
        except Exception as exc:
            errors.append(f"{rel(cand['path'])}: {exc}")
    return pd.DataFrame(rows), curves, errors


def token(eps: float) -> str:
    if eps == 0:
        return "0"
    return (f"{eps:.4f}".rstrip("0").rstrip(".")).replace(".", "_")


def availability_notes():
    notes = []
    for eps in EPSILON_REQUESTED:
        t = token(eps)
        score = list(RESULTS.glob(f"**/*pgd*probabilities*epsilon_{t}.csv"))
        hard = list(RESULTS.glob(f"**/*pgd*predictions*epsilon_{t}.csv"))
        if score:
            notes.append(f"- epsilon {eps:.3f}: found {len(score)} PGD probability/logit score file(s).")
        elif hard:
            notes.append(f"- epsilon {eps:.3f}: found {len(hard)} hard-prediction PGD file(s), but no fall score/probability/logit column.")
        else:
            notes.append(f"- epsilon {eps:.3f}: no PGD score file found.")
    sweeps = list(RESULTS.glob("**/*pgd_sweep_predictions_test.csv"))
    if sweeps:
        notes.append(f"- Found {len(sweeps)} PGD sweep prediction table(s); these store argmax labels and max confidence rather than fall score.")
    ckpts = list((ROOT / "checkpoints").glob("**/*.pt"))
    if ckpts and (ROOT / "scripts" / "export_probability_predictions.py").exists():
        notes.append(f"- Frozen checkpoints are present ({len(ckpts)} .pt files), and scripts/export_probability_predictions.py can export fall probabilities at additional epsilons without retraining.")
    trades = list(ROOT.glob("**/*trades*")) + list(ROOT.glob("**/*TRADES*"))
    notes.append(f"- TRADES-named artifacts found: {len(trades)} path(s)." if trades else "- TRADES-named artifacts were not found in the local repo inventory.")
    return notes


def best_rows(summary: pd.DataFrame):
    out = {}
    scope = summary[(summary["split"] == "test") & (summary["condition"] == "pgd")]
    for cap in FAR_CAPS:
        part = scope[scope["far_cap"] == cap].copy()
        if len(part):
            out[cap] = part.sort_values(["recall", "FP", "auroc", "threshold"], ascending=[False, True, False, False], kind="mergesort").iloc[0]
    return out


def md_table(summary: pd.DataFrame, split: str):
    scope = summary[(summary["split"] == split) & (summary["condition"] == "pgd")]
    if scope.empty:
        return "_No rows._"
    keys = ["family", "candidate", "epsilon", "auroc"]
    rows = []
    for key, group in scope.groupby(keys, dropna=False, sort=False):
        item = dict(zip(keys, key))
        for cap in FAR_CAPS:
            r = group[group["far_cap"] == cap].iloc[0]
            suffix = int(cap * 100)
            item[f"recall_{suffix}"] = r["recall"]
            item[f"tp_fp_{suffix}"] = f"{int(r['TP'])}/{int(r['FP'])}"
        rows.append(item)
    p = pd.DataFrame(rows).sort_values(["recall_20", "recall_10", "auroc"], ascending=[False, False, False], kind="mergesort")
    lines = ["| family | candidate | AUROC | recall@FAR<=0.10 TP/FP | recall@FAR<=0.20 TP/FP |", "|---|---|---:|---:|---:|"]
    for _, r in p.head(30).iterrows():
        lines.append(f"| {r['family']} | {r['candidate']} | {r['auroc']:.3f} | {r['recall_10']:.3f} ({r['tp_fp_10']}) | {r['recall_20']:.3f} ({r['tp_fp_20']}) |")
    return "\n".join(lines)


def write_outputs(summary: pd.DataFrame, curves: dict, errors: list[str]):
    OUT.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT / "operating_region_summary.csv", index=False)
    best = best_rows(summary)
    lines = ["# Operating-Region Characterization", "", f"Generated: {datetime.now(timezone.utc).isoformat()}", "", "Analysis-only run using existing per-window CSV score exports. Fall label is class 1.", f"Test split assumption: {EXPECTED_FALL} fall windows and {EXPECTED_NONFALL} non-fall windows.", "Decision rule: predict fall when fall score >= threshold.", "", "## Best PGD Test Operating Points"]
    for cap in FAR_CAPS:
        r = best.get(cap)
        if r is None:
            lines.append(f"- At FAR <= {cap:.2f}, no PGD test score row was available.")
        else:
            lines.append(f"- At FAR <= {cap:.2f}, best recall is {r['recall']:.3f} with TP/FP {int(r['TP'])}/{int(r['FP'])}. Full point: FN={int(r['FN'])}, TN={int(r['TN'])}, FAR={r['FAR']:.3f}, threshold={r['threshold']:.6g}, AUROC={r['auroc']:.3f}, candidate={r['candidate']}.")
    reached10 = best.get(0.10) is not None and best[0.10]["recall"] >= TARGET_RECALL
    reached20 = best.get(0.20) is not None and best[0.20]["recall"] >= TARGET_RECALL
    lines += [f"- Target recall >= 0.80 reached at FAR <= 0.10? {'yes' if reached10 else 'no'}.", f"- Target recall >= 0.80 reached at FAR <= 0.20? {'yes' if reached20 else 'no'}.", "", "## PGD Test Candidates", md_table(summary, "test"), "", "## Validation-Only Comparators", md_table(summary, "val"), "", "## Score Availability"]
    lines.extend(availability_notes())
    if errors:
        lines += ["", "## Skipped Files"] + [f"- {e}" for e in errors]
    (OUT / "operating_region_summary.md").write_text("\n".join(lines), encoding="utf-8")

    write_figure(summary, curves)


def write_figure(summary: pd.DataFrame, curves: dict):
    OUT.mkdir(parents=True, exist_ok=True)
    plt.style.use("default")
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.titlesize": 16,
        "axes.labelsize": 13,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "legend.fontsize": 9,
        "legend.title_fontsize": 10,
    })

    test_names = summary[(summary["split"] == "test") & (summary["condition"] == "pgd") & (summary["far_cap"] == 0.20)].sort_values(["recall", "FP", "auroc"], ascending=[False, True, False]).head(10)["candidate"].tolist()
    fig, ax = plt.subplots(figsize=(12.5, 7.2), constrained_layout=True)
    for name in test_names:
        c = curves[name].sort_values("FAR")
        ax.step(c["FAR"], c["recall"], where="post", linewidth=1.9, alpha=0.95, label=name)

    ax.axvline(0.10, color="black", linestyle="--", linewidth=1.2, alpha=0.72)
    ax.axvline(0.20, color="black", linestyle="--", linewidth=1.2, alpha=0.72)
    ax.axhline(TARGET_RECALL, color="tab:red", linestyle="--", linewidth=1.4, alpha=0.82)
    ax.text(0.10, 1.005, "FAR = 0.10", rotation=90, ha="right", va="top", fontsize=10)
    ax.text(0.20, 1.005, "FAR = 0.20", rotation=90, ha="right", va="top", fontsize=10)
    ax.text(0.302, TARGET_RECALL, "R_fall = 0.80", ha="right", va="bottom", color="tab:red", fontsize=10)

    best = best_rows(summary)
    point_styles = {
        0.10: {
            "label": "Best FAR <= 0.10\nR=0.356, TP=16, FP=45",
            "xytext": (0.035, 0.47),
            "color": "tab:blue",
        },
        0.20: {
            "label": "Best FAR <= 0.20\nR=0.800, TP=36, FP=91",
            "xytext": (0.145, 0.91),
            "color": "tab:red",
        },
    }
    for cap, style in point_styles.items():
        r = best.get(cap)
        if r is None:
            continue
        ax.scatter([r["FAR"]], [r["recall"]], s=78, color=style["color"], edgecolor="white", linewidth=1.2, zorder=6)
        ax.annotate(
            style["label"],
            xy=(r["FAR"], r["recall"]),
            xytext=style["xytext"],
            textcoords="data",
            arrowprops={"arrowstyle": "->", "color": style["color"], "lw": 1.2},
            bbox={"boxstyle": "round,pad=0.28", "fc": "white", "ec": style["color"], "alpha": 0.94},
            fontsize=10,
            color="black",
        )

    ax.set_xlim(0, 0.30)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("False-fall alarm rate, FAR = FP / (FP + TN)")
    ax.set_ylabel("Fall recall, R_fall = TP / (TP + FN)")
    ax.set_title("PGD Operating-Region Characterization at epsilon = 0.030", pad=14)
    ax.grid(True, color="#d9d9d9", linewidth=0.8, alpha=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(title="Candidate", loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
    fig.savefig(OUT / "operating_region_recall_far_curve.png", dpi=220, facecolor="white", bbox_inches="tight", pad_inches=0.2)
    fig.savefig(OUT / "operating_region_recall_far_curve_thesis.png", dpi=420, facecolor="white", bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)


def parse_args():
    parser = argparse.ArgumentParser(description="Operating-region characterization from existing score CSVs.")
    parser.add_argument("--figure-only", action="store_true", help="Regenerate only the operating-region figures.")
    return parser.parse_args()

def main():
    args = parse_args()
    summary, curves, errors = analyze()
    if args.figure_only:
        write_figure(summary, curves)
    else:
        write_outputs(summary, curves, errors)
    best = best_rows(summary)
    for cap in FAR_CAPS:
        r = best.get(cap)
        if r is not None:
            print(f"At FAR <= {cap:.2f}, best recall is {r['recall']:.3f} with TP/FP {int(r['TP'])}/{int(r['FP'])}.")
    print(f"Target recall >= 0.80 reached at FAR <= 0.10? {'yes' if best.get(0.10) is not None and best[0.10]['recall'] >= TARGET_RECALL else 'no'}.")
    print(f"Target recall >= 0.80 reached at FAR <= 0.20? {'yes' if best.get(0.20) is not None and best[0.20]['recall'] >= TARGET_RECALL else 'no'}.")


if __name__ == "__main__":
    main()
