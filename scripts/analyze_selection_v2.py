"""
Variant E selection-v2 analysis (seeds 42 + 43): comparison, diagnostics, figures.

Analysis only. For each seed, compares on test (n=500, ε=0.030):
    FGSM defense, Variant D safety, prior Variant E λ=1.0 safety, prior Variant E λ=1.0
    macro-F1, selection-v2 safety-eligible (v2safety), selection-v2 low-false-alarm (v2lowFA).

Outputs under results/safety_guided_defense/variantE_motion_hard_negative/selection_v2/:
    selection_v2_comparison.csv
    analysis/{selection_candidates,false_alarm_class_sources,binary_alert_metrics,probability_diagnosis}.csv
    figures/{fig_recall_vs_false_alarms,fig_clean_accuracy,fig_matched_recall_frontier}.png

Command:
    python scripts/analyze_selection_v2.py
"""

from __future__ import annotations

from pathlib import Path
import csv
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEEDS = (42, 43)


def helpers():
    sd = Path(__file__).resolve().parent
    if str(sd) not in sys.path:
        sys.path.insert(0, str(sd))
    import analyze_variantE as av
    import build_safety_guided_comparison as b
    return av, b


def main():
    av, b = helpers()
    CLASS, NONFALL, WALK, RUN, FALL = av.CLASS, av.NONFALL, av.WALK, av.RUN, av.FALL
    rows_of, source_counts, binmetrics = av.rows_of, av.source_counts, av.binmetrics

    exp = Path(__file__).resolve().parents[1]
    ca = exp / "results" / "converged_attacks"
    sg = exp / "results" / "safety_guided_defense"
    root = sg / "variantE_motion_hard_negative" / "selection_v2"
    figdir = root / "figures"; anadir = root / "analysis"
    figdir.mkdir(parents=True, exist_ok=True); anadir.mkdir(parents=True, exist_ok=True)

    def model_list(N):
        d_te = sg / f"seed{N}" / "test_eval"
        e_te = sg / "variantE_motion_hard_negative" / f"seed{N}" / "test_eval"
        v2_te = root / f"seed{N}" / "test_eval"
        # (label, ModelEval, predictions_dir, prob_dir, prob_prefix)
        return [
            ("FGSM_defense", b.ModelEval("Existing FGSM defense", "fgsmAT", ca, f"defended_fgsm_at_seed{N}"), ca, None, None),
            ("D_safety", b.ModelEval("Variant D safety", "safety", d_te, "variantD_bySafetyScore"), d_te, d_te, "variantD_bySafetyScore"),
            ("priorE_safety", b.ModelEval("prior Variant E safety", "safety", e_te, "E_lam1p0_bySafetyScore"), e_te, e_te, "E_lam1p0_bySafetyScore"),
            ("priorE_macroF1", b.ModelEval("prior Variant E macro-F1", "macroF1", e_te, "E_lam1p0_byValMacroF1"), e_te, e_te, "E_lam1p0_byValMacroF1"),
            ("v2safety", b.ModelEval("selection-v2 safety", "v2safety", v2_te, "v2safety"), v2_te, v2_te, "v2safety"),
            ("v2lowFA", b.ModelEval("selection-v2 lowFA", "v2lowFA", v2_te, "v2lowFA"), v2_te, v2_te, "v2lowFA"),
        ]

    # ---- comparison CSV ----
    comp_path = root / "selection_v2_comparison.csv"
    fields = ["seed", "model", "selection", "clean_accuracy", "clean_fall_recall",
              "pgd_0p030_fall_recall", "pgd_false_fall_alarms", "pgd_walk_to_fall", "pgd_run_to_fall",
              "pgd_collapse_epsilon", "fgsm_0p030_fall_recall", "fgsm_false_fall_alarms"]
    comp_rows = []
    with comp_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for N in SEEDS:
            for label, me, pdir, _, _ in model_list(N):
                if not me.available:
                    continue
                tr = me.table_row()
                rp = rows_of(Path(pdir) / f"{me.run_name}_pgd_predictions_test_epsilon_0_03.csv")
                w_, r_ = ("", "")
                if rp:
                    sc = source_counts(rp, "attacked_predicted_label"); w_, r_ = sc[WALK], sc[RUN]
                row = {"seed": N, "model": label, "selection": tr["selection_method"],
                       "clean_accuracy": tr["clean_accuracy"], "clean_fall_recall": tr["clean_fall_recall"],
                       "pgd_0p030_fall_recall": tr["pgd_0p030_fall_recall"], "pgd_false_fall_alarms": tr["pgd_false_fall_alarms"],
                       "pgd_walk_to_fall": w_, "pgd_run_to_fall": r_,
                       "pgd_collapse_epsilon": tr["pgd_collapse_epsilon"],
                       "fgsm_0p030_fall_recall": tr["fgsm_0p030_fall_recall"], "fgsm_false_fall_alarms": tr["fgsm_false_fall_alarms"]}
                w.writerow(row); comp_rows.append(row)
    print(f"[comparison] {comp_path}")

    # ---- class sources + binary + prob diagnosis ----
    src_path = anadir / "false_alarm_class_sources.csv"
    bin_path = anadir / "binary_alert_metrics.csv"
    diag_path = anadir / "probability_diagnosis.csv"
    with src_path.open("w", newline="", encoding="utf-8") as sf, bin_path.open("w", newline="", encoding="utf-8") as bf, \
         diag_path.open("w", newline="", encoding="utf-8") as df:
        sw = csv.writer(sf); sw.writerow(["seed", "checkpoint", "condition"] + [CLASS[k] for k in NONFALL] + ["total_false_fall"])
        bw = csv.writer(bf); bw.writerow(["seed", "checkpoint", "condition", "fall_recall", "false_fall_alarms",
                                          "fall_precision", "specificity", "fpr_nonfall", "binary_f1", "missed_fall_count"])
        dw = csv.writer(df); dw.writerow(["seed", "checkpoint", "group", "n", "fallprob_median", "maxconf_median"])
        for N in SEEDS:
            for label, me, pdir, probdir, prefix in model_list(N):
                if not me.available:
                    continue
                rf = rows_of(Path(pdir) / f"{me.run_name}_fgsm_predictions_test_epsilon_0_03.csv")
                rp = rows_of(Path(pdir) / f"{me.run_name}_pgd_predictions_test_epsilon_0_03.csv")
                if rf and rp:
                    for cond, rs, col in [("clean", rf, "clean_predicted_label"), ("fgsm003", rf, "attacked_predicted_label"), ("pgd003", rp, "attacked_predicted_label")]:
                        sc = source_counts(rs, col)
                        sw.writerow([N, label, cond] + [sc[k] for k in NONFALL] + [sum(sc.values())])
                        m = binmetrics(rs, col)
                        bw.writerow([N, label, cond, f"{m['recall']:.3f}", m['fp'], f"{m['precision']:.3f}",
                                     f"{m['specificity']:.3f}", f"{m['fpr']:.3f}", f"{m['f1']:.3f}", m['missed']])
                if probdir and prefix:
                    pp = rows_of(Path(probdir) / f"{prefix}_pgd_probabilities_test_epsilon_0_03.csv")
                    if pp:
                        T = np.array([int(r["true_label"]) for r in pp]); P = np.array([int(r["predicted_label"]) for r in pp])
                        FPB = np.array([float(r["fall_probability"]) for r in pp]); MC = np.array([float(r["max_confidence"]) for r in pp])
                        for g, mask in {"true_fall": (T == FALL), "walk_false_alarm": (T == WALK) & (P == FALL),
                                        "run_false_alarm": (T == RUN) & (P == FALL)}.items():
                            if mask.sum() == 0:
                                dw.writerow([N, label, g, 0, "nan", "nan"]); continue
                            dw.writerow([N, label, g, int(mask.sum()), f"{np.median(FPB[mask]):.4f}", f"{np.median(MC[mask]):.4f}"])
    print(f"[class-sources] {src_path}\n[binary] {bin_path}\n[prob-diagnosis] {diag_path}")

    # ---- combined selection_candidates.csv ----
    cand_out = anadir / "selection_candidates.csv"
    with cand_out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["seed", "selection", "selected_epoch", "val_clean_acc", "val_clean_macro_f1", "val_pgd_recall", "val_pgd_false_alarms", "safety_score"])
        for N in SEEDS:
            src = root / f"seed{N}" / "analysis" / f"seed{N}_variantE_selv2_lam1p0_selection_candidates.csv"
            for r in (rows_of(src) or []):
                w.writerow([N, r["selection"], r["selected_epoch"], r["val_clean_acc"], r["val_clean_macro_f1"], r["val_pgd_recall"], r["val_pgd_false_alarms"], r["safety_score"]])
    print(f"[candidates] {cand_out}")

    # ---- Figure 1: PGD recall vs FP operating points ----
    colors = {"FGSM_defense": "tab:gray", "D_safety": "tab:orange", "priorE_safety": "tab:green",
              "priorE_macroF1": "tab:olive", "v2safety": "tab:blue", "v2lowFA": "tab:purple"}
    markers = {42: "o", 43: "^"}
    fig, ax = plt.subplots(figsize=(9, 6))
    for r in comp_rows:
        try:
            rec = float(r["pgd_0p030_fall_recall"]); fp = int(r["pgd_false_fall_alarms"])
        except (ValueError, TypeError):
            continue
        ax.scatter([fp], [rec], color=colors.get(r["model"], "k"), marker=markers[r["seed"]], s=80, zorder=4)
        ax.annotate(f"{r['model']}·s{r['seed']}", (fp, rec), fontsize=6, xytext=(3, 3), textcoords="offset points")
    ax.set_xlabel("PGD@0.030 false-fall alarms (test)"); ax.set_ylabel("PGD@0.030 fall recall")
    ax.set_title("Selection-v2 vs prior Variant E / Variant D: recall vs false alarms (○ seed42, △ seed43)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(figdir / "fig_recall_vs_false_alarms.png", dpi=150); plt.close(fig)
    print(f"[figure] {figdir / 'fig_recall_vs_false_alarms.png'}")

    # ---- Figure 2: clean accuracy bars ----
    order = ["FGSM_defense", "D_safety", "priorE_safety", "v2safety", "v2lowFA"]
    fig, ax = plt.subplots(figsize=(11, 5))
    width = 0.38
    x = np.arange(len(order))
    for i, N in enumerate(SEEDS):
        accs = []
        for m in order:
            v = next((float(r["clean_accuracy"]) for r in comp_rows if r["seed"] == N and r["model"] == m), np.nan)
            accs.append(v)
        ax.bar(x + (i - 0.5) * width, accs, width, label=f"seed {N}")
    ax.axhline(0.70, color="red", linestyle=":", linewidth=1, alpha=0.6, label="v2 guard 0.70")
    ax.set_xticks(x); ax.set_xticklabels(order, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("clean accuracy"); ax.set_title("Clean accuracy by defense (selection-v2 vs prior)")
    ax.legend(fontsize=8); ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(figdir / "fig_clean_accuracy.png", dpi=150); plt.close(fig)
    print(f"[figure] {figdir / 'fig_clean_accuracy.png'}")

    # ---- Figure 3: matched-recall PGD frontier (prior E vs v2safety vs D), per seed ----
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for ax, N in zip(axes, SEEDS):
        d_te = sg / f"seed{N}" / "test_eval"; e_te = sg / "variantE_motion_hard_negative" / f"seed{N}" / "test_eval"; v2_te = root / f"seed{N}" / "test_eval"
        for path, lbl, c in [(d_te / "variantD_bySafetyScore_pgd_epsilon_sweep_test.csv", "Variant D safety", "tab:orange"),
                             (e_te / "E_lam1p0_bySafetyScore_pgd_epsilon_sweep_test.csv", "prior E safety", "tab:green"),
                             (v2_te / "v2safety_pgd_epsilon_sweep_test.csv", "v2 safety", "tab:blue")]:
            rs = rows_of(path)
            if not rs:
                continue
            rs = sorted(rs, key=lambda r: float(r["epsilon"]))
            ax.plot([int(r["false_fall_alarm_count"]) for r in rs], [float(r["fall_recall"]) for r in rs], "-o", color=c, ms=3, label=lbl)
        ax.set_title(f"seed {N}"); ax.set_xlabel("PGD false-fall alarms"); ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("PGD fall recall"); axes[0].legend(fontsize=8)
    fig.suptitle("Matched-recall PGD frontier: recall vs false alarms (across epsilon)")
    fig.tight_layout(); fig.savefig(figdir / "fig_matched_recall_frontier.png", dpi=150); plt.close(fig)
    print(f"[figure] {figdir / 'fig_matched_recall_frontier.png'}")
    print("[done] selection-v2 analysis complete.")


if __name__ == "__main__":
    main()
