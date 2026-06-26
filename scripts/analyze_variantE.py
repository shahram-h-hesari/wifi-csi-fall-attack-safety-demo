"""
Variant E (motion hard-negative) seed-42 analysis: comparison, diagnostics, figures.

Compares the Variant E pilots against the existing FGSM defense and the frozen
Variant D safety-guided / macro-F1 checkpoints (all seed 42, test n=500). Reuses
build_safety_guided_comparison.ModelEval for the metric/sweep readout; computes
false-alarm class sources, binary fall-alert metrics, and a fall-probability
diagnosis (true fall vs walk/run false alarms) from prediction / probability CSVs.

Analysis only -- reads existing CSVs; no training, no attacks.

Outputs (results/safety_guided_defense/variantE_motion_hard_negative/seed42/):
    variantE_seed42_comparison.csv
    analysis/false_alarm_class_sources.csv
    analysis/binary_alert_metrics.csv
    analysis/probability_diagnosis.csv
    figures/fig_recall_vs_false_alarms.png
    figures/fig_walk_run_false_alarm_reduction.png

Command:
    python scripts/analyze_variantE.py
"""

from __future__ import annotations

from pathlib import Path
import csv
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CLASS = {0: "lie down", 1: "fall", 2: "walk", 3: "pickup", 4: "run", 5: "sit down", 6: "stand up"}
NONFALL = [0, 2, 3, 4, 5, 6]
WALK, RUN, FALL = 2, 4, 1


def builder():
    sd = Path(__file__).resolve().parent
    if str(sd) not in sys.path:
        sys.path.insert(0, str(sd))
    import build_safety_guided_comparison as b
    return b


def rows_of(p):
    p = Path(p)
    if not p.exists():
        return None
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def source_counts(rs, col):
    c = {k: 0 for k in NONFALL}
    for r in rs:
        if int(r["true_label"]) != FALL and int(r[col]) == FALL:
            c[int(r["true_label"])] += 1
    return c


def binmetrics(rs, col):
    tp = fp = fn = tn = 0
    for r in rs:
        t = int(r["true_label"]) == FALL
        p = int(r[col]) == FALL
        if t and p: tp += 1
        elif (not t) and p: fp += 1
        elif t and (not p): fn += 1
        else: tn += 1
    rec = tp / (tp + fn) if tp + fn else 0.0
    prec = tp / (tp + fp) if tp + fp else 0.0
    spec = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return dict(recall=rec, fp=fp, precision=prec, specificity=spec,
                fpr=(fp / (fp + tn) if fp + tn else 0.0), f1=f1, missed=fn, fn=fn, tp=tp, tn=tn)


