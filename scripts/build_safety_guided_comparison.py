"""
Stage 3b analysis: comparison table + diagnostic figures (seed 42 only).

Consumes the held-out TEST-set attack evaluations produced by
run_converged_attacks.py for:
    * the clean LeNet baseline          (results/converged_attacks/converged_seed42_*)
    * the existing FGSM defense         (results/converged_attacks/defended_fgsm_at_seed42_*)
    * the new safety-guided variants    (results/safety_guided_defense/seed42/test_eval/*)

and produces:
    Step 6 -> a comparison table CSV
    Step 7 -> three seed-42 diagnostic figures:
        1. fall recall vs epsilon (FGSM + PGD panels)
        2. false-fall alarms vs epsilon (FGSM + PGD panels)
        3. clean/FGSM/PGD grouped bar chart (fall recall + false alarms)

"Collapse epsilon" is defined as the first sweep epsilon at which fall recall
falls below 0.50 (same semantics as run_converged_attacks' threshold report);
reported as NaN/"none" if recall never drops below 0.50 within the swept range.

Scope: window-level digital-domain white-box robustness on processed CSI
tensors. Not clinical, not over-the-air, not certified. Seed 42 only.

Commands:
    python scripts/build_safety_guided_comparison.py
    python scripts/build_safety_guided_comparison.py --best-variant variantB_bySafetyScore
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


COLLAPSE_THRESHOLD = 0.50


def read_kv(path: Path) -> dict:
    """Read a metric,value CSV into a dict (values kept as strings)."""
    out = {}
    if not path.exists():
        return out
    with path.open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["metric"]] = row["value"]
    return out


def read_sweep(path: Path) -> list:
    """Read a sweep CSV into a list of dicts sorted by ascending epsilon."""
    rows = []
    if not path.exists():
        return rows
    with path.open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    rows.sort(key=lambda r: float(r["epsilon"]))
    return rows


def collapse_epsilon(sweep_rows: list) -> float:
    """First epsilon where fall_recall < COLLAPSE_THRESHOLD, else NaN."""
    for r in sweep_rows:
        if float(r["fall_recall"]) < COLLAPSE_THRESHOLD:
            return float(r["epsilon"])
    return float("nan")


def fmt(x, nd=3):
    if x is None:
        return ""
    if isinstance(x, float) and np.isnan(x):
        return "none"
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return str(x)


class ModelEval:
    """One model's test-set attack evaluation, loaded from CSV artifacts."""

    def __init__(self, name, selection, attacks_dir, run_name, notes=""):
        self.name = name
        self.selection = selection
        self.notes = notes
        self.run_name = run_name
        d = attacks_dir
        self.fgsm_single = read_kv(d / f"{run_name}_fgsm_safety_metrics_test_epsilon_0_03.csv")
        self.pgd_single = read_kv(d / f"{run_name}_pgd_safety_metrics_test_epsilon_0_03.csv")
        self.fgsm_sweep = read_sweep(d / f"{run_name}_fgsm_epsilon_sweep_test.csv")
        self.pgd_sweep = read_sweep(d / f"{run_name}_pgd_epsilon_sweep_test.csv")

    @property
    def available(self):
        return bool(self.pgd_single)

    @property
    def clean_accuracy(self):
        return self.pgd_single.get("clean_accuracy")

    @property
    def clean_fall_recall(self):
        return self.pgd_single.get("clean_fall_recall")

    @property
    def fgsm_fall_recall(self):
        return self.fgsm_single.get("fall_recall")

    @property
    def fgsm_false_alarms(self):
        return self.fgsm_single.get("false_fall_alarm_count")

    @property
    def pgd_fall_recall(self):
        return self.pgd_single.get("fall_recall")

    @property
    def pgd_false_alarms(self):
        return self.pgd_single.get("false_fall_alarm_count")

    def table_row(self):
        return {
            "model_defense": self.name,
            "selection_method": self.selection,
            "clean_accuracy": fmt(self.clean_accuracy),
            "clean_fall_recall": fmt(self.clean_fall_recall),
            "fgsm_0p030_fall_recall": fmt(self.fgsm_fall_recall),
            "fgsm_false_fall_alarms": self.fgsm_false_alarms or "",
            "pgd_0p030_fall_recall": fmt(self.pgd_fall_recall),
            "pgd_false_fall_alarms": self.pgd_false_alarms or "",
            "fgsm_collapse_epsilon": fmt(collapse_epsilon(self.fgsm_sweep)),
            "pgd_collapse_epsilon": fmt(collapse_epsilon(self.pgd_sweep)),
            "notes": self.notes,
        }


