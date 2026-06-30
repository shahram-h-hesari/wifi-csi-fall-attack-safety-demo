"""
DS-SGE Stage A: post-hoc dual-specialist safety-gate calibration and analysis.

Purpose:
    ANALYSIS / LOGGING ONLY. Reads the committed per-window probability CSVs of a
    RECALL specialist (f_R) and a FALSE-ALARM-control specialist (f_B), both frozen
    LeNet checkpoints exported by `export_probability_predictions.py`, and tests
    whether the smooth safety gate

        S(x) = alpha * p_R(fall|x) + (1 - alpha) * p_B(fall|x),   fall <=> S(x) >= tau

    improves the empirical adversarial fall-recall vs false-alarm frontier over
    either specialist alone. NO training, NO model loading, NO attack generation
    here (the adaptive full-gate attack lives in a separate torch script).

Protocol (research-integrity rules, enforced in code):
    * (alpha, tau) are selected on VALIDATION ONLY, on the PGD@eps condition (the
      operative threat), maximizing validation fall recall s.t. validation
      FAR <= 0.10. The full grid is saved for audit; the locked point is applied
      to TEST exactly once.
    * The TEST split is never used for selection.
    * Splits are the committed UT-HAR splits (val 496 / test 500); sample_id
      ordering is identical across the two checkpoints (same deterministic loader
      + same --seed), verified by a true-label alignment assertion.

Scope: window-level, digital-domain, white-box, processed CSI; eps=0.030.
    NOT certified, NOT clinical, NOT deployment, NOT over-the-air.

Inputs (in --prob-dir):
    {R,B}_<tag>_{clean,fgsm,pgd}_probabilities_{val,test}_epsilon_0_03.csv

Outputs (in --out-dir):
    validation_probabilities.csv, test_probabilities.csv  (merged R||B, per cond,
        with entropy/margin/disagreement features)
    gate_grid_validation.csv      (full alpha x tau grid on val PGD)
    gate_config.json              (locked alpha,tau; feasibility; val metrics)
    metrics_clean.csv, metrics_fgsm_eps003.csv, metrics_pgd_eps003.csv  (locked
        TEST metrics for f_R-alone, f_B-alone, and the gate)
    error_overlap.csv             (complementarity of R vs B errors, per cond)
    frontier_points.csv           (recall/FAR points + gate val/test curves)

Commands:
    python scripts/gate_dual_specialist.py \
        --prob-dir results/safety_guided_defense/dual_specialist_safety_gate/A1/seed42/probabilities \
        --out-dir  results/safety_guided_defense/dual_specialist_safety_gate/A1/seed42 \
        --r-tag R_G1maxrec --b-tag B_G1lowFA --eps-token 0_03 \
        --recall-specialist seed42_variantG_G1_v2maxrec_best \
        --far-specialist    seed42_variantG_G1_v2lowFA_best
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json

import numpy as np
import pandas as pd


FALL_CLASS_INDEX = 1
FAR_BUDGET = 0.10
PROB_COLS = ["prob_lie_down", "prob_fall", "prob_walk", "prob_pickup",
             "prob_run", "prob_sit_down", "prob_stand_up"]
CONDITIONS = ["clean", "fgsm", "pgd"]


# --------------------------------------------------------------------------- #
# Loading + per-window feature construction
# --------------------------------------------------------------------------- #
def _entropy(p: np.ndarray) -> np.ndarray:
    """Row-wise Shannon entropy (nats) of a probability matrix."""
    p = np.clip(p, 1e-12, 1.0)
    return -(p * np.log(p)).sum(axis=1)


def _margin(p: np.ndarray) -> np.ndarray:
    """Row-wise top1 - top2 probability margin (confidence margin)."""
    s = np.sort(p, axis=1)
    return s[:, -1] - s[:, -2]


def load_condition(prob_dir: Path, tag: str, cond: str, split: str, eps_token: str) -> pd.DataFrame:
    f = prob_dir / f"{tag}_{cond}_probabilities_{split}_epsilon_{eps_token}.csv"
    if not f.exists():
        raise FileNotFoundError(f"Missing probability CSV: {f}")
    df = pd.read_csv(f)
    probs = df[PROB_COLS].to_numpy()
    out = pd.DataFrame({
        "sample_id": df["sample_id"].astype(int),
        "true_label": df["true_label"].astype(int),
        "fall_true_binary": df["fall_true_binary"].astype(int),
        "p_fall": df["fall_probability"].astype(float),
        "pred_label": df["predicted_label"].astype(int),
        "fall_pred_binary": df["fall_pred_binary"].astype(int),
        "entropy": _entropy(probs),
        "margin": _margin(probs),
    })
    return out


def merge_specialists(prob_dir: Path, r_tag: str, b_tag: str, cond: str,
                      split: str, eps_token: str) -> pd.DataFrame:
    r = load_condition(prob_dir, r_tag, cond, split, eps_token)
    b = load_condition(prob_dir, b_tag, cond, split, eps_token)
    m = r.merge(b, on="sample_id", suffixes=("_R", "_B"))
    if len(m) != len(r) or len(m) != len(b):
        raise RuntimeError(f"sample_id merge mismatch ({split}/{cond}): "
                           f"R={len(r)} B={len(b)} merged={len(m)}")
    # Alignment check: the same window must carry the same true label in both.
    if not (m["true_label_R"] == m["true_label_B"]).all():
        raise RuntimeError(f"True-label misalignment between R and B ({split}/{cond}); "
                           "loaders are not identically ordered.")
    out = pd.DataFrame({
        "sample_id": m["sample_id"],
        "attack_type": cond,
        "split": split,
        "true_label": m["true_label_R"],
        "fall_true_binary": m["fall_true_binary_R"],
        "p_R_fall": m["p_fall_R"],
        "p_B_fall": m["p_fall_B"],
        "pred_R": m["pred_label_R"],
        "pred_B": m["pred_label_B"],
        "fall_pred_R": m["fall_pred_binary_R"],
        "fall_pred_B": m["fall_pred_binary_B"],
        "entropy_R": m["entropy_R"],
        "entropy_B": m["entropy_B"],
        "margin_R": m["margin_R"],
        "margin_B": m["margin_B"],
    })
    out["disagree_flag"] = (out["pred_R"] != out["pred_B"]).astype(int)
    out["fall_disagree_flag"] = (out["fall_pred_R"] != out["fall_pred_B"]).astype(int)
    return out


# --------------------------------------------------------------------------- #
# Binary fall metrics
# --------------------------------------------------------------------------- #
def binary_metrics(fall_true: np.ndarray, fall_pred: np.ndarray) -> dict:
    fall_true = fall_true.astype(bool)
    fall_pred = fall_pred.astype(bool)
    tp = int(( fall_true &  fall_pred).sum())
    fn = int(( fall_true & ~fall_pred).sum())
    fp = int((~fall_true &  fall_pred).sum())
    tn = int((~fall_true & ~fall_pred).sum())
    n_fall = tp + fn
    n_nonfall = fp + tn
    recall = tp / n_fall if n_fall else 0.0
    far = fp / n_nonfall if n_nonfall else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    acc = (tp + tn) / (tp + fn + fp + tn)
    return {"TP": tp, "FN": fn, "FP": fp, "TN": tn, "n_fall": n_fall,
            "n_nonfall": n_nonfall, "fall_recall": recall, "missed_fall_rate": 1 - recall,
            "false_alarm_rate": far, "fall_precision": precision, "fall_f1": f1,
            "binary_accuracy": acc}


def gate_decision(p_R: np.ndarray, p_B: np.ndarray, alpha: float, tau: float) -> np.ndarray:
    return (alpha * p_R + (1.0 - alpha) * p_B) >= tau


# --------------------------------------------------------------------------- #
# Validation-only grid search
# --------------------------------------------------------------------------- #
def grid_search(val_pgd: pd.DataFrame, step: float = 0.01) -> pd.DataFrame:
    p_R = val_pgd["p_R_fall"].to_numpy()
    p_B = val_pgd["p_B_fall"].to_numpy()
    y = val_pgd["fall_true_binary"].to_numpy().astype(bool)
    alphas = np.round(np.arange(0.0, 1.0 + 1e-9, step), 4)
    taus = np.round(np.arange(0.0, 1.0 + 1e-9, step), 4)
    rows = []
    for a in alphas:
        S = a * p_R + (1.0 - a) * p_B          # (N,)
        pred = S[:, None] >= taus[None, :]      # (N, T)
        tp = (y[:, None] & pred).sum(axis=0)
        fn = (y[:, None] & ~pred).sum(axis=0)
        fp = (~y[:, None] & pred).sum(axis=0)
        tn = (~y[:, None] & ~pred).sum(axis=0)
        n_fall = tp + fn
        n_nonfall = fp + tn
        recall = np.where(n_fall > 0, tp / np.maximum(n_fall, 1), 0.0)
        far = np.where(n_nonfall > 0, fp / np.maximum(n_nonfall, 1), 0.0)
        prec = np.where((tp + fp) > 0, tp / np.maximum(tp + fp, 1), 0.0)
        f1 = np.where((prec + recall) > 0, 2 * prec * recall / np.maximum(prec + recall, 1e-12), 0.0)
        acc = (tp + tn) / (tp + fn + fp + tn)
        for j, t in enumerate(taus):
            rows.append({"alpha": a, "tau": t, "TP": int(tp[j]), "FN": int(fn[j]),
                         "FP": int(fp[j]), "TN": int(tn[j]),
                         "fall_recall": float(recall[j]), "false_alarm_rate": float(far[j]),
                         "fall_precision": float(prec[j]), "fall_f1": float(f1[j]),
                         "binary_accuracy": float(acc[j])})
    return pd.DataFrame(rows)


def select_operating_point(grid: pd.DataFrame, far_budget: float = FAR_BUDGET) -> dict:
    feasible = grid[grid["false_alarm_rate"] <= far_budget + 1e-12].copy()
    constraint_met = len(feasible) > 0
    if constraint_met:
        pool = feasible
        # max recall, then precision, then F1, then accuracy, then lower tau
        pool = pool.sort_values(
            by=["fall_recall", "fall_precision", "fall_f1", "binary_accuracy", "tau"],
            ascending=[False, False, False, False, True])
    else:
        # no feasible point: min FAR, then max recall
        pool = grid.sort_values(by=["false_alarm_rate", "fall_recall"],
                                ascending=[True, False])
    best = pool.iloc[0]
    return {"alpha": float(best["alpha"]), "tau": float(best["tau"]),
            "constraint_met": bool(constraint_met),
            "val_pgd_metrics": {k: (float(best[k]) if k in ("fall_recall", "false_alarm_rate",
                                    "fall_precision", "fall_f1", "binary_accuracy") else int(best[k]))
                                for k in ("TP", "FN", "FP", "TN", "fall_recall",
                                          "false_alarm_rate", "fall_precision", "fall_f1",
                                          "binary_accuracy")}}


# --------------------------------------------------------------------------- #
# Error overlap (complementarity) — uses native argmax fall decisions
# --------------------------------------------------------------------------- #
def error_overlap(df: pd.DataFrame, alpha: float, tau: float) -> dict:
    fall = df["fall_true_binary"].to_numpy().astype(bool)
    nonfall = ~fall
    miss_R = fall & (df["fall_pred_R"].to_numpy() == 0)
    miss_B = fall & (df["fall_pred_B"].to_numpy() == 0)
    fa_R = nonfall & (df["fall_pred_R"].to_numpy() == 1)
    fa_B = nonfall & (df["fall_pred_B"].to_numpy() == 1)
    gate_pred = gate_decision(df["p_R_fall"].to_numpy(), df["p_B_fall"].to_numpy(), alpha, tau)
    # union/intersection of argmax detections (diagnostic recall ceiling)
    det_R = fall & (df["fall_pred_R"].to_numpy() == 1)
    det_B = fall & (df["fall_pred_B"].to_numpy() == 1)
    # falls missed by BOTH specialists (argmax) but flagged fall by the gate's prob threshold
    rescued = miss_R & miss_B & gate_pred
    return {
        "n_fall": int(fall.sum()), "n_nonfall": int(nonfall.sum()),
        "missed_by_R_only": int((miss_R & ~miss_B).sum()),
        "missed_by_B_only": int((miss_B & ~miss_R).sum()),
        "missed_by_both": int((miss_R & miss_B).sum()),
        "missed_falls_rescued_by_gate": int(rescued.sum()),
        "fa_by_R_only": int((fa_R & ~fa_B).sum()),
        "fa_by_B_only": int((fa_B & ~fa_R).sum()),
        "fa_by_both": int((fa_R & fa_B).sum()),
        "fa_suppressed_by_gate": int((nonfall & ((df["fall_pred_R"].to_numpy() == 1)
                                      | (df["fall_pred_B"].to_numpy() == 1)) & ~gate_pred).sum()),
        "argmax_union_recall": float((det_R | det_B).sum() / max(int(fall.sum()), 1)),
        "argmax_intersection_recall": float((det_R & det_B).sum() / max(int(fall.sum()), 1)),
        "recall_R_argmax": float(det_R.sum() / max(int(fall.sum()), 1)),
        "recall_B_argmax": float(det_B.sum() / max(int(fall.sum()), 1)),
    }


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def parse_args():
    p = argparse.ArgumentParser(description="DS-SGE Stage A post-hoc gate analysis (no torch).")
    p.add_argument("--prob-dir", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--r-tag", required=True, help="Filename tag of the recall specialist exports.")
    p.add_argument("--b-tag", required=True, help="Filename tag of the FAR specialist exports.")
    p.add_argument("--eps-token", default="0_03")
    p.add_argument("--recall-specialist", default="", help="Checkpoint name (metadata only).")
    p.add_argument("--far-specialist", default="", help="Checkpoint name (metadata only).")
    p.add_argument("--grid-step", type=float, default=0.01)
    return p.parse_args()


def main():
    args = parse_args()
    prob_dir = Path(args.prob_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Merge specialists for every split/condition.
    merged = {}
    for split in ("val", "test"):
        for cond in CONDITIONS:
            merged[(split, cond)] = merge_specialists(
                prob_dir, args.r_tag, args.b_tag, cond, split, args.eps_token)

    val_df = pd.concat([merged[("val", c)] for c in CONDITIONS], ignore_index=True)
    test_df = pd.concat([merged[("test", c)] for c in CONDITIONS], ignore_index=True)
    val_df.to_csv(out_dir / "validation_probabilities.csv", index=False)
    test_df.to_csv(out_dir / "test_probabilities.csv", index=False)

    # 2) Validation-only calibration on PGD.
    val_pgd = merged[("val", "pgd")]
    grid = grid_search(val_pgd, step=args.grid_step)
    grid.to_csv(out_dir / "gate_grid_validation.csv", index=False)
    sel = select_operating_point(grid, FAR_BUDGET)
    alpha, tau = sel["alpha"], sel["tau"]

    # Validation metrics at locked point for all conditions (reference).
    val_locked = {}
    for cond in CONDITIONS:
        d = merged[("val", cond)]
        pred = gate_decision(d["p_R_fall"].to_numpy(), d["p_B_fall"].to_numpy(), alpha, tau)
        val_locked[cond] = binary_metrics(d["fall_true_binary"].to_numpy(), pred)

    gate_config = {
        "method": "DS-SGE post-hoc smooth safety gate S=alpha*p_R+(1-alpha)*p_B, fall<=>S>=tau",
        "recall_specialist": args.recall_specialist,
        "far_specialist": args.far_specialist,
        "selection_split": "validation",
        "selection_condition": "pgd",
        "selection_epsilon": 0.030,
        "selection_rule": "max val fall recall s.t. val FAR<=0.10; tie-break precision,F1,acc,lower tau",
        "far_budget": FAR_BUDGET,
        "alpha": alpha, "tau": tau,
        "constraint_met": sel["constraint_met"],
        "val_pgd_metrics_at_locked_point": sel["val_pgd_metrics"],
        "val_locked_metrics_all_conditions": val_locked,
        "grid_step": args.grid_step,
        "scope": "window-level, digital-domain, white-box, processed CSI, eps=0.030; "
                 "NOT certified/clinical/deployment/OTA.",
    }
    with (out_dir / "gate_config.json").open("w", encoding="utf-8") as f:
        json.dump(gate_config, f, indent=2)

    # 3) Locked TEST evaluation: R-alone (argmax), B-alone (argmax), gate.
    metrics_files = {"clean": "metrics_clean.csv", "fgsm": "metrics_fgsm_eps003.csv",
                     "pgd": "metrics_pgd_eps003.csv"}
    frontier_rows = []
    for cond in CONDITIONS:
        d = merged[("test", cond)]
        rows = []
        r_alone = binary_metrics(d["fall_true_binary"].to_numpy(), d["fall_pred_R"].to_numpy())
        r_alone.update({"system": "f_R_alone_argmax", "attack": cond, "alpha": 1.0, "tau": np.nan})
        b_alone = binary_metrics(d["fall_true_binary"].to_numpy(), d["fall_pred_B"].to_numpy())
        b_alone.update({"system": "f_B_alone_argmax", "attack": cond, "alpha": 0.0, "tau": np.nan})
        gpred = gate_decision(d["p_R_fall"].to_numpy(), d["p_B_fall"].to_numpy(), alpha, tau)
        g = binary_metrics(d["fall_true_binary"].to_numpy(), gpred)
        g.update({"system": "DS_SGE_gate", "attack": cond, "alpha": alpha, "tau": tau})
        for r in (r_alone, b_alone, g):
            rows.append(r)
            frontier_rows.append({"attack": cond, "system": r["system"],
                                  "fall_recall": r["fall_recall"],
                                  "false_alarm_rate": r["false_alarm_rate"],
                                  "TP": r["TP"], "FP": r["FP"], "FN": r["FN"], "TN": r["TN"]})
        pd.DataFrame(rows).to_csv(out_dir / metrics_files[cond], index=False)

    pd.DataFrame(frontier_rows).to_csv(out_dir / "frontier_points.csv", index=False)

    # 4) Error overlap per condition (complementarity test).
    overlap_rows = []
    for split in ("val", "test"):
        for cond in CONDITIONS:
            ov = error_overlap(merged[(split, cond)], alpha, tau)
            ov.update({"split": split, "attack": cond})
            overlap_rows.append(ov)
    pd.DataFrame(overlap_rows).to_csv(out_dir / "error_overlap.csv", index=False)

    # 5) Console summary.
    print("=" * 78)
    print(f"DS-SGE Stage A — post-hoc gate (R={args.r_tag} x B={args.b_tag})")
    print("=" * 78)
    print(f"Locked (validation-PGD) operating point: alpha={alpha:.2f} tau={tau:.2f} "
          f"feasible={sel['constraint_met']}")
    vp = sel["val_pgd_metrics"]
    print(f"  VAL  PGD @locked: recall={vp['fall_recall']:.3f} FAR={vp['false_alarm_rate']:.3f} "
          f"TP={vp['TP']} FP={vp['FP']}")
    print("-" * 78)
    print(f"{'attack':6s} {'system':18s} {'recall':>7s} {'FAR':>7s} {'TP':>4s} {'FP':>4s} {'FN':>4s}")
    for r in frontier_rows:
        print(f"{r['attack']:6s} {r['system']:18s} {r['fall_recall']:7.3f} "
              f"{r['false_alarm_rate']:7.3f} {r['TP']:4d} {r['FP']:4d} {r['FN']:4d}")
    print("-" * 78)
    print("Error overlap (TEST, PGD) — the complementarity test:")
    ov = [o for o in overlap_rows if o["split"] == "test" and o["attack"] == "pgd"][0]
    print(f"  falls: missed_by_R_only={ov['missed_by_R_only']} missed_by_B_only={ov['missed_by_B_only']} "
          f"missed_by_both={ov['missed_by_both']} (n_fall={ov['n_fall']})")
    print(f"  recall R_argmax={ov['recall_R_argmax']:.3f} B_argmax={ov['recall_B_argmax']:.3f} "
          f"UNION={ov['argmax_union_recall']:.3f} INTERSECTION={ov['argmax_intersection_recall']:.3f}")
    print(f"  false alarms: R_only={ov['fa_by_R_only']} B_only={ov['fa_by_B_only']} both={ov['fa_by_both']}")
    print("=" * 78)
    print(f"Outputs written to: {out_dir}")


if __name__ == "__main__":
    main()