def main():
    b = builder()
    exp = Path(__file__).resolve().parents[1]
    ca = exp / "results" / "converged_attacks"
    d_te = exp / "results" / "safety_guided_defense" / "seed42" / "test_eval"
    e_base = exp / "results" / "safety_guided_defense" / "variantE_motion_hard_negative" / "seed42"
    e_te = e_base / "test_eval"
    d_prob = exp / "results" / "safety_guided_defense" / "decision_analysis" / "seed42_test_probabilities"
    figdir = e_base / "figures"
    anadir = e_base / "analysis"
    figdir.mkdir(parents=True, exist_ok=True)
    anadir.mkdir(parents=True, exist_ok=True)

    # Discover Variant E runs (by single-eps PGD metrics).
    e_runs = sorted(p.name.replace("_pgd_safety_metrics_test_epsilon_0_03.csv", "")
                    for p in e_te.glob("*_pgd_safety_metrics_test_epsilon_0_03.csv"))

    # (label, ModelEval, predictions_dir, prob_dir, prob_prefix)
    models = []
    models.append(("FGSM_defense",
                   b.ModelEval("Existing FGSM defense", "0.5cleanF1+0.5fgsmF1", ca, "defended_fgsm_at_seed42"),
                   ca, None, None))
    models.append(("D_safety",
                   b.ModelEval("Variant D safety-guided", "safety_score", d_te, "variantD_bySafetyScore"),
                   d_te, d_prob, "seed42_variantD_bySafetyScore"))
    models.append(("D_macroF1",
                   b.ModelEval("Variant D macro-F1", "val_macro_f1", d_te, "variantD_byValMacroF1"),
                   d_te, d_prob, "seed42_variantD_byValMacroF1"))
    for run in e_runs:
        sel = "safety_score" if "bySafetyScore" in run else ("val_macro_f1" if "byValMacroF1" in run else "?")
        models.append((run, b.ModelEval(f"Variant E ({run})", sel, e_te, run), e_te, e_te, run))

    avail = [m for m in models if m[1].available]

    # ---- comparison CSV (+ walk/run PGD false-alarm columns) ----
    comp_path = e_base / "variantE_seed42_comparison.csv"
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
                sc = source_counts(pgd_pred, "attacked_predicted_label")
                tot = sum(sc.values())
                row["pgd_walk_to_fall"] = sc[WALK]
                row["pgd_run_to_fall"] = sc[RUN]
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

    # ---- probability diagnosis (test PGD): fall-prob by group ----
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
            T = np.array([int(r["true_label"]) for r in pp])
            P = np.array([int(r["predicted_label"]) for r in pp])
            FP = np.array([float(r["fall_probability"]) for r in pp])
            MC = np.array([float(r["max_confidence"]) for r in pp])
            groups = {"true_fall": (T == FALL),
                      "walk_false_alarm": (T == WALK) & (P == FALL),
                      "run_false_alarm": (T == RUN) & (P == FALL),
                      "other_false_alarm": (T != FALL) & (T != WALK) & (T != RUN) & (P == FALL)}
            for g, mask in groups.items():
                if mask.sum() == 0:
                    w.writerow([label, g, 0, "nan", "nan", "nan", "nan"]); continue
                w.writerow([label, g, int(mask.sum()), f"{np.median(FP[mask]):.4f}",
                            f"{np.percentile(FP[mask],25):.4f}", f"{np.percentile(FP[mask],75):.4f}",
                            f"{np.median(MC[mask]):.4f}"])
    print(f"[prob-diagnosis] {diag_path}")

    # ---- Figure 1: PGD recall vs false alarms (operating points) ----
    fig, ax = plt.subplots(figsize=(9, 6))
    for label, me, _, _, _ in avail:
        if not me.pgd_single:
            continue
        rec = float(me.pgd_fall_recall); fp = int(me.pgd_false_alarms)
        if label == "FGSM_defense":
            c, mk = "tab:gray", "s"
        elif label.startswith("D_"):
            c, mk = "tab:orange", "D"
        else:
            c, mk = "tab:green", "^"
        ax.scatter([fp], [rec], color=c, marker=mk, s=90, zorder=4)
        ax.annotate(label, (fp, rec), fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax.set_xlabel("PGD@0.030 false-fall alarms (test, n=500)")
    ax.set_ylabel("PGD@0.030 fall recall")
    ax.set_title("Seed 42 - Variant E vs Variant D / FGSM defense: recall vs false alarms")
    ax.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(figdir / "fig_recall_vs_false_alarms.png", dpi=150); plt.close(fig)
    print(f"[figure] {figdir / 'fig_recall_vs_false_alarms.png'}")

    # ---- Figure 2: walk/run -> fall false alarms (PGD) bar chart ----
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
    ax.set_title("Seed 42 - walk/run -> fall false alarms by defense")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=7)
    ax.legend(); ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(figdir / "fig_walk_run_false_alarm_reduction.png", dpi=150); plt.close(fig)
    print(f"[figure] {figdir / 'fig_walk_run_false_alarm_reduction.png'}")
    print("[done] Variant E analysis complete.")


if __name__ == "__main__":
    main()