def discover_variant_evals(test_eval_dir: Path) -> list:
    """Find safety-guided variant eval runs from their single-eps PGD CSVs."""
    runs = []
    for p in sorted(test_eval_dir.glob("*_pgd_safety_metrics_test_epsilon_0_03.csv")):
        run_name = p.name.replace("_pgd_safety_metrics_test_epsilon_0_03.csv", "")
        runs.append(run_name)
    return runs


def pretty_variant_name(run_name: str) -> tuple:
    """Map a safety-guided run_name to (display_name, selection_label)."""
    selection = "safety_score" if "bySafetyScore" in run_name else (
        "val_macro_f1" if "byValMacroF1" in run_name else "unknown")
    base = run_name.split("_bySafetyScore")[0].split("_byValMacroF1")[0]
    return f"safety_guided_{base}", selection


def build_table(models: list, out_path: Path):
    fields = ["model_defense", "selection_method", "clean_accuracy", "clean_fall_recall",
              "fgsm_0p030_fall_recall", "fgsm_false_fall_alarms", "pgd_0p030_fall_recall",
              "pgd_false_fall_alarms", "fgsm_collapse_epsilon", "pgd_collapse_epsilon", "notes"]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for m in models:
            writer.writerow(m.table_row())
    print(f"[table] wrote {out_path}")


def sweep_xy(sweep_rows, key):
    xs = [float(r["epsilon"]) for r in sweep_rows]
    ys = [float(r[key]) for r in sweep_rows]
    return xs, ys


def figure_recall_vs_epsilon(baseline, fgsm_def, best, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    series = [("Clean baseline", baseline, "tab:gray", "o"),
              ("FGSM defense", fgsm_def, "tab:orange", "s"),
              (f"Safety-guided ({best.selection})", best, "tab:green", "^")]
    for ax, (sweeps, title) in zip(axes, [("fgsm_sweep", "FGSM attack"), ("pgd_sweep", "PGD attack")]):
        for label, m, color, marker in series:
            rows = getattr(m, sweeps)
            if not rows:
                continue
            xs, ys = sweep_xy(rows, "fall_recall")
            ax.plot(xs, ys, marker=marker, color=color, label=label, linewidth=1.8, markersize=4)
        ax.axhline(COLLAPSE_THRESHOLD, color="red", linestyle=":", linewidth=1, alpha=0.6)
        ax.axvline(0.030, color="black", linestyle="--", linewidth=0.8, alpha=0.5)
        ax.set_title(title)
        ax.set_xlabel("epsilon (L-inf)")
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("fall recall (test, n=500)")
    axes[0].legend(loc="upper right", fontsize=8)
    fig.suptitle("Seed 42 - fall recall vs attack epsilon (digital-domain white-box)", fontsize=12)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"[figure] wrote {out_path}")


def figure_false_alarms_vs_epsilon(baseline, fgsm_def, best, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    series = [("Clean baseline", baseline, "tab:gray", "o"),
              ("FGSM defense", fgsm_def, "tab:orange", "s"),
              (f"Safety-guided ({best.selection})", best, "tab:green", "^")]
    for ax, (sweeps, title) in zip(axes, [("fgsm_sweep", "FGSM attack"), ("pgd_sweep", "PGD attack")]):
        for label, m, color, marker in series:
            rows = getattr(m, sweeps)
            if not rows:
                continue
            xs, ys = sweep_xy(rows, "false_fall_alarm_count")
            ax.plot(xs, ys, marker=marker, color=color, label=label, linewidth=1.8, markersize=4)
        ax.axvline(0.030, color="black", linestyle="--", linewidth=0.8, alpha=0.5)
        ax.set_title(title)
        ax.set_xlabel("epsilon (L-inf)")
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("false-fall alarms (count, non-fall->fall)")
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("Seed 42 - false-fall alarms vs attack epsilon", fontsize=12)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"[figure] wrote {out_path}")


