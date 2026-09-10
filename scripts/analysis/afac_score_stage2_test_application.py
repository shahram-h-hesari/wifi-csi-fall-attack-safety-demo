"""
AFAC-score (optionB maxscore) Stage 2 — single-shot application of the FROZEN Stage 1
validation-selected thresholds to the existing held-out test PGD scores.

This script contains NO threshold-selection logic. The four thresholds below were frozen in
Stage 1 (scripts/analysis/afac_score_stage1_validation_selection.py, run against validation only)
and are hard-coded here exactly as selected. They are not recomputed, adjusted, or re-derived from
any test data in this script.

Reuses the existing Gate-5 test score exports; no new test-split inference is performed.
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "afac_score_frozen_threshold_followup"
TEST_DIR = (REPO / "results" / "safety_guided_defense" / "variantH_dual_tail_budget"
            / "adaptive_lagrangian_far_constrained" / "optionB" / "seed42" / "test_eval")
TEST_PGD_CSV = TEST_DIR / "optionB_maxscore_pgd_probabilities_test_epsilon_0_03.csv"
TEST_CLEAN_CSV = TEST_DIR / "optionB_maxscore_clean_probabilities_test_epsilon_0_03.csv"

# FROZEN in Stage 1 (validation-only). DO NOT MODIFY. DO NOT RESELECT.
FROZEN_THRESHOLDS = [
    {"far_cap": 0.18, "role": "primary", "threshold": 0.170908,
     "val_recall": 0.772727, "val_far": 0.157080},
    {"far_cap": 0.20, "role": "comparison", "threshold": 0.147881,
     "val_recall": 0.818182, "val_far": 0.194690},
    {"far_cap": 0.15, "role": "diagnostic", "threshold": 0.181992,
     "val_recall": 0.704545, "val_far": 0.143805},
    {"far_cap": 0.10, "role": "r90f10_diagnostic", "threshold": 0.234373,
     "val_recall": 0.386364, "val_far": 0.090708},
]

D8B_REFERENCE = {
    "method_id": "D8b (reference)",
    "evidence_type": "test post-hoc FAR sweep (NOT frozen-threshold protocol)",
    "threshold": 0.153246, "TP": 36, "FN": 9, "FP": 91, "TN": 364,
    "recall": 0.8000, "FAR": 0.2000, "AUROC": 0.8439,
}
D10_D11_LOCKED = [
    {"method_id": "D10 (locked, FAR cap 0.20)", "threshold": None,
     "TP": 34, "FN": 11, "FP": 93, "TN": 362, "recall": 0.7556, "FAR": 0.2044},
    {"method_id": "D11a (locked, FAR cap 0.20)", "threshold": None,
     "TP": 31, "FN": 14, "FP": 102, "TN": 353, "recall": 0.6889, "FAR": 0.2242},
    {"method_id": "D11b (locked, FAR cap 0.20)", "threshold": None,
     "TP": 34, "FN": 11, "FP": 98, "TN": 357, "recall": 0.7556, "FAR": 0.2154},
]


def load_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"empty CSV: {path}")
    return rows


def extract(rows):
    y = [int(r["fall_true_binary"]) for r in rows]
    s = [float(r["fall_probability"]) for r in rows]
    true_cls = [r["true_class_name"] for r in rows]
    pred_cls = [r["predicted_class_name"] for r in rows]
    return y, s, true_cls, pred_cls


def check_split(y, n_total, n_fall, label):
    if len(y) != n_total or sum(y) != n_fall:
        raise AssertionError(
            f"{label}: expected {n_total} windows / {n_fall} falls, "
            f"got {len(y)} / {sum(y)}")


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


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    pgd_rows = load_rows(TEST_PGD_CSV)
    ty, ts, t_true_cls, t_pred_cls = extract(pgd_rows)
    check_split(ty, 500, 45, "test PGD")

    clean_rows = load_rows(TEST_CLEAN_CSV)
    cy, cs, _, _ = extract(clean_rows)
    check_split(cy, 500, 45, "test clean")

    test_auroc = auroc(ty, ts)

    metrics_rows = []
    fp_rows = []
    fn_rows = []
    clean_rows_out = []

    for spec in FROZEN_THRESHOLDS:
        tau = spec["threshold"]
        tp, fn, fp, tn = confusion(ty, ts, tau)
        recall, far, precision, f1 = rates(tp, fn, fp, tn)
        f20 = recall >= 0.80 and far <= 0.20
        r90f10 = recall >= 0.90 and far <= 0.10

        metrics_rows.append({
            "far_cap": spec["far_cap"], "role": spec["role"],
            "frozen_threshold": f"{tau:.6f}",
            "val_recall_at_threshold": f"{spec['val_recall']:.6f}",
            "val_FAR_at_threshold": f"{spec['val_far']:.6f}",
            "test_TP": tp, "test_FN": fn, "test_FP": fp, "test_TN": tn,
            "test_recall": f"{recall:.6f}", "test_FAR": f"{far:.6f}",
            "test_precision": f"{precision:.6f}", "test_F1": f"{f1:.6f}",
            "test_AUROC": f"{test_auroc:.6f}",
            "F20_met": f20, "R90F10_met": r90f10,
        })

        # clean-condition check at the primary threshold only
        if spec["role"] == "primary":
            ctp, cfn, cfp, ctn = confusion(cy, cs, tau)
            crecall, cfar, cprec, cf1 = rates(ctp, cfn, cfp, ctn)
            clean_rows_out.append({
                "far_cap": spec["far_cap"], "role": spec["role"],
                "frozen_threshold": f"{tau:.6f}",
                "clean_TP": ctp, "clean_FN": cfn, "clean_FP": cfp, "clean_TN": ctn,
                "clean_recall": f"{crecall:.6f}", "clean_FAR": f"{cfar:.6f}",
                "clean_precision": f"{cprec:.6f}", "clean_F1": f"{cf1:.6f}",
            })

        # error breakdowns
        fp_counts, fn_counts = {}, {}
        for yi, si, tc, pc in zip(ty, ts, t_true_cls, t_pred_cls):
            if yi == 0 and si >= tau:
                fp_counts[tc] = fp_counts.get(tc, 0) + 1
            elif yi == 1 and si < tau:
                fn_counts[pc] = fn_counts.get(pc, 0) + 1
        for cls, cnt in sorted(fp_counts.items(), key=lambda kv: -kv[1]):
            fp_rows.append({"far_cap": spec["far_cap"], "role": spec["role"],
                            "threshold": f"{tau:.6f}",
                            "true_source_class": cls, "false_alarm_count": cnt})
        for cls, cnt in sorted(fn_counts.items(), key=lambda kv: -kv[1]):
            fn_rows.append({"far_cap": spec["far_cap"], "role": spec["role"],
                            "threshold": f"{tau:.6f}",
                            "argmax_destination_class": cls,
                            "missed_fall_count": cnt})

    def write_csv(path, rows):
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"[write] {path.relative_to(REPO)} ({len(rows)} rows)")

    write_csv(OUT / "afac_score_test_metrics_by_far_cap.csv", metrics_rows)
    write_csv(OUT / "afac_score_false_alarm_source_breakdown.csv", fp_rows)
    write_csv(OUT / "afac_score_missed_fall_destination_breakdown.csv", fn_rows)
    if clean_rows_out:
        write_csv(OUT / "afac_score_clean_condition_at_primary_threshold.csv", clean_rows_out)

    # comparison summary: AFAC frozen rows + D8b reference + D10/D11 locked rows
    summary = [{
        "method_id": D8B_REFERENCE["method_id"],
        "evidence_type": D8B_REFERENCE["evidence_type"],
        "threshold": D8B_REFERENCE["threshold"],
        "test_TP": D8B_REFERENCE["TP"], "test_FN": D8B_REFERENCE["FN"],
        "test_FP": D8B_REFERENCE["FP"], "test_TN": D8B_REFERENCE["TN"],
        "test_recall": D8B_REFERENCE["recall"], "test_FAR": D8B_REFERENCE["FAR"],
        "test_AUROC": D8B_REFERENCE["AUROC"], "F20_met": True, "R90F10_met": False,
    }]
    for r in D10_D11_LOCKED:
        summary.append({
            "method_id": r["method_id"], "evidence_type": "held-out test, frozen validation-selected threshold",
            "threshold": r["threshold"], "test_TP": r["TP"], "test_FN": r["FN"],
            "test_FP": r["FP"], "test_TN": r["TN"], "test_recall": r["recall"],
            "test_FAR": r["FAR"], "test_AUROC": "", "F20_met": False, "R90F10_met": False,
        })
    for m in metrics_rows:
        summary.append({
            "method_id": f"AFAC-score ({m['role']}, FAR cap {m['far_cap']})",
            "evidence_type": "held-out test, frozen validation-selected threshold",
            "threshold": m["frozen_threshold"],
            "test_TP": m["test_TP"], "test_FN": m["test_FN"],
            "test_FP": m["test_FP"], "test_TN": m["test_TN"],
            "test_recall": m["test_recall"], "test_FAR": m["test_FAR"],
            "test_AUROC": m["test_AUROC"], "F20_met": m["F20_met"],
            "R90F10_met": m["R90F10_met"],
        })
    write_csv(OUT / "afac_score_frozen_threshold_summary.csv", summary)

    print(f"[info] test-split overall AUROC (PGD) = {test_auroc:.6f}")
    print("[done] Stage 2 test application complete. Thresholds were NOT modified or reselected.")


if __name__ == "__main__":
    main()
