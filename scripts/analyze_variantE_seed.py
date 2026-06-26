"""
Seed-parametric Variant E analysis (comparison + diagnostics + figures).

`analyze_variantE.py` is hard-coded to seed 42; this sibling applies the SAME
analysis to any seed without modifying it (it imports analyze_variantE's tested
helpers). For a given seed N it compares, on the test split:
    existing FGSM defense (seed N), Variant D safety / macro-F1 (seed N),
    and the Variant E λ=1.0 safety / macro-F1 checkpoints (seed N).

Probability/logit CSVs are read from each checkpoint's own test_eval directory
(prefix = run name), which is where run_converged_attacks /
export_probability_predictions write them for seeds other than 42.

Analysis only -- reads existing CSVs; no training, no attacks.

Outputs (results/safety_guided_defense/variantE_motion_hard_negative/seed{N}/):
    variantE_seed{N}_comparison.csv
    analysis/{false_alarm_class_sources,binary_alert_metrics,probability_diagnosis}.csv
    figures/{fig_recall_vs_false_alarms,fig_walk_run_false_alarm_reduction}.png

Command:
    python scripts/analyze_variantE_seed.py --seed 43
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def helpers():
    sd = Path(__file__).resolve().parent
    if str(sd) not in sys.path:
        sys.path.insert(0, str(sd))
    import analyze_variantE as av
    import build_safety_guided_comparison as b
    return av, b


def main():
    ap = argparse.ArgumentParser(description="Seed-parametric Variant E analysis.")
    ap.add_argument("--seed", type=int, required=True)
    args = ap.parse_args()
    N = args.seed
    av, b = helpers()
    CLASS, NONFALL, WALK, RUN, FALL = av.CLASS, av.NONFALL, av.WALK, av.RUN, av.FALL
    rows_of, source_counts, binmetrics = av.rows_of, av.source_counts, av.binmetrics

    exp = Path(__file__).resolve().parents[1]
    ca = exp / "results" / "converged_attacks"
    d_te = exp / "results" / "safety_guided_defense" / f"seed{N}" / "test_eval"
    e_base = exp / "results" / "safety_guided_defense" / "variantE_motion_hard_negative" / f"seed{N}"
    e_te = e_base / "test_eval"
    figdir = e_base / "figures"
    anadir = e_base / "analysis"
    figdir.mkdir(parents=True, exist_ok=True)
    anadir.mkdir(parents=True, exist_ok=True)

    e_runs = sorted(p.name.replace("_pgd_safety_metrics_test_epsilon_0_03.csv", "")
                    for p in e_te.glob("*_pgd_safety_metrics_test_epsilon_0_03.csv"))

    # (label, ModelEval, predictions_dir, prob_dir, prob_prefix)
    models = [
        ("FGSM_defense", b.ModelEval("Existing FGSM defense", "0.5cleanF1+0.5fgsmF1", ca, f"defended_fgsm_at_seed{N}"), ca, None, None),
        ("D_safety", b.ModelEval("Variant D safety-guided", "safety_score", d_te, "variantD_bySafetyScore"), d_te, d_te, "variantD_bySafetyScore"),
        ("D_macroF1", b.ModelEval("Variant D macro-F1", "val_macro_f1", d_te, "variantD_byValMacroF1"), d_te, d_te, "variantD_byValMacroF1"),
    ]
    for run in e_runs:
        sel = "safety_score" if "bySafetyScore" in run else ("val_macro_f1" if "byValMacroF1" in run else "?")
        models.append((run, b.ModelEval(f"Variant E ({run})", sel, e_te, run), e_te, e_te, run))
    avail = [m for m in models if m[1].available]

    # ---- comparison CSV ----
    comp_path = e_base / f"variantE_seed{N}_comparison.csv"
    fields = ["model_defense", "selection_method", "clean_accuracy", "clean_fall_recall",
              "fgsm_0p030_fall_recall", "fgsm_false_fall_alarms", "pgd_0p030_fall_recall",
              "pgd_false_fall_alarms", "pgd_walk_to_fall", "pgd_run_to_fall", "pgd_walk_run_share",
              "fgsm_collapse_epsilon", "pgd_collapse_epsilon", "notes"]
    with comp_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for label, me, pdir, _, _ in avail:
            row = me.table_row()
            pgd_pred = rows_of(Path(pdir) / f"{me.run_name}_pgd_predictions_test_epsilon_0_03.csv")
            if pgd_pred:
                sc = source_counts(pgd_pred, "attacked_predicted_label"); tot = sum(sc.values())
                row["pgd_walk_to_fall"] = sc[WALK]; row["pgd_run_to_fall"] = sc[RUN]
                row["pgd_walk_run_share"] = f"{(sc[WALK]+sc[RUN])/tot:.3f}" if tot else "0"
            else:
                row["pgd_walk_to_fall"] = row["pgd_run_to_fall"] = row["pgd_walk_run_share"] = ""
            w.writerow(row)
    print(f"[comparison] {comp_path}")

    # ---- class sources + binary metrics ----
    src_path = anadir / "false_alarm_class_sources.csv"
    bin_path = anadir / "binary_alert_metrics.csv"
    with src_path.open("w", newline="", encoding="utf-8") as sf, bin_path.open("w", newline="", encoding="utf-8") as bf:
        sw = csv.writer(sf); sw.writerow(["checkpoint", "condition"] + [CLASS[k] for k in NONFALL] + ["total_false_fall"])
        bw = csv.writer(bf); bw.writerow(["checkpoint", "condition", "fall_recall", "false_fall_alarms",
                                          "fall_precision", "specificity", "fpr_nonfall", "binary_f1",
                                          "missed_fall_count", "tp", "fp", "fn", "tn"])
        for label, me, pdir, _, _ in avail:
            rf = rows_of(Path(pdir) / f"{me.run_name}_fgsm_predictions_test_epsilon_0_03.csv")
            rp = rows_of(Path(pdir) / f"{me.run_name}_pgd_predictions_test_epsilon_0_03.csv")
            if rf is None or rp is None:
                continue
            for cond, rs, col in [("clean", rf, "clean_predicted_label"),
                                  ("fgsm003", rf, "attacked_predicted_label"),
                                  ("pgd003", rp, "attacked_predicted_label")]:
                sc = source_counts(rs, col)
                sw.writerow([label, cond] + [sc[k] for k in NONFALL] + [sum(sc.values())])
                m = binmetrics(rs, col)
                bw.writerow([label, cond, f"{m['recall']:.3f}", m['fp'], f"{m['precision']:.3f}",
                             f"{m['specificity']:.3f}", f"{m['fpr']:.3f}", f"{m['f1']:.3f}",
                             m['missed'], m['tp'], m['fp'], m['fn'], m['tn']])
    print(f"[class-sources] {src_path}")
    print(f"[binary] {bin_path}")

    # ---- probability diagnosis (test PGD) ----
    diag_path = anadir / "probability_diagnosis.csv"
    with diag_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["checkpoint", "group", "n", "fallprob_median", "fallprob_p25", "fallprob_p75", "maxconf_median"])
        for label, me, _, probdir, prefix in avail:
            if probdir is None or prefix is None:
                continue
            pp = rows_of(Path(probdir) / f"{prefix}_pgd_probabilities_test_epsilon_0_03.csv")
            if pp is None:
                continue
            T = np.array([int(r["true_label"]) for r in pp]); P = np.array([int(r["predicted_label"]) for r in pp])
            FPB = np.array([float(r["fall_probability"]) for r in pp]); MC = np.array([float(r["max_confidence"]) for r in pp])
            groups = {"true_fall": (T == FALL), "walk_false_alarm": (T == WALK) & (P == FALL),
                      "run_false_alarm": (T == RUN) & (P == FALL),
                      "other_false_alarm": (T != FALL) & (T != WALK) & (T != RUN) & (P == FALL)}
            for g, mask in groups.items():
                if mask.sum() == 0:
                    w.writerow([label, g, 0, "nan", "nan", "nan", "nan"]); continue
                w.writerow([label, g, int(mask.sum()), f"{np.median(FPB[mask]):.4f}",
                            f"{np.percentile(FPB[mask],25):.4f}", f"{np.percentile(FPB[mask],75):.4f}",
                            f"{np.median(MC[mask]):.4f}"])
    print(f"[prob-diagnosis] {diag_path}")

    # ---- Figure 1: PGD recall vs false alarms ----
    fig, ax = plt.subplots(figsize=(9, 6))
    for label, me, _, _, _ in avail:
        if not me.pgd_single:
            continue
        rec = float(me.pgd_fall_recall); fp = int(me.pgd_false_alarms)
        c, mk = ("tab:gray", "s") if label == "FGSM_defense" else (("tab:orange", "D") if label.startswith("D_") else ("tab:green", "^"))
        ax.scatter([fp], [rec], color=c, marker=mk, s=90, zorder=4)
        ax.annotate(label, (fp, rec), fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax.set_xlabel("PGD@0.030 false-fall alarms (test, n=500)"); ax.set_ylabel("PGD@0.030 fall recall")
    ax.set_title(f"Seed {N} - Variant E vs Variant D / FGSM defense: recall vs false alarms")
    ax.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(figdir / "fig_recall_vs_false_alarms.png", dpi=150); plt.close(fig)
    print(f"[figure] {figdir / 'fig_recall_vs_false_alarms.png'}")

    # ---- Figure 2: walk/run -> fall false alarms (PGD) ----
    labels, walk_c, run_c = [], [], []
    for label, me, pdir, _, _ in avail:
        rp = rows_of(Path(pdir) / f"{me.run_name}_pgd_predictions_test_epsilon_0_03.csv")
        if rp is None:
            continue
        sc = source_counts(rp, "attacked_predicted_label")
        labels.append(label); walk_c.append(sc[WALK]); run_c.append(sc[RUN])
    x = np.arange(len(labels)); width = 0.4
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.bar(x - width/2, walk_c, width, label="walk->fall", color="tab:red")
    ax.bar(x + width/2, run_c, width, label="run->fall", color="tab:purple")
    ax.set_ylabel("false-fall alarms (count, PGD@0.030)")
    ax.set_title(f"Seed {N} - walk/run -> fall false alarms by defense")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=7)
    ax.legend(); ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(figdir / "fig_walk_run_false_alarm_reduction.png", dpi=150); plt.close(fig)
    print(f"[figure] {figdir / 'fig_walk_run_false_alarm_reduction.png'}")
    print("[done] Variant E seed analysis complete.")


if __name__ == "__main__":
    main()
