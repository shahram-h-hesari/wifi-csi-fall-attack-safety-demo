"""
Variant F seed-42 pilot analysis: comparison, logit-margin geometry, Wilson CIs,
Pareto, FN:FP cost, and the pre-registered criteria scorecard.

Analysis only (reads existing test-eval CSVs; no training/attacks). Compares the Variant F
v2safety/v2lowFA candidates (all 3 lambda settings) against seed-42 references: Variant D safety,
prior Variant E safety, selection-v2 v2safety/v2lowFA, FGSM defense.

Outputs under results/safety_guided_defense/variantF_motion_margin/seed42/:
    variantF_seed42_comparison.csv
    analysis/logit_margin_geometry.csv
    analysis/wilson_intervals.csv
    analysis/criteria_scorecard.csv
    analysis/cost_curve.csv
    figures/fig_pareto_variantF.png

Command: python scripts/analyze_variantF.py
"""
from __future__ import annotations
from pathlib import Path
import csv, glob, math, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

EXP = Path(__file__).resolve().parents[1]
SG = EXP / "results" / "safety_guided_defense"
VF = SG / "variantF_motion_margin" / "seed42"
TE = VF / "test_eval"
FIG = VF / "figures"; ANA = VF / "analysis"
FIG.mkdir(parents=True, exist_ok=True); ANA.mkdir(parents=True, exist_ok=True)
CLASS = {0: "lie down", 1: "fall", 2: "walk", 3: "pickup", 4: "run", 5: "sit down", 6: "stand up"}
NONFALL = [0, 2, 3, 4, 5, 6]; WALK, RUN, FALL = 2, 4, 1
NFALL = 45
LOGIT = [f"logit_{CLASS[i].replace(' ', '_')}" for i in range(7)]

# selection-v2 v2safety seed42 reference (the bar Variant F must meet/beat)
REF = dict(recall=0.356, fp=117, walkrun=80, acc=0.806, f1=0.790)
VARIANTD_FP = 157  # seed42; 0.70x = 110


def rows(p):
    p = Path(p)
    if not p.exists():
        return None
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def kv(p):
    return {r["metric"]: r["value"] for r in (rows(p) or [])}


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def src_counts(rs, col):
    c = {k: 0 for k in NONFALL}
    for r in rs:
        if int(r["true_label"]) != FALL and int(r[col]) == FALL:
            c[int(r["true_label"])] += 1
    return c


def walkrun_margin(prob_csv):
    """median logit_fall - logit_true for residual walk/run false alarms (test PGD)."""
    rs = rows(prob_csv)
    if not rs:
        return float("nan"), 0
    vals = []
    for r in rs:
        t = int(r["true_label"]); p = int(r["predicted_label"])
        if t in (WALK, RUN) and p == FALL:
            vals.append(float(r["logit_fall"]) - float(r[LOGIT[t]]))
    return (float(np.median(vals)) if vals else float("nan")), len(vals)


