"""
Priority 1 aggregator: summarize multi-seed robustness once seed runs exist.

Purpose:
    Read the per-seed artifacts produced by run_multiseed_converged_pipeline.py
    (which calls the existing Stage 1/2/3 scripts) and aggregate them into
    seed-wise and across-seed summary tables, collapse-threshold tables, and a
    fall-recall-vs-epsilon figure with a mean +/- interval band.

    This script is missing-input tolerant by design: at this wiring stage most
    seeds have not been run, so it discovers whatever exists, writes a
    missing-input report, and never crashes unless --strict is given.

File-naming is NOT hard-coded blindly; it mirrors the conventions found in the
committed seed-42 artifacts:

    Clean baseline (per seed, run-name converged_seed{S}):
        results/converged_baseline/converged_seed{S}_fall_binary_metrics.csv
        results/converged_baseline/converged_seed{S}_summary_metrics.csv
        results/converged_baseline/converged_seed{S}_per_class_metrics.csv   (walk = class 2)
        results/converged_baseline/converged_seed{S}_test_predictions.csv     (for MCC/kappa/bal-acc)

    Undefended matched attacks (eps 0.03):
        results/converged_attacks/converged_seed{S}_{fgsm,pgd}_safety_metrics_test_epsilon_0_03.csv
        results/converged_attacks/converged_seed{S}_{fgsm,pgd}_predictions_test_epsilon_0_03.csv

    Undefended epsilon sweep (for collapse thresholds + figure):
        results/converged_attacks/converged_seed{S}_{fgsm,pgd}_epsilon_sweep_test.csv

    FGSM-AT defense (run-name defended_fgsm_at_seed{S}):
        results/converged_defense/defended_fgsm_at_seed{S}_clean_metrics_test.csv
        results/converged_attacks/defended_fgsm_at_seed{S}_{fgsm,pgd}_safety_metrics_test_epsilon_0_03.csv

Scope / claim boundary:
    Window-level safety-proxy metrics on digital-domain processed-tensor
    perturbations. Not clinical, not physical-layer/over-the-air, not certified.

Commands:
    python scripts/summarize_multiseed_robustness.py --help
    python scripts/summarize_multiseed_robustness.py --allow-missing --seeds 42 43
    python scripts/summarize_multiseed_robustness.py --seeds 42 43 44 45 46 --bootstrap 2000
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv
import math

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEEDS = [42, 43, 44, 45, 46]

# Class index 2 == "walk" in the UT-HAR label map (see per_class_metrics.csv).
WALK_CLASS_INDEX = 2

# Numeric metrics aggregated across seeds for each condition.
SUMMARY_METRICS = [
    "fall_recall",
    "missed_fall_rate",
    "false_fall_alarm_count",
    "fall_precision",
    "fall_f1",
    "accuracy",
    "macro_f1",
    "walking_recall",
    "prediction_change_rate",
    "balanced_accuracy",
    "mcc",
    "cohen_kappa",
]

# Collapse-threshold fields read/derived from the epsilon-sweep CSVs.
THRESHOLD_FIELDS = [
    "clean_fall_recall",
    "first_eps_drop_ge_0_10",
    "first_eps_recall_below_0_50",
    "first_eps_recall_zero",
]


# --------------------------------------------------------------------------- #
# Small CSV readers (no pandas dependency).
# --------------------------------------------------------------------------- #
def read_metric_value_csv(path: Path) -> dict:
    """Read a two-column metric,value CSV into a dict (values left as strings)."""
    out = {}
    with path.open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["metric"]] = row["value"]
    return out


def read_rows(path: Path) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# --------------------------------------------------------------------------- #
# Optional per-window classification metrics (MCC / kappa / balanced accuracy).
# Computed only when the prediction CSV and sklearn are available; failures are
# swallowed so the summarizer never crashes on missing extras.
# --------------------------------------------------------------------------- #
def fall_binary_extra_metrics(pred_path: Path, true_col: str, pred_col: str) -> dict:
    """Return {balanced_accuracy, mcc, cohen_kappa} for fall-vs-nonfall, or {}."""
    if not pred_path.exists():
        return {}
    try:
        from sklearn.metrics import (
            balanced_accuracy_score,
            cohen_kappa_score,
            matthews_corrcoef,
        )
    except Exception:
        return {}
    try:
        rows = read_rows(pred_path)
        y_true = [1 if int(r[true_col]) == 1 else 0 for r in rows]
        y_pred = [1 if int(r[pred_col]) == 1 else 0 for r in rows]
        if not y_true:
            return {}
        return {
            "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
            "mcc": float(matthews_corrcoef(y_true, y_pred)),
            "cohen_kappa": float(cohen_kappa_score(y_true, y_pred)),
        }
    except Exception:
        return {}


# --------------------------------------------------------------------------- #
# Per-condition extraction. Each returns (metrics_dict_or_None, missing_list).
# --------------------------------------------------------------------------- #
def walking_recall_from_per_class(path: Path):
    if not path.exists():
        return None
    for row in read_rows(path):
        if int(row.get("class_index", -1)) == WALK_CLASS_INDEX:
            return to_float(row.get("recall"))
    return None


def extract_clean(seed: int, results_root: Path):
    """Undefended clean condition for one seed."""
    base = results_root / "converged_baseline"
    fb = base / f"converged_seed{seed}_fall_binary_metrics.csv"
    summ = base / f"converged_seed{seed}_summary_metrics.csv"
    pc = base / f"converged_seed{seed}_per_class_metrics.csv"
    preds = base / f"converged_seed{seed}_test_predictions.csv"

    missing = [p for p in (fb, summ) if not p.exists()]
    if missing:
        return None, missing

    fbm = read_metric_value_csv(fb)
    sm = read_metric_value_csv(summ)
    m = {
        "fall_recall": to_float(fbm.get("fall_recall")),
        "missed_fall_rate": to_float(fbm.get("missed_fall_rate")),
        "false_fall_alarm_count": to_float(fbm.get("fall_false_positive")),
        "fall_precision": to_float(fbm.get("fall_precision")),
        "fall_f1": to_float(fbm.get("fall_f1")),
        "accuracy": to_float(sm.get("test_accuracy")),
        "macro_f1": to_float(sm.get("test_macro_f1")),
        "walking_recall": walking_recall_from_per_class(pc),
        "prediction_change_rate": None,  # not defined for clean
        "n_windows": to_float(fbm.get("fall_windows", 0)) and (
            to_float(fbm.get("fall_windows")) + to_float(fbm.get("nonfall_windows"))
        ),
        "source_file": str(fb.relative_to(REPO_ROOT)),
    }
    m.update(fall_binary_extra_metrics(preds, "fall_true_binary", "fall_pred_binary"))
    return m, []


def extract_matched_attack(seed: int, results_root: Path, attack: str, run_name: str):
    """Undefended or defended matched-epsilon (0.03) attack condition."""
    ad = results_root / "converged_attacks"
    safety = ad / f"{run_name}_{attack}_safety_metrics_test_epsilon_0_03.csv"
    preds = ad / f"{run_name}_{attack}_predictions_test_epsilon_0_03.csv"
    if not safety.exists():
        return None, [safety]

    sm = read_metric_value_csv(safety)
    m = {
        "fall_recall": to_float(sm.get("fall_recall")),
        "missed_fall_rate": to_float(sm.get("missed_fall_rate")),
        "false_fall_alarm_count": to_float(sm.get("false_fall_alarm_count")),
        "fall_precision": to_float(sm.get("fall_precision")),
        "fall_f1": to_float(sm.get("fall_f1")),
        "accuracy": to_float(sm.get("attack_accuracy")),
        "macro_f1": to_float(sm.get("attack_macro_f1")),
        "walking_recall": None,  # not in the safety CSV; left blank
        "prediction_change_rate": to_float(sm.get("prediction_change_rate")),
        "n_windows": to_float(sm.get("n_windows")),
        "source_file": str(safety.relative_to(REPO_ROOT)),
    }
    m.update(
        fall_binary_extra_metrics(
            preds, "fall_true_binary", "attacked_fall_pred_binary"
        )
    )
    return m, []


def extract_defended_clean(seed: int, results_root: Path):
    """FGSM-AT defended clean condition for one seed."""
    path = (
        results_root
        / "converged_defense"
        / f"defended_fgsm_at_seed{seed}_clean_metrics_test.csv"
    )
    if not path.exists():
        return None, [path]
    dm = read_metric_value_csv(path)
    m = {
        "fall_recall": to_float(dm.get("fall_recall")),
        "missed_fall_rate": to_float(dm.get("missed_fall_rate")),
        "false_fall_alarm_count": to_float(dm.get("fall_false_positive")),
        "fall_precision": to_float(dm.get("fall_precision")),
        "fall_f1": to_float(dm.get("fall_f1")),
        "accuracy": to_float(dm.get("accuracy")),
        "macro_f1": to_float(dm.get("macro_f1")),
        "walking_recall": None,
        "prediction_change_rate": None,
        "n_windows": to_float(dm.get("n_windows")),
        "source_file": str(path.relative_to(REPO_ROOT)),
    }
    return m, []


# Condition registry: (condition_name, extractor_callable(seed, results_root)).
def condition_extractors():
    return [
        ("clean", lambda s, r: extract_clean(s, r)),
        ("fgsm_eps0.03", lambda s, r: extract_matched_attack(s, r, "fgsm", f"converged_seed{s}")),
        ("pgd_eps0.03", lambda s, r: extract_matched_attack(s, r, "pgd", f"converged_seed{s}")),
        ("defended_clean", lambda s, r: extract_defended_clean(s, r)),
        ("defended_fgsm_eps0.03", lambda s, r: extract_matched_attack(s, r, "fgsm", f"defended_fgsm_at_seed{s}")),
        ("defended_pgd_eps0.03", lambda s, r: extract_matched_attack(s, r, "pgd", f"defended_fgsm_at_seed{s}")),
    ]


# --------------------------------------------------------------------------- #
# Collapse thresholds from epsilon-sweep CSVs.
# --------------------------------------------------------------------------- #
def collapse_thresholds_from_sweep(path: Path):
    """Return the three epsilon collapse thresholds from one sweep CSV, or None."""
    if not path.exists():
        return None
    rows = sorted(read_rows(path), key=lambda d: to_float(d.get("epsilon"), 0.0))
    if not rows:
        return None
    clean_recall = to_float(rows[0].get("fall_recall"))

    def first(predicate):
        for d in rows:
            if predicate(d):
                return to_float(d.get("epsilon"))
        return None

    return {
        "clean_fall_recall": clean_recall,
        "first_eps_drop_ge_0_10": first(
            lambda d: clean_recall is not None
            and to_float(d.get("fall_recall")) is not None
            and (clean_recall - to_float(d.get("fall_recall"))) >= 0.10
        ),
        "first_eps_recall_below_0_50": first(
            lambda d: (to_float(d.get("fall_recall")) or 0.0) < 0.50
        ),
        "first_eps_recall_zero": first(
            lambda d: to_float(d.get("fall_recall")) == 0.0
        ),
    }


# --------------------------------------------------------------------------- #
# Statistics.
# --------------------------------------------------------------------------- #
def summary_stats(values: list[float], bootstrap: int):
    """Mean / std / sem / 95% normal-t CI (+ optional bootstrap percentile CI)."""
    import numpy as np

    arr = np.asarray([v for v in values if v is not None], dtype=float)
    n = int(arr.size)
    out = {
        "n_seeds": n,
        "mean": None, "std": None, "sem": None,
        "ci95_low": None, "ci95_high": None,
        "boot_low": None, "boot_high": None,
    }
    if n == 0:
        return out

    mean = float(arr.mean())
    out["mean"] = mean
    if n == 1:
        out["std"] = 0.0
        out["sem"] = 0.0
        out["ci95_low"] = out["ci95_high"] = mean
        return out

    std = float(arr.std(ddof=1))
    sem = std / math.sqrt(n)
    out["std"] = std
    out["sem"] = sem
    # Student-t critical value; fall back to 1.96 if scipy is unavailable.
    try:
        from scipy import stats
        tcrit = float(stats.t.ppf(0.975, df=n - 1))
    except Exception:
        tcrit = 1.96
    out["ci95_low"] = mean - tcrit * sem
    out["ci95_high"] = mean + tcrit * sem

    if bootstrap and bootstrap > 0:
        rng = np.random.default_rng(12345)
        boot_means = arr[rng.integers(0, n, size=(bootstrap, n))].mean(axis=1)
        out["boot_low"] = float(np.percentile(boot_means, 2.5))
        out["boot_high"] = float(np.percentile(boot_means, 97.5))
    return out


# --------------------------------------------------------------------------- #
# CSV writers.
# --------------------------------------------------------------------------- #
def fmt(value):
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    return value


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: fmt(r.get(k)) for k in fieldnames})


# --------------------------------------------------------------------------- #
# Figure (kept inside the summarizer; skipped cleanly when no sweep data).
# --------------------------------------------------------------------------- #
def make_fall_recall_figure(seeds, results_root: Path, fig_path: Path) -> bool:
    """Mean +/- 95% CI fall-recall-vs-epsilon band for FGSM and PGD. Returns True if drawn."""
    import numpy as np

    attacks_dir = results_root / "converged_attacks"
    series = {}  # attack -> {epsilon: [recall per seed]}
    for attack in ("fgsm", "pgd"):
        per_eps = {}
        for s in seeds:
            path = attacks_dir / f"converged_seed{s}_{attack}_epsilon_sweep_test.csv"
            if not path.exists():
                continue
            for row in read_rows(path):
                eps = to_float(row.get("epsilon"))
                rec = to_float(row.get("fall_recall"))
                if eps is None or rec is None:
                    continue
                per_eps.setdefault(eps, []).append(rec)
        if per_eps:
            series[attack] = per_eps

    if not series:
        return False

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from scipy import stats
    except Exception:
        return False

    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = {"fgsm": "#d1495b", "pgd": "#30638e"}
    for attack, per_eps in series.items():
        xs = sorted(per_eps)
        means, los, his = [], [], []
        for eps in xs:
            vals = np.asarray(per_eps[eps], dtype=float)
            m = float(vals.mean())
            means.append(m)
            n = vals.size
            if n > 1:
                sem = float(vals.std(ddof=1)) / math.sqrt(n)
                tcrit = float(stats.t.ppf(0.975, df=n - 1))
                los.append(m - tcrit * sem)
                his.append(m + tcrit * sem)
            else:
                los.append(m)
                his.append(m)
        ax.plot(xs, means, marker="o", color=colors.get(attack), label=f"{attack.upper()} mean")
        ax.fill_between(xs, los, his, color=colors.get(attack), alpha=0.20)

    ax.set_xlabel("Perturbation epsilon (L-inf, processed-tensor)")
    ax.set_ylabel("Fall recall (window-level safety proxy)")
    ax.set_title("Multi-seed fall recall vs epsilon (mean +/- 95% CI)")
    ax.set_ylim(-0.02, 1.02)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(fig_path, dpi=150)
    plt.close(fig)
    return True


# --------------------------------------------------------------------------- #
# Main.
# --------------------------------------------------------------------------- #
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Aggregate multi-seed converged-pipeline robustness outputs "
        "(Priority 1). Missing-input tolerant unless --strict.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--seeds", type=int, nargs="+", default=DEFAULT_SEEDS)
    p.add_argument("--results-root", type=Path, default=REPO_ROOT / "results")
    p.add_argument("--out-dir", type=Path, default=REPO_ROOT / "results" / "multiseed_robustness")
    p.add_argument("--fig-dir", type=Path, default=REPO_ROOT / "figures" / "multiseed_robustness")
    p.add_argument("--bootstrap", type=int, default=1000, help="Bootstrap resamples for CI (0 disables).")
    p.add_argument("--allow-missing", action="store_true",
                   help="Summarize whatever exists and warn about missing seeds (default behavior).")
    p.add_argument("--strict", action="store_true",
                   help="Exit non-zero if any expected input is missing.")
    p.add_argument("--no-figure", action="store_true", help="Do not attempt to draw the figure.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    results_root = args.results_root
    extractors = condition_extractors()

    condition_rows = []   # seed-wise per-condition metrics
    missing_rows = []     # missing-input report
    threshold_rows = []   # per-seed collapse thresholds

    print("=" * 78)
    print("Multi-seed robustness summarizer (Priority 1)")
    print("-" * 78)
    print(f"Results root: {results_root}")
    print(f"Seeds:        {args.seeds}")
    print(f"Out dir:      {args.out_dir}")
    print(f"Bootstrap:    {args.bootstrap}")
    print("=" * 78)

    # ---- Gather per-seed, per-condition metrics. ----
    for seed in args.seeds:
        for cond_name, extractor in extractors:
            metrics, missing = extractor(seed, results_root)
            if metrics is None:
                for mp in missing:
                    missing_rows.append({
                        "seed": seed, "condition": cond_name,
                        "expected_path": str(Path(mp)),
                        "status": "missing",
                    })
                print(f"  seed {seed:>3} | {cond_name:<22} : MISSING")
                continue
            row = {"seed": seed, "condition": cond_name}
            row.update(metrics)
            condition_rows.append(row)
            fr = metrics.get("fall_recall")
            print(f"  seed {seed:>3} | {cond_name:<22} : fall_recall={fmt(fr)}")

        # ---- Collapse thresholds from undefended sweeps. ----
        for attack in ("fgsm", "pgd"):
            sweep = results_root / "converged_attacks" / f"converged_seed{seed}_{attack}_epsilon_sweep_test.csv"
            th = collapse_thresholds_from_sweep(sweep)
            if th is None:
                missing_rows.append({
                    "seed": seed, "condition": f"{attack}_epsilon_sweep",
                    "expected_path": str(sweep), "status": "missing",
                })
                continue
            trow = {"seed": seed, "attack": attack}
            trow.update(th)
            threshold_rows.append(trow)

    # ---- Write seed-wise condition metrics. ----
    cond_fields = ["seed", "condition"] + SUMMARY_METRICS + ["n_windows", "source_file"]
    write_csv(args.out_dir / "multiseed_condition_metrics.csv", cond_fields, condition_rows)

    # ---- Across-seed summary stats per (condition, metric). ----
    summary_rows = []
    by_condition = {}
    for row in condition_rows:
        by_condition.setdefault(row["condition"], []).append(row)
    for cond_name, _ in extractors:
        rows = by_condition.get(cond_name, [])
        for metric in SUMMARY_METRICS:
            stats_d = summary_stats([r.get(metric) for r in rows], args.bootstrap)
            summary_rows.append({
                "condition": cond_name, "metric": metric, **stats_d,
            })
    summary_fields = ["condition", "metric", "n_seeds", "mean", "std", "sem",
                      "ci95_low", "ci95_high", "boot_low", "boot_high"]
    write_csv(args.out_dir / "multiseed_summary_stats.csv", summary_fields, summary_rows)

    # ---- Collapse thresholds: per-seed rows + per-attack mean/std rows. ----
    collapse_out = list(threshold_rows)
    by_attack = {}
    for row in threshold_rows:
        by_attack.setdefault(row["attack"], []).append(row)
    for attack, rows in by_attack.items():
        for agg_label in ("mean", "std"):
            agg_row = {"seed": agg_label, "attack": attack}
            for field in THRESHOLD_FIELDS:
                stats_d = summary_stats([r.get(field) for r in rows], 0)
                agg_row[field] = stats_d["mean"] if agg_label == "mean" else stats_d["std"]
            collapse_out.append(agg_row)
    collapse_fields = ["seed", "attack"] + THRESHOLD_FIELDS
    write_csv(args.out_dir / "multiseed_collapse_thresholds.csv", collapse_fields, collapse_out)

    # ---- Missing-input report (always written, even if empty). ----
    write_csv(
        args.out_dir / "multiseed_missing_inputs.csv",
        ["seed", "condition", "expected_path", "status"],
        missing_rows,
    )

    # ---- Figure (optional / tolerant). ----
    fig_drawn = False
    if not args.no_figure:
        fig_path = args.fig_dir / "multiseed_fall_recall_vs_epsilon.png"
        fig_drawn = make_fall_recall_figure(args.seeds, results_root, fig_path)
        if fig_drawn:
            print(f"Figure written: {fig_path}")
        else:
            print("Figure skipped: no epsilon-sweep data found yet.")

    print("-" * 78)
    print(f"Condition rows:    {len(condition_rows)}")
    print(f"Threshold rows:    {len(threshold_rows)}")
    print(f"Missing inputs:    {len(missing_rows)}")
    print(f"Outputs written to: {args.out_dir}")
    print("-" * 78)

    if missing_rows and args.strict:
        print(f"[strict] {len(missing_rows)} missing input(s); exiting non-zero.")
        return 1
    if missing_rows:
        print(f"[ok] {len(missing_rows)} input(s) not yet available; "
              f"see multiseed_missing_inputs.csv. (use --strict to fail instead)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