def figure_bar_summary(baseline, fgsm_def, best, out_path):
    models = [("Clean\nbaseline", baseline), ("FGSM\ndefense", fgsm_def),
              (f"Safety-guided\n({best.selection})", best)]
    labels = [m[0] for m in models]
    x = np.arange(len(models))
    width = 0.25

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Left: fall recall (clean / FGSM / PGD).
    clean_fr = [float(m.clean_fall_recall) for _, m in models]
    fgsm_fr = [float(m.fgsm_fall_recall) for _, m in models]
    pgd_fr = [float(m.pgd_fall_recall) for _, m in models]
    axes[0].bar(x - width, clean_fr, width, label="clean", color="tab:gray")
    axes[0].bar(x, fgsm_fr, width, label="FGSM@0.030", color="tab:orange")
    axes[0].bar(x + width, pgd_fr, width, label="PGD@0.030", color="tab:green")
    axes[0].set_ylabel("fall recall")
    axes[0].set_title("Fall recall (higher = safer)")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, fontsize=9)
    axes[0].set_ylim(0, 1.05)
    axes[0].legend(fontsize=8)
    axes[0].grid(True, axis="y", alpha=0.3)

    # Right: false-fall alarms (FGSM / PGD).
    fgsm_fa = [float(m.fgsm_false_alarms) for _, m in models]
    pgd_fa = [float(m.pgd_false_alarms) for _, m in models]
    axes[1].bar(x - width / 2, fgsm_fa, width, label="FGSM@0.030", color="tab:orange")
    axes[1].bar(x + width / 2, pgd_fa, width, label="PGD@0.030", color="tab:green")
    axes[1].set_ylabel("false-fall alarms (count)")
    axes[1].set_title("False-fall alarms (lower = better)")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, fontsize=9)
    axes[1].legend(fontsize=8)
    axes[1].grid(True, axis="y", alpha=0.3)

    fig.suptitle("Seed 42 - safety-critical trade-off summary (test, n=500)", fontsize=12)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"[figure] wrote {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Seed-42 safety-guided defense comparison + figures.")
    parser.add_argument("--best-variant", default=None,
                        help="run_name of the safety-guided eval to highlight as 'best' in figures. "
                        "Default: auto-select the variant with the highest PGD@0.030 test fall recall.")
    args = parser.parse_args()

    experiment_dir = Path(__file__).resolve().parents[1]
    converged_attacks = experiment_dir / "results" / "converged_attacks"
    test_eval = experiment_dir / "results" / "safety_guided_defense" / "seed42" / "test_eval"
    figures_dir = experiment_dir / "results" / "safety_guided_defense" / "seed42" / "figures"
    out_table = experiment_dir / "results" / "safety_guided_defense" / "seed42" / "seed42_defense_comparison.csv"
    figures_dir.mkdir(parents=True, exist_ok=True)

    baseline = ModelEval("Clean LeNet baseline", "val_macro_f1", converged_attacks,
                         "converged_seed42", notes="undefended reference")
    fgsm_def = ModelEval("Existing FGSM defense", "0.5*cleanF1+0.5*fgsmF1", converged_attacks,
                         "defended_fgsm_at_seed42", notes="prior FGSM adversarial training")

    variant_runs = discover_variant_evals(test_eval)
    variant_models = []
    for run_name in variant_runs:
        display, selection = pretty_variant_name(run_name)
        variant_models.append(ModelEval(display, selection, test_eval, run_name,
                                        notes="safety-proxy-guided adversarial training"))

    all_models = [baseline, fgsm_def] + variant_models
    available_models = [m for m in all_models if m.available]
    build_table(available_models, out_table)

    # Determine the "best" safety-guided variant by PGD@0.030 test fall recall.
    best = None
    if args.best_variant:
        for m in variant_models:
            if m.run_name == args.best_variant:
                best = m
                break
        if best is None:
            print(f"[warn] --best-variant {args.best_variant} not found; auto-selecting.")
    if best is None:
        candidates = [m for m in variant_models if m.available]
        if candidates:
            best = max(candidates, key=lambda m: float(m.pgd_fall_recall))

    if best is None:
        print("[warn] no safety-guided variant eval found yet; table written, figures skipped.")
        return

    print(f"[best] highlighting {best.name} ({best.selection}) "
          f"PGD@0.030 fall recall={fmt(best.pgd_fall_recall)}")
    figure_recall_vs_epsilon(baseline, fgsm_def, best, figures_dir / "fig1_fall_recall_vs_epsilon.png")
    figure_false_alarms_vs_epsilon(baseline, fgsm_def, best, figures_dir / "fig2_false_fall_alarms_vs_epsilon.png")
    figure_bar_summary(baseline, fgsm_def, best, figures_dir / "fig3_clean_fgsm_pgd_bar_summary.png")
    print("[done] comparison + figures complete.")


if __name__ == "__main__":
    main()
