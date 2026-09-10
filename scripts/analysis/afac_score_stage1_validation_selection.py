"""
AFAC-score (optionB maxscore) Stage 1 — VALIDATION-ONLY threshold selection.

Purpose: select and freeze fall-score thresholds for FAR caps {0.18 (primary), 0.20, 0.15, 0.10}
using ONLY the validation PGD score export. Does not read, open, or reference any test-split file.
This script is the selection step of the two-stage AFAC-score frozen-threshold protocol described
in results/afac_score_frozen_threshold_followup/AFAC_PRE_RUN_STRATEGY.md. Stage 2 (test
application) is a separate script, run only after Shahram approves the frozen thresholds below.

Threshold rule: maximize validation fall recall subject to validation FAR <= cap;
tie-break 1 = lower validation FAR; tie-break 2 = higher threshold.

No test file path appears anywhere in this script (grep-verifiable).
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "afac_score_frozen_threshold_followup"
VAL_CSV = OUT / "val_eval" / "optionB_maxscore_pgd_probabilities_val_epsilon_0_03.csv"

FAR_CAPS = [0.18, 0.20, 0.15, 0.10]  # 0.18 primary listed first; all four reported
N_BOOTSTRAP = 2000
BOOTSTRAP_SEED = 20260704


def load_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"empty CSV: {path}")
    return rows


def extract(rows):
    y = [int(r["fall_true_binary"]) for r in rows]
    s = [float(r["fall_probability"]) for r in rows]
    return y, s


def confusion(y, s, tau):
    tp = fn = fp = tn = 0
    for yi, si in zip(y, s):
        pred = si >= tau
        if yi == 1:
            tp += pred
            fn += not pred
        else:
            fp += pred
            tn += not pred
    return tp, fn, fp, tn


def rates(tp, fn, fp, tn):
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    far = fp / (fp + tn) if (fp + tn) else float("nan")
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) > 0 else 0.0)
    return recall, far, precision, f1


def auroc(y, s):
    pairs = sorted(zip(s, y))
    n = len(pairs)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        i = j + 1
    n_pos = sum(yy for _, yy in pairs)
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    rank_sum_pos = sum(r for r, (_, yy) in zip(ranks, pairs) if yy == 1)
    u = rank_sum_pos - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * n_neg)


def select_threshold(y, s, cap):
    """Max recall s.t. FAR <= cap; tie-break lower FAR, then higher tau."""
    best = None
    for tau in sorted(set(s), reverse=True):
        tp, fn, fp, tn = confusion(y, s, tau)
        recall, far, _, _ = rates(tp, fn, fp, tn)
        if far > cap:
            continue
        key = (recall, -far, tau)
        if best is None or key > best[0]:
            best = (key, tau, tp, fn, fp, tn, recall, far)
    if best is None:
        return None
    _, tau, tp, fn, fp, tn, recall, far = best
    return tau, tp, fn, fp, tn, recall, far


def check_split(y, n_total, n_fall):
    if len(y) != n_total or sum(y) != n_fall:
        raise AssertionError(
            f"validation split mismatch: expected {n_total} windows / {n_fall} falls, "
            f"got {len(y)} / {sum(y)}")


def bootstrap_stability(y, s, cap, n_boot=N_BOOTSTRAP, seed=BOOTSTRAP_SEED):
    """Stratified bootstrap (resample fall and non-fall windows separately) to
    quantify threshold and FAR uncertainty at a given cap. Validation only."""
    rng = random.Random(seed)
    fall_idx = [i for i, yi in enumerate(y) if yi == 1]
    nonfall_idx = [i for i, yi in enumerate(y) if yi == 0]
    thresholds, recalls, fars = [], [], []
    for _ in range(n_boot):
        f_sample = [rng.choice(fall_idx) for _ in fall_idx]
        nf_sample = [rng.choice(nonfall_idx) for _ in nonfall_idx]
        idx = f_sample + nf_sample
        yb = [y[i] for i in idx]
        sb = [s[i] for i in idx]
        sel = select_threshold(yb, sb, cap)
        if sel is None:
            continue
        tau, _, _, _, _, recall, far = sel
        thresholds.append(tau)
        recalls.append(recall)
        fars.append(far)
    thresholds.sort()
    recalls.sort()
    n = len(thresholds)
    if n == 0:
        return None
    lo, hi = int(0.025 * n), min(int(0.975 * n), n - 1)
    return {
        "n_boot_valid": n,
        "threshold_median": thresholds[n // 2],
        "threshold_ci95_lo": thresholds[lo],
        "threshold_ci95_hi": thresholds[hi],
        "recall_median": recalls[n // 2],
        "recall_ci95_lo": recalls[lo],
        "recall_ci95_hi": recalls[hi],
    }


def main():
    val_rows = load_rows(VAL_CSV)
    y, s = extract(val_rows)
    check_split(y, 496, 44)
    n_nonfall = len(y) - sum(y)
    print(f"[check] validation split OK: {len(y)} windows, {sum(y)} fall, {n_nonfall} non-fall")

    val_auroc = auroc(y, s)

    selection_rows = []
    bootstrap_rows = []
    for cap in FAR_CAPS:
        sel = select_threshold(y, s, cap)
        primary_flag = (cap == 0.18)
        if sel is None:
            selection_rows.append({
                "far_cap": cap, "is_primary": primary_flag, "selected_threshold": "",
                "val_TP": "", "val_FN": "", "val_FP": "", "val_TN": "",
                "val_recall": "", "val_FAR": "", "val_precision": "", "val_F1": "",
                "val_AUROC_overall": f"{val_auroc:.6f}",
                "note": "no threshold satisfies this FAR cap on validation",
            })
            continue
        tau, tp, fn, fp, tn, recall, far = sel
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        f1 = (2 * precision * recall / (precision + recall)
              if (precision + recall) > 0 else 0.0)
        selection_rows.append({
            "far_cap": cap, "is_primary": primary_flag,
            "selected_threshold": f"{tau:.6f}",
            "val_TP": tp, "val_FN": fn, "val_FP": fp, "val_TN": tn,
            "val_recall": f"{recall:.6f}", "val_FAR": f"{far:.6f}",
            "val_precision": f"{precision:.6f}", "val_F1": f"{f1:.6f}",
            "val_AUROC_overall": f"{val_auroc:.6f}",
            "note": "",
        })

        boot = bootstrap_stability(y, s, cap)
        if boot is not None:
            bootstrap_rows.append({"far_cap": cap, "is_primary": primary_flag, **boot})

    def write_csv(path, rows):
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"[write] {path.relative_to(REPO)} ({len(rows)} rows)")

    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "afac_score_threshold_selection_validation.csv", selection_rows)
    if bootstrap_rows:
        write_csv(OUT / "afac_score_bootstrap_stability_validation.csv", bootstrap_rows)

    # Frontier: recall/FAR at every distinct validation score, for inspection
    frontier_rows = []
    for tau in sorted(set(s), reverse=True):
        tp, fn, fp, tn = confusion(y, s, tau)
        recall, far, precision, f1 = rates(tp, fn, fp, tn)
        frontier_rows.append({
            "threshold": f"{tau:.6f}", "TP": tp, "FN": fn, "FP": fp, "TN": tn,
            "recall": f"{recall:.6f}", "FAR": f"{far:.6f}",
            "precision": f"{precision:.6f}", "F1": f"{f1:.6f}",
        })
    write_csv(OUT / "afac_score_validation_frontier.csv", frontier_rows)

    print(f"[info] validation-only overall AUROC = {val_auroc:.6f}")
    print("[done] Stage 1 validation-only selection complete. NO test file was read.")


if __name__ == "__main__":
    main()
