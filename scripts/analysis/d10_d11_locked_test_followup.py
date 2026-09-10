"""
D10/D11 locked held-out test follow-up (analysis only).

Protocol (pre-registered, validation/test discipline):
  1. For each method (D10 GAIRAT GR1_v2macroF1, D11a Stage-1/BASAT ST1b6_v2lowFA,
     D11b SAT SA1_v2lowFA), thresholds are selected ONLY on the existing
     validation PGD (epsilon=0.030, eval PGD-10 alpha=eps/6) fall-probability
     exports: for each FAR cap in {0.20, 0.15, 0.10}, choose the threshold that
     maximizes validation fall recall subject to validation FAR <= cap
     (tie-break: lower FAR, then higher threshold).
  2. Thresholds are then FROZEN and applied exactly once to the newly exported
     held-out 500-window test PGD scores. No threshold is changed after seeing
     test results; this script computes selection and application in one pass
     with no test feedback into selection.

Evidence type produced: held-out test with frozen validation-selected
thresholds (window-level, digital-domain, PGD epsilon=0.030 eval PGD-10).
Claim boundary: not clinical, not deployment-validated, not certified.
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "d10_d11_locked_test_followup"
BASE = REPO / "results" / "safety_guided_defense" / "boundary_aware_selective_at"
TEST_EVAL = OUT / "test_eval"

FAR_CAPS = [0.20, 0.15, 0.10]

METHODS = [
    {
        "id": "D10",
        "desc": "GAIRAT-style boundary reweighting (GR1, v2macroF1 checkpoint)",
        "run_name": "GR1_v2macroF1",
        "val_csv": BASE / "gairat" / "seed42" / "GR1" / "val_eval"
        / "GR1_v2macroF1_pgd_probabilities_val_epsilon_0_03.csv",
        "checkpoint": "checkpoints/safety_guided_defense/boundary_aware_selective_at/"
        "gairat/seed42/GR1/seed42_basat_gairat_GR1_v2macroF1_best.pt",
    },
    {
        "id": "D11a",
        "desc": "SAT-style selective filtering, internal Stage-1/BASAT pilot "
        "(beta6p0, v2lowFA checkpoint)",
        "run_name": "ST1b6_v2lowFA",
        "val_csv": BASE / "seed42" / "beta6p0" / "val_eval"
        / "ST1b6_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv",
        "checkpoint": "checkpoints/safety_guided_defense/boundary_aware_selective_at/"
        "seed42/beta6p0/seed42_basat_stage1_beta6p0_v2lowFA_best.pt",
    },
    {
        "id": "D11b",
        "desc": "SAT-style selective filtering pilot (SA1, v2lowFA checkpoint)",
        "run_name": "SA1_v2lowFA",
        "val_csv": BASE / "sat" / "seed42" / "SA1" / "val_eval"
        / "SA1_v2lowFA_pgd_probabilities_val_epsilon_0_03.csv",
        "checkpoint": "checkpoints/safety_guided_defense/boundary_aware_selective_at/"
        "sat/seed42/SA1/seed42_basat_sat_SA1_v2lowFA_best.pt",
    },
]

D8B_REFERENCE = {
    "method_id": "D8b (reference)",
    "method_desc": "AFAC-score (optionB_maxscore seed42), held-out test post-hoc FAR sweep",
    "evidence_type": "test post-hoc FAR sweep (NOT frozen-threshold protocol)",
    "far_cap": 0.20,
    "threshold": 0.153246,
    "TP": 36, "FN": 9, "FP": 91, "TN": 364,
    "recall": 0.8000, "FAR": 0.2000, "AUROC": 0.8439,
}


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
    """Rank-based AUROC (Mann-Whitney U) with tie correction."""
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
    """Max validation recall s.t. FAR <= cap; tie-break lower FAR, then higher tau."""
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
        raise ValueError(f"no threshold satisfies FAR <= {cap} on validation")
    _, tau, tp, fn, fp, tn, recall, far = best
    return tau, tp, fn, fp, tn, recall, far


def check_split(name, y, n_total, n_fall):
    if len(y) != n_total or sum(y) != n_fall:
        raise AssertionError(
            f"{name}: expected {n_total} windows / {n_fall} falls, "
            f"got {len(y)} / {sum(y)}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sel_rows, test_rows_out, fp_rows, fn_rows = [], [], [], []

    for m in METHODS:
        test_csv = TEST_EVAL / (
            f"{m['run_name']}_pgd_probabilities_test_epsilon_0_03.csv")
        vy, vs, _, _ = extract(load_rows(m["val_csv"]))
        ty, ts, t_true_cls, t_pred_cls = extract(load_rows(test_csv))
        check_split(f"{m['id']} val", vy, 496, 44)
        check_split(f"{m['id']} test", ty, 500, 45)

        test_auroc = auroc(ty, ts)
        val_auroc = auroc(vy, vs)

        for cap in FAR_CAPS:
            tau, vtp, vfn, vfp, vtn, vrec, vfar = select_threshold(vy, vs, cap)
            sel_rows.append({
                "method_id": m["id"], "method_desc": m["desc"],
                "run_name": m["run_name"], "far_cap": cap,
                "selection_split": "val", "attack": "pgd", "epsilon": 0.03,
                "selected_threshold": f"{tau:.6f}",
                "val_TP": vtp, "val_FN": vfn, "val_FP": vfp, "val_TN": vtn,
                "val_recall": f"{vrec:.6f}", "val_FAR": f"{vfar:.6f}",
                "val_AUROC": f"{val_auroc:.6f}",
            })

            ttp, tfn, tfp, ttn = confusion(ty, ts, tau)
            trec, tfar, tprec, tf1 = rates(ttp, tfn, tfp, ttn)
            f20 = trec >= 0.80 and tfar <= 0.20
            r90f10 = trec >= 0.90 and tfar <= 0.10
            test_rows_out.append({
                "method_id": m["id"], "method_desc": m["desc"],
                "run_name": m["run_name"],
                "evidence_type": "held-out test, frozen validation-selected threshold",
                "threshold_selection_split": "val",
                "final_evaluation_split": "test",
                "attack": "pgd", "epsilon": 0.03, "far_cap": cap,
                "selected_threshold": f"{tau:.6f}",
                "val_recall_at_threshold": f"{vrec:.6f}",
                "val_FAR_at_threshold": f"{vfar:.6f}",
                "test_TP": ttp, "test_FN": tfn, "test_FP": tfp, "test_TN": ttn,
                "test_recall": f"{trec:.6f}", "test_FAR": f"{tfar:.6f}",
                "test_precision": f"{tprec:.6f}", "test_F1": f"{tf1:.6f}",
                "test_AUROC": f"{test_auroc:.6f}",
                "F20_met": f20, "R90F10_met": r90f10,
            })

            # false-alarm source classes and missed-fall destination classes
            fp_counts, fn_counts = {}, {}
            for yi, si, tc, pc in zip(ty, ts, t_true_cls, t_pred_cls):
                if yi == 0 and si >= tau:
                    fp_counts[tc] = fp_counts.get(tc, 0) + 1
                elif yi == 1 and si < tau:
                    fn_counts[pc] = fn_counts.get(pc, 0) + 1
            for cls, cnt in sorted(fp_counts.items(), key=lambda kv: -kv[1]):
                fp_rows.append({"method_id": m["id"], "far_cap": cap,
                                "threshold": f"{tau:.6f}",
                                "true_source_class": cls, "false_alarm_count": cnt})
            for cls, cnt in sorted(fn_counts.items(), key=lambda kv: -kv[1]):
                fn_rows.append({"method_id": m["id"], "far_cap": cap,
                                "threshold": f"{tau:.6f}",
                                "argmax_destination_class": cls,
                                "missed_fall_count": cnt})

    def write_csv(path, rows):
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"[write] {path.relative_to(REPO)} ({len(rows)} rows)")

    write_csv(OUT / "d10_d11_threshold_selection_validation.csv", sel_rows)
    write_csv(OUT / "d10_d11_test_metrics_by_far_cap.csv", test_rows_out)
    if fp_rows:
        write_csv(OUT / "d10_d11_false_alarm_source_breakdown.csv", fp_rows)
    if fn_rows:
        write_csv(OUT / "d10_d11_missed_fall_destination_breakdown.csv", fn_rows)

    # summary CSV: D8b reference + frozen-threshold test rows
    summary = [{
        "method_id": D8B_REFERENCE["method_id"],
        "method_desc": D8B_REFERENCE["method_desc"],
        "evidence_type": D8B_REFERENCE["evidence_type"],
        "far_cap": D8B_REFERENCE["far_cap"],
        "threshold": D8B_REFERENCE["threshold"],
        "test_TP": D8B_REFERENCE["TP"], "test_FN": D8B_REFERENCE["FN"],
        "test_FP": D8B_REFERENCE["FP"], "test_TN": D8B_REFERENCE["TN"],
        "test_recall": D8B_REFERENCE["recall"], "test_FAR": D8B_REFERENCE["FAR"],
        "test_AUROC": D8B_REFERENCE["AUROC"],
        "F20_met": True, "R90F10_met": False,
    }]
    for r in test_rows_out:
        summary.append({
            "method_id": r["method_id"], "method_desc": r["method_desc"],
            "evidence_type": r["evidence_type"], "far_cap": r["far_cap"],
            "threshold": r["selected_threshold"],
            "test_TP": r["test_TP"], "test_FN": r["test_FN"],
            "test_FP": r["test_FP"], "test_TN": r["test_TN"],
            "test_recall": r["test_recall"], "test_FAR": r["test_FAR"],
            "test_AUROC": r["test_AUROC"],
            "F20_met": r["F20_met"], "R90F10_met": r["R90F10_met"],
        })
    write_csv(OUT / "d10_d11_locked_test_summary.csv", summary)
    print("[done] locked-test follow-up analysis complete")


if __name__ == "__main__":
    main()