def main():
    # reference run-name -> (predictions/metrics dir prefix, prob csv)
    refs = {
        "FGSM_defense": (EXP / "results" / "converged_attacks", "defended_fgsm_at_seed42", None),
        "D_safety": (SG / "seed42" / "test_eval", "variantD_bySafetyScore", SG / "seed42" / "test_eval" / "variantD_bySafetyScore_pgd_probabilities_test_epsilon_0_03.csv"),
        "priorE_safety": (SG / "variantE_motion_hard_negative" / "seed42" / "test_eval", "E_lam1p0_bySafetyScore", SG / "variantE_motion_hard_negative" / "seed42" / "test_eval" / "E_lam1p0_bySafetyScore_pgd_probabilities_test_epsilon_0_03.csv"),
        "selv2_v2safety": (SG / "variantE_motion_hard_negative" / "selection_v2" / "seed42" / "test_eval", "v2safety", SG / "variantE_motion_hard_negative" / "selection_v2" / "seed42" / "test_eval" / "v2safety_pgd_probabilities_test_epsilon_0_03.csv"),
        "selv2_v2lowFA": (SG / "variantE_motion_hard_negative" / "selection_v2" / "seed42" / "test_eval", "v2lowFA", None),
    }
    # discover Variant F eval run-names (single-eps pgd metrics)
    vf_runs = sorted(p.name.replace("_pgd_safety_metrics_test_epsilon_0_03.csv", "")
                     for p in TE.glob("*_pgd_safety_metrics_test_epsilon_0_03.csv")
                     if "_pgd20" not in p.name)

    # prior E walk/run margin reference
    priorE_margin, _ = walkrun_margin(refs["priorE_safety"][2])

    # ---- comparison + geometry + wilson ----
    comp = []
    for label, (d, run, prob) in refs.items():
        m = kv(Path(d) / f"{run}_pgd_safety_metrics_test_epsilon_0_03.csv")
        if not m:
            continue
        pgdpred = rows(Path(d) / f"{run}_pgd_predictions_test_epsilon_0_03.csv")
        col = "attacked_predicted_label"
        sc = src_counts(pgdpred, col) if pgdpred else {k: 0 for k in NONFALL}
        marg = walkrun_margin(prob)[0] if prob else float("nan")
        comp.append(dict(group="reference", label=label, recall=float(m["fall_recall"]),
                         fp=int(m["false_fall_alarm_count"]), walkrun=sc[WALK] + sc[RUN],
                         acc=float(m["clean_accuracy"]), f1=float(m["clean_macro_f1"]),
                         clean_fr=float(m["clean_fall_recall"]), wr_margin=marg, pgd20_recall=float("nan")))
    for run in vf_runs:
        m = kv(TE / f"{run}_pgd_safety_metrics_test_epsilon_0_03.csv")
        pgdpred = rows(TE / f"{run}_pgd_predictions_test_epsilon_0_03.csv")
        sc = src_counts(pgdpred, "attacked_predicted_label") if pgdpred else {k: 0 for k in NONFALL}
        marg = walkrun_margin(TE / f"{run}_pgd_probabilities_test_epsilon_0_03.csv")[0]
        p20 = kv(TE / f"{run}_pgd20_pgd_safety_metrics_test_epsilon_0_03.csv")
        comp.append(dict(group="variantF", label=run, recall=float(m["fall_recall"]),
                         fp=int(m["false_fall_alarm_count"]), walkrun=sc[WALK] + sc[RUN],
                         acc=float(m["clean_accuracy"]), f1=float(m["clean_macro_f1"]),
                         clean_fr=float(m["clean_fall_recall"]), wr_margin=marg,
                         pgd20_recall=float(p20["fall_recall"]) if p20 else float("nan")))

    with (VF / "variantF_seed42_comparison.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "label", "pgd_recall", "pgd_FP", "walk_run_to_fall", "clean_acc",
                    "clean_macro_f1", "clean_fall_recall", "wr_logit_margin", "pgd20_recall"])
        for c in comp:
            w.writerow([c["group"], c["label"], f"{c['recall']:.3f}", c["fp"], c["walkrun"],
                        f"{c['acc']:.3f}", f"{c['f1']:.3f}", f"{c['clean_fr']:.3f}",
                        f"{c['wr_margin']:.3f}", f"{c['pgd20_recall']:.3f}"])

    with (ANA / "wilson_intervals.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["label", "recall", "tp", "n_fall", "wilson_low", "wilson_high"])
        for c in comp:
            tp = round(c["recall"] * NFALL); lo, hi = wilson(tp, NFALL)
            w.writerow([c["label"], f"{c['recall']:.3f}", tp, NFALL, f"{lo:.3f}", f"{hi:.3f}"])

    with (ANA / "logit_margin_geometry.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["label", "median_logit_fall_minus_true_walkrun_FA", "vs_priorE"])
        for c in comp:
            delta = c["wr_margin"] - priorE_margin if not math.isnan(c["wr_margin"]) else float("nan")
            w.writerow([c["label"], f"{c['wr_margin']:.3f}", f"{delta:+.3f}"])

    # ---- criteria scorecard (Variant F candidates only) ----
    with (ANA / "criteria_scorecard.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["candidate", "c1_acc>=0.70", "c2_f1>=0.65", "c3_cleanfr>=0.90",
                    "c4_recall>=v2safety(0.356)", "c5_FP<=117_and<=110", "c6_walkrun<=80",
                    "c7_geometry_improved_vs_priorE", "c8_pgd20_not_zero", "c9_wilson_low>0",
                    "overall"])
        for c in comp:
            if c["group"] != "variantF":
                continue
            tp = round(c["recall"] * NFALL); lo, _ = wilson(tp, NFALL)
            c1 = c["acc"] >= 0.70; c2 = c["f1"] >= 0.65; c3 = c["clean_fr"] >= 0.90
            c4 = c["recall"] >= 0.356; c5 = (c["fp"] <= 117 and c["fp"] <= 110); c6 = c["walkrun"] <= 80
            c7 = (not math.isnan(c["wr_margin"])) and c["wr_margin"] < priorE_margin
            c8 = (not math.isnan(c["pgd20_recall"])) and c["pgd20_recall"] > 0
            c9 = lo > 0
            allc = all([c1, c2, c3, c4, c5, c6, c7, c8, c9])
            w.writerow([c["label"]] + [int(x) for x in (c1, c2, c3, c4, c5, c6, c7, c8, c9)] + [int(allc)])

    # ---- FN:FP cost ----
    with (ANA / "cost_curve.csv").open("w", newline="") as f:
        w = csv.writer(f); ratios = [1, 2, 5, 10, 20, 50]
        w.writerow(["label"] + [f"cost_{r}to1" for r in ratios])
        for c in comp:
            missed = round((1 - c["recall"]) * NFALL)
            w.writerow([c["label"]] + [r * missed + c["fp"] for r in ratios])

    # ---- pareto figure ----
    fig, ax = plt.subplots(figsize=(9, 6))
    for c in comp:
        col = "tab:blue" if c["group"] == "variantF" else "tab:gray"
        mk = "^" if c["group"] == "variantF" else "o"
        ax.scatter(c["fp"], c["recall"], color=col, marker=mk, s=80, zorder=4)
        ax.annotate(c["label"].replace("seed42_variantF_margin_", "F:").replace("_gm0p5_gf0p5", ""),
                    (c["fp"], c["recall"]), fontsize=6, xytext=(3, 3), textcoords="offset points")
    ax.axvline(117, color="red", ls=":", lw=0.8, alpha=0.6)
    ax.axhline(0.356, color="green", ls=":", lw=0.8, alpha=0.6)
    ax.set_xlabel("PGD@0.030 false-fall alarms"); ax.set_ylabel("PGD@0.030 fall recall")
    ax.set_title("Seed 42 Variant F (^) vs references (o); dotted = selection-v2 v2safety bar")
    ax.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(FIG / "fig_pareto_variantF.png", dpi=150); plt.close(fig)
    print(f"priorE walk/run logit margin reference = {priorE_margin:.3f}")
    print("[done] Variant F analysis complete.")


if __name__ == "__main__":
    main()
