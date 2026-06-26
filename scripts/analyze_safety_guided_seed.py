"""
Per-seed safety-guided defense analysis (comparison table + figures + diagnostics).

Generalizes scripts/build_safety_guided_comparison.py (which is hard-coded to
seed 42) to an arbitrary seed, WITHOUT modifying it -- it imports that module's
ModelEval class, figure functions, and helpers and reuses them. Produces, for a
given seed N:

    results/safety_guided_defense/seed{N}/seed{N}_defense_comparison.csv
    results/safety_guided_defense/seed{N}/analysis/false_alarm_class_sources.csv
    results/safety_guided_defense/seed{N}/analysis/binary_alert_metrics.csv
    results/safety_guided_defense/seed{N}/figures/fig1_fall_recall_vs_epsilon.png
    results/safety_guided_defense/seed{N}/figures/fig2_false_fall_alarms_vs_epsilon.png
    results/safety_guided_defense/seed{N}/figures/fig3_clean_fgsm_pgd_bar_summary.png

Comparison rows: clean LeNet baseline, existing FGSM defense, Variant D
safety-guided, Variant D macro-F1 (all for the same seed). The class-source and
binary metrics are computed from the per-window prediction CSVs with the SAME
logic used for the seed-42 memo, so seeds are directly comparable.

Analysis only: reads existing prediction/metric CSVs; does not train or attack.

Command:
    python scripts/analyze_safety_guided_seed.py --seed 43
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

CLASS = {0: "lie down", 1: "fall", 2: "walk", 3: "pickup", 4: "run", 5: "sit down", 6: "stand up"}
NONFALL = [0, 2, 3, 4, 5, 6]
FALL = 1


def import_builder():
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import build_safety_guided_comparison as b
    return b


def rows_of(path: Path):
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def source_counts(rs, pred_col):
    c = {k: 0 for k in NONFALL}
    for r in rs:
        t = int(r["true_label"])
        if t != FALL and int(r[pred_col]) == FALL:
            c[t] += 1
    return c


def binmetrics(rs, pred_col):
    tp = fp = fn = tn = 0
    for r in rs:
        t = 1 if int(r["true_label"]) == FALL else 0
        p = 1 if int(r[pred_col]) == FALL else 0
        if t and p:
            tp += 1
        elif (not t) and p:
            fp += 1
        elif t and (not p):
            fn += 1
        else:
            tn += 1
    rec = tp / (tp + fn) if tp + fn else 0.0
    prec = tp / (tp + fp) if tp + fp else 0.0
    spec = tn / (tn + fp) if tn + fp else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return dict(tp=tp, fp=fp, fn=fn, tn=tn, recall=rec, precision=prec,
                specificity=spec, fpr=fpr, f1=f1, missed=fn)


def _sweep_xy(rows, key):
    xs = [float(r["epsilon"]) for r in rows]
    ys = [float(r[key]) for r in rows]
    return xs, ys


def _fig_recall_vs_epsilon(seed, baseline, fgsm_def, best, out_path, collapse_thr):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    series = [("Clean baseline", baseline, "tab:gray", "o"),
              ("FGSM defense", fgsm_def, "tab:orange", "s"),
              ("Variant D safety-guided", best, "tab:green", "^")]
    for ax, (attr, title) in zip(axes, [("fgsm_sweep", "FGSM attack"), ("pgd_sweep", "PGD attack")]):
        for label, m, color, marker in series:
            rows = getattr(m, attr)
            if not rows:
                continue
            xs, ys = _sweep_xy(rows, "fall_recall")
            ax.plot(xs, ys, marker=marker, color=color, label=label, linewidth=1.8, markersize=4)
        ax.axhline(collapse_thr, color="red", linestyle=":", linewidth=1, alpha=0.6)
        ax.axvline(0.030, color="black", linestyle="--", linewidth=0.8, alpha=0.5)
        ax.set_title(title); ax.set_xlabel("epsilon (L-inf)"); ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("fall recall (test, n=500)")
    axes[0].legend(loc="upper right", fontsize=8)
    fig.suptitle(f"Seed {seed} - fall recall vs attack epsilon (digital-domain white-box)", fontsize=12)
    fig.tight_layout(); fig.savefig(out_path, dpi=150); plt.close(fig)


def _fig_false_alarms_vs_epsilon(seed, baseline, fgsm_def, best, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    series = [("Clean baseline", baseline, "tab:gray", "o"),
              ("FGSM defense", fgsm_def, "tab:orange", "s"),
              ("Variant D safety-guided", best, "tab:green", "^")]
    for ax, (attr, title) in zip(axes, [("fgsm_sweep", "FGSM attack"), ("pgd_sweep", "PGD attack")]):
        for label, m, color, marker in series:
            rows = getattr(m, attr)
            if not rows:
                continue
            xs, ys = _sweep_xy(rows, "false_fall_alarm_count")
            ax.plot(xs, ys, marker=marker, color=color, label=label, linewidth=1.8, markersize=4)
        ax.axvline(0.030, color="black", linestyle="--", linewidth=0.8, alpha=0.5)
        ax.set_title(title); ax.set_xlabel("epsilon (L-inf)"); ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("false-fall alarms (count, non-fall->fall)")
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle(f"Seed {seed} - false-fall alarms vs attack epsilon", fontsize=12)
    fig.tight_layout(); fig.savefig(out_path, dpi=150); plt.close(fig)


def _fig_bar_summary(seed, baseline, fgsm_def, best, out_path):
    models = [("Clean\nbaseline", baseline), ("FGSM\ndefense", fgsm_def),
              ("Variant D\nsafety-guided", best)]
    labels = [m[0] for m in models]
    x = np.arange(len(models)); width = 0.25
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    clean_fr = [float(m.clean_fall_recall) for _, m in models]
    fgsm_fr = [float(m.fgsm_fall_recall) for _, m in models]
    pgd_fr = [float(m.pgd_fall_recall) for _, m in models]
    axes[0].bar(x - width, clean_fr, width, label="clean", color="tab:gray")
    axes[0].bar(x, fgsm_fr, width, label="FGSM@0.030", color="tab:orange")
    axes[0].bar(x + width, pgd_fr, width, label="PGD@0.030", color="tab:green")
    axes[0].set_ylabel("fall recall"); axes[0].set_title("Fall recall (higher = safer)")
    axes[0].set_xticks(x); axes[0].set_xticklabels(labels, fontsize=9)
    axes[0].set_ylim(0, 1.05); axes[0].legend(fontsize=8); axes[0].grid(True, axis="y", alpha=0.3)
    fgsm_fa = [float(m.fgsm_false_alarms) for _, m in models]
    pgd_fa = [float(m.pgd_false_alarms) for _, m in models]
    axes[1].bar(x - width / 2, fgsm_fa, width, label="FGSM@0.030", color="tab:orange")
    axes[1].bar(x + width / 2, pgd_fa, width, label="PGD@0.030", color="tab:green")
    axes[1].set_ylabel("false-fall alarms (count)"); axes[1].set_title("False-fall alarms (lower = better)")
    axes[1].set_xticks(x); axes[1].set_xticklabels(labels, fontsize=9)
    axes[1].legend(fontsize=8); axes[1].grid(True, axis="y", alpha=0.3)
    fig.suptitle(f"Seed {seed} - safety-critical trade-off summary (test, n=500)", fontsize=12)
    fig.tight_layout(); fig.savefig(out_path, dpi=150); plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="Per-seed safety-guided defense analysis.")
    ap.add_argument("--seed", type=int, required=True)
    args = ap.parse_args()
    N = args.seed

    b = import_builder()
    exp = Path(__file__).resolve().parents[1]
    ca = exp / "results" / "converged_attacks"
    te = exp / "results" / "safety_guided_defense" / f"seed{N}" / "test_eval"
    seed_dir = exp / "results" / "safety_guided_defense" / f"seed{N}"
    fig_dir = seed_dir / "figures"
    ana_dir = seed_dir / "analysis"
    fig_dir.mkdir(parents=True, exist_ok=True)
    ana_dir.mkdir(parents=True, exist_ok=True)

    baseline = b.ModelEval("Clean LeNet baseline", "val_macro_f1", ca, f"converged_seed{N}",
                           notes="undefended reference")
    fgsm_def = b.ModelEval("Existing FGSM defense", "0.5*cleanF1+0.5*fgsmF1", ca,
                           f"defended_fgsm_at_seed{N}", notes="prior FGSM adversarial training")
    d_safety = b.ModelEval("Variant D safety-guided", "safety_score", te, "variantD_bySafetyScore",
                           notes="frozen Variant D, safety-guided selection")
    d_f1 = b.ModelEval("Variant D macro-F1", "val_macro_f1", te, "variantD_byValMacroF1",
                       notes="frozen Variant D, standard-selection comparison")
    models = [m for m in (baseline, fgsm_def, d_safety, d_f1) if m.available]

    # 1) comparison table (reuse ModelEval.table_row)
    out_table = seed_dir / f"seed{N}_defense_comparison.csv"
    b.build_table(models, out_table)

    # 2) figures (seed-aware titles; reuse builder's ModelEval sweep data, not its
    #    hard-coded "Seed 42" titles). Highlight Variant D safety-guided.
    if d_safety.available:
        _fig_recall_vs_epsilon(N, baseline, fgsm_def, d_safety,
                               fig_dir / "fig1_fall_recall_vs_epsilon.png", b.COLLAPSE_THRESHOLD)
        _fig_false_alarms_vs_epsilon(N, baseline, fgsm_def, d_safety,
                                     fig_dir / "fig2_false_fall_alarms_vs_epsilon.png")
        _fig_bar_summary(N, baseline, fgsm_def, d_safety,
                         fig_dir / "fig3_clean_fgsm_pgd_bar_summary.png")

    # 3) class-source + binary diagnostics (from prediction CSVs)
    checkpoints = [
        ("FGSM_defense", ca / f"defended_fgsm_at_seed{N}_fgsm_predictions_test_epsilon_0_03.csv",
         ca / f"defended_fgsm_at_seed{N}_pgd_predictions_test_epsilon_0_03.csv"),
        ("D_safety", te / "variantD_bySafetyScore_fgsm_predictions_test_epsilon_0_03.csv",
         te / "variantD_bySafetyScore_pgd_predictions_test_epsilon_0_03.csv"),
        ("D_macroF1", te / "variantD_byValMacroF1_fgsm_predictions_test_epsilon_0_03.csv",
         te / "variantD_byValMacroF1_pgd_predictions_test_epsilon_0_03.csv"),
    ]
    src_path = ana_dir / "false_alarm_class_sources.csv"
    bin_path = ana_dir / "binary_alert_metrics.csv"
    missing = []
    with src_path.open("w", newline="", encoding="utf-8") as sf, \
         bin_path.open("w", newline="", encoding="utf-8") as bf:
        sw = csv.writer(sf)
        sw.writerow(["checkpoint", "condition"] + [CLASS[k] for k in NONFALL] + ["total_false_fall"])
        bw = csv.writer(bf)
        bw.writerow(["checkpoint", "condition", "fall_recall", "false_fall_alarms", "fall_precision",
                     "specificity", "fpr_nonfall", "binary_f1", "missed_fall_count", "tp", "fp", "fn", "tn"])
        for label, ff, pf in checkpoints:
            rf = rows_of(ff)
            rp = rows_of(pf)
            if rf is None or rp is None:
                missing.append(label)
                continue
            for cond, rs, col in [("clean", rf, "clean_predicted_label"),
                                  ("fgsm003", rf, "attacked_predicted_label"),
                                  ("pgd003", rp, "attacked_predicted_label")]:
                c = source_counts(rs, col)
                sw.writerow([label, cond] + [c[k] for k in NONFALL] + [sum(c.values())])
                m = binmetrics(rs, col)
                bw.writerow([label, cond, f"{m['recall']:.3f}", m['fp'], f"{m['precision']:.3f}",
                             f"{m['specificity']:.3f}", f"{m['fpr']:.3f}", f"{m['f1']:.3f}",
                             m['missed'], m['tp'], m['fp'], m['fn'], m['tn']])

    print(f"[table]   {out_table}")
    print(f"[sources] {src_path}")
    print(f"[binary]  {bin_path}")
    print(f"[figures] {fig_dir}")
    if missing:
        print(f"[warn] prediction files missing for: {missing}")
    print("[done] seed analysis complete.")


if __name__ == "__main__":
    main()
