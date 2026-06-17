"""
Generate Chapter 4 converged-test-split artifacts from the committed
converged_seed42_* result CSVs.

Purpose:
    Rebuild the Chapter 4 tables and figures (epsilon-sweep selected table,
    multiclass error pathways, dangerous-transition / walking-class numbers,
    dose-response plot + zoom, fall error-pathway figure, seven-class confusion
    matrices) using the NEW converged baseline + attack results on the primary
    held-out TEST split (n=500). Legacy val+test (n=996) is NOT used for the
    primary Chapter 4 artifacts.

    Old generator scripts and old pilot artifacts are left untouched; all
    outputs here go to new namespaces:
        results/converged_ch04_artifacts/
        figures/converged_ch04_artifacts/

Scope:
    Window-level, software-tensor evaluation. Not physical-layer/over-the-air,
    not clinical, not event-level.

Commands:
    python scripts/generate_ch04_converged_artifacts.py --help
    python scripts/generate_ch04_converged_artifacts.py
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


CLASS_NAMES = {
    0: "lie down", 1: "fall", 2: "walk", 3: "pickup",
    4: "run", 5: "sit down", 6: "stand up",
}
NUM_CLASSES = 7
FALL = 1
WALK = 2
DEFAULT_SELECTED_EPS = [0.0, 0.0025, 0.0050, 0.0075, 0.0100, 0.0300]


def read_rows(path: Path) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fpr_from(fp: float, tn: float) -> float:
    return fp / (fp + tn) if (fp + tn) > 0 else 0.0


def safety_score(mfr: float, fpr: float) -> float:
    return 10.0 * mfr + fpr


# ---------------------------------------------------------------------------
# 1. Epsilon-sweep selected table (tab:ch04-epsilon-sweep-selected)
# ---------------------------------------------------------------------------
def build_sweep_selected(fgsm_sweep, pgd_sweep, selected_eps, out_csv):
    def pick(rows, attack):
        out = []
        for eps in selected_eps:
            match = None
            for r in rows:
                if abs(float(r["epsilon"]) - eps) < 1e-9:
                    match = r
                    break
            if match is None:
                continue
            fp = float(match["fall_false_positive"])
            tn = float(match["fall_true_negative"])
            mfr = float(match["missed_fall_rate"])
            fpr = fpr_from(fp, tn)
            out.append({
                "attack": attack,
                "epsilon": f"{eps:.4f}",
                "accuracy": f"{float(match['attack_accuracy']):.4f}",
                "missed_fall_rate": f"{mfr:.4f}",
                "false_positive_rate": f"{fpr:.4f}",
                "safety_score_10_to_1": f"{safety_score(mfr, fpr):.4f}",
                "tp_fn_fp_tn": f"{int(float(match['fall_true_positive']))}/"
                               f"{int(float(match['fall_false_negative']))}/"
                               f"{int(fp)}/{int(tn)}",
            })
        return out

    rows = pick(fgsm_sweep, "FGSM") + pick(pgd_sweep, "PGD")
    fields = ["attack", "epsilon", "accuracy", "missed_fall_rate",
              "false_positive_rate", "safety_score_10_to_1", "tp_fn_fp_tn"]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return rows


# ---------------------------------------------------------------------------
# Transition helpers
# ---------------------------------------------------------------------------
def true_and_pred(rows, attacked: bool):
    """Return (true_labels, pred_labels). For attack CSVs, attacked=True uses
    attacked_predicted_label; the clean CSV uses predicted_label."""
    yt, yp = [], []
    for r in rows:
        yt.append(int(r["true_label"]))
        if "attacked_predicted_label" in r:
            yp.append(int(r["attacked_predicted_label"] if attacked else r["clean_predicted_label"]))
        else:
            yp.append(int(r["predicted_label"]))
    return np.array(yt), np.array(yp)


def fall_to_nonfall(yt, yp):
    counts = {}
    for c in range(NUM_CLASSES):
        if c == FALL:
            continue
        n = int(np.sum((yt == FALL) & (yp == c)))
        if n > 0:
            counts[CLASS_NAMES[c]] = n
    return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))


def nonfall_to_fall(yt, yp):
    counts = {}
    for c in range(NUM_CLASSES):
        if c == FALL:
            continue
        n = int(np.sum((yt == c) & (yp == FALL)))
        if n > 0:
            counts[CLASS_NAMES[c]] = n
    return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))


def fmt_pathways(d, src_to_fall=False):
    if not d:
        return "none"
    if src_to_fall:
        return "; ".join(f"{k} $\\rightarrow$ fall: {v}" for k, v in d.items())
    return "; ".join(f"fall $\\rightarrow$ {k}: {v}" for k, v in d.items())


# ---------------------------------------------------------------------------
# 2/3. Multiclass error pathways + dangerous transitions + walking class
# ---------------------------------------------------------------------------
def build_pathways(conditions, out_pathways_csv, out_detail_csv):
    pathway_rows = []
    detail_rows = []
    for name, yt, yp in conditions:
        miss = fall_to_nonfall(yt, yp)
        fa = nonfall_to_fall(yt, yp)
        pathway_rows.append({
            "condition": name,
            "missed_fall_pathways": fmt_pathways(miss),
            "false_fall_alarm_pathways": fmt_pathways(fa, src_to_fall=True),
        })
        for k, v in miss.items():
            detail_rows.append({"condition": name, "direction": "fall_to_nonfall",
                                "other_class": k, "count": v})
        for k, v in fa.items():
            detail_rows.append({"condition": name, "direction": "nonfall_to_fall",
                                "other_class": k, "count": v})

    with out_pathways_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["condition", "missed_fall_pathways",
                                          "false_fall_alarm_pathways"])
        w.writeheader()
        w.writerows(pathway_rows)
    with out_detail_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["condition", "direction", "other_class", "count"])
        w.writeheader()
        w.writerows(detail_rows)
    return pathway_rows


def build_walking(clean, fgsm, pgd, out_csv):
    yt_c, yp_c = true_and_pred(clean, attacked=False)
    yt_f, yp_f = true_and_pred(fgsm, attacked=True)
    yt_p, yp_p = true_and_pred(pgd, attacked=True)

    total_walk = int(np.sum(yt_c == WALK))
    clean_correct = int(np.sum((yt_c == WALK) & (yp_c == WALK)))
    fgsm_correct = int(np.sum((yt_f == WALK) & (yp_f == WALK)))
    pgd_correct = int(np.sum((yt_p == WALK) & (yp_p == WALK)))
    fgsm_walk_to_fall = int(np.sum((yt_f == WALK) & (yp_f == FALL)))
    pgd_walk_to_fall = int(np.sum((yt_p == WALK) & (yp_p == FALL)))

    def rec(n):
        return n / total_walk if total_walk else 0.0

    rows = {
        "total_walking_windows": total_walk,
        "clean_walking_correct": clean_correct,
        "clean_walking_recall": round(rec(clean_correct), 4),
        "fgsm_walking_correct": fgsm_correct,
        "fgsm_walking_recall": round(rec(fgsm_correct), 4),
        "pgd_walking_correct": pgd_correct,
        "pgd_walking_recall": round(rec(pgd_correct), 4),
        "fgsm_walking_availability_drop": round(1 - (fgsm_correct / clean_correct), 4) if clean_correct else 0.0,
        "pgd_walking_availability_drop": round(1 - (pgd_correct / clean_correct), 4) if clean_correct else 0.0,
        "fgsm_walk_to_fall_count": fgsm_walk_to_fall,
        "pgd_walk_to_fall_count": pgd_walk_to_fall,
        "fgsm_walk_to_fall_rate": round(rec(fgsm_walk_to_fall), 4),
        "pgd_walk_to_fall_rate": round(rec(pgd_walk_to_fall), 4),
    }
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        for k, v in rows.items():
            w.writerow([k, v])
    return rows


# ---------------------------------------------------------------------------
# 4/5. Dose-response + zoom figures
# ---------------------------------------------------------------------------
def sweep_series(rows):
    rows = sorted(rows, key=lambda r: float(r["epsilon"]))
    eps = [float(r["epsilon"]) for r in rows]
    acc = [float(r["attack_accuracy"]) for r in rows]
    mfr = [float(r["missed_fall_rate"]) for r in rows]
    fpr = [fpr_from(float(r["fall_false_positive"]), float(r["fall_true_negative"])) for r in rows]
    ss = [safety_score(m, f) for m, f in zip(mfr, fpr)]
    return eps, acc, mfr, fpr, ss


def dose_response_figure(fgsm_sweep, pgd_sweep, out_png, xmax=None, title_suffix=""):
    ef, af, mf, ff, sf = sweep_series(fgsm_sweep)
    ep, ap, mp, fp, sp = sweep_series(pgd_sweep)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    panels = [
        ("Missed-fall rate", mf, mp),
        ("False-positive rate", ff, fp),
        ("Safety-priority score (10:1)", sf, sp),
        ("Attacked accuracy", af, ap),
    ]
    for ax, (label, fv, pv) in zip(axes.ravel(), panels):
        ax.plot(ef, fv, "o-", label="FGSM", color="#1f77b4")
        ax.plot(ep, pv, "s-", label="PGD", color="#d62728")
        ax.set_xlabel(r"$\epsilon$")
        ax.set_ylabel(label)
        ax.set_title(label)
        ax.grid(True, alpha=0.3)
        if xmax is not None:
            ax.set_xlim(0, xmax)
        ax.legend()
    fig.suptitle(f"Converged test-split attack-severity dose response{title_suffix}", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)


def error_pathway_figure(fgsm, pgd, out_png):
    yt_f, yp_f = true_and_pred(fgsm, attacked=True)
    yt_p, yp_p = true_and_pred(pgd, attacked=True)
    classes = [CLASS_NAMES[c] for c in range(NUM_CLASSES) if c != FALL]

    def miss_vec(yt, yp):
        return [int(np.sum((yt == FALL) & (yp == c))) for c in range(NUM_CLASSES) if c != FALL]

    def fa_vec(yt, yp):
        return [int(np.sum((yt == c) & (yp == FALL))) for c in range(NUM_CLASSES) if c != FALL]

    x = np.arange(len(classes))
    w = 0.38
    fig, (a, b) = plt.subplots(1, 2, figsize=(13, 5))
    a.bar(x - w / 2, miss_vec(yt_f, yp_f), w, label="FGSM", color="#1f77b4")
    a.bar(x + w / 2, miss_vec(yt_p, yp_p), w, label="PGD", color="#d62728")
    a.set_title("Panel A: fall $\\rightarrow$ non-fall (missed-fall)")
    a.set_xticks(x); a.set_xticklabels(classes, rotation=30, ha="right")
    a.set_ylabel("window count"); a.legend(); a.grid(True, axis="y", alpha=0.3)
    b.bar(x - w / 2, fa_vec(yt_f, yp_f), w, label="FGSM", color="#1f77b4")
    b.bar(x + w / 2, fa_vec(yt_p, yp_p), w, label="PGD", color="#d62728")
    b.set_title("Panel B: non-fall $\\rightarrow$ fall (false alarm)")
    b.set_xticks(x); b.set_xticklabels(classes, rotation=30, ha="right")
    b.set_ylabel("window count"); b.legend(); b.grid(True, axis="y", alpha=0.3)
    fig.suptitle("Converged test-split high-risk multiclass fall-error pathways ($\\epsilon=0.030$)", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)


def confusion_matrix(yt, yp):
    m = np.zeros((NUM_CLASSES, NUM_CLASSES), dtype=int)
    for t, p in zip(yt, yp):
        m[t, p] += 1
    return m


def confusion_figure(clean, fgsm, pgd, out_png):
    panels = [
        ("Clean", *true_and_pred(clean, attacked=False)),
        ("FGSM $\\epsilon=0.030$", *true_and_pred(fgsm, attacked=True)),
        ("PGD $\\epsilon=0.030$", *true_and_pred(pgd, attacked=True)),
    ]
    labels = [CLASS_NAMES[c] for c in range(NUM_CLASSES)]
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    for ax, (name, yt, yp) in zip(axes, panels):
        m = confusion_matrix(yt, yp)
        im = ax.imshow(m, cmap="Blues")
        ax.set_title(f"{name}")
        ax.set_xticks(range(NUM_CLASSES)); ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(NUM_CLASSES)); ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel("predicted"); ax.set_ylabel("true")
        thresh = m.max() / 2 if m.max() > 0 else 0.5
        for i in range(NUM_CLASSES):
            for j in range(NUM_CLASSES):
                ax.text(j, i, m[i, j], ha="center", va="center",
                        color="white" if m[i, j] > thresh else "black", fontsize=8)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("Converged test-split seven-class confusion matrices", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)


def parse_args():
    p = argparse.ArgumentParser(
        description="Generate Chapter 4 converged test-split artifacts (tables + figures).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--run-name", default="converged_seed42", help="Run name of the input CSVs.")
    p.add_argument("--selected-epsilons", default=",".join(str(e) for e in DEFAULT_SELECTED_EPS),
                   help="Comma-separated epsilons for the selected sweep table.")
    return p.parse_args()


def main():
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    baseline = root / "results" / "converged_baseline"
    attacks = root / "results" / "converged_attacks"
    out_res = root / "results" / "converged_ch04_artifacts"
    out_fig = root / "figures" / "converged_ch04_artifacts"
    out_res.mkdir(parents=True, exist_ok=True)
    out_fig.mkdir(parents=True, exist_ok=True)

    rn = args.run_name
    inputs = {
        "clean": baseline / f"{rn}_test_predictions.csv",
        "fgsm": attacks / f"{rn}_fgsm_predictions_test_epsilon_0_03.csv",
        "pgd": attacks / f"{rn}_pgd_predictions_test_epsilon_0_03.csv",
        "fgsm_sweep": attacks / f"{rn}_fgsm_epsilon_sweep_test.csv",
        "pgd_sweep": attacks / f"{rn}_pgd_epsilon_sweep_test.csv",
    }
    for k, v in inputs.items():
        if not v.exists():
            raise FileNotFoundError(f"Missing input '{k}': {v}")

    clean = read_rows(inputs["clean"])
    fgsm = read_rows(inputs["fgsm"])
    pgd = read_rows(inputs["pgd"])
    fgsm_sweep = read_rows(inputs["fgsm_sweep"])
    pgd_sweep = read_rows(inputs["pgd_sweep"])
    selected_eps = [float(x) for x in args.selected_epsilons.split(",")]

    # Tables
    sweep_csv = out_res / "ch04_epsilon_sweep_selected.csv"
    pathways_csv = out_res / "ch04_multiclass_error_pathways.csv"
    detail_csv = out_res / "ch04_transition_detail.csv"
    walking_csv = out_res / "ch04_walking_class_vulnerability.csv"

    sweep_rows = build_sweep_selected(fgsm_sweep, pgd_sweep, selected_eps, sweep_csv)

    yt_c, yp_c = true_and_pred(clean, attacked=False)
    yt_f, yp_f = true_and_pred(fgsm, attacked=True)
    yt_p, yp_p = true_and_pred(pgd, attacked=True)
    conditions = [
        ("Undefended clean", yt_c, yp_c),
        (r"Undefended FGSM, $\epsilon=0.030$", yt_f, yp_f),
        (r"Undefended PGD, $\epsilon=0.030$", yt_p, yp_p),
    ]
    pathway_rows = build_pathways(conditions, pathways_csv, detail_csv)
    walking = build_walking(clean, fgsm, pgd, walking_csv)

    # Figures
    fig42 = out_fig / "ch04_figure_4_2_attack_severity_dose_response.png"
    fig43 = out_fig / "ch04_figure_4_3_attack_severity_zoom.png"
    fig44 = out_fig / "ch04_figure_4_4_multiclass_fall_error_pathways.png"
    fig45 = out_fig / "ch04_figure_4_5_seven_class_confusion_matrices.png"
    dose_response_figure(fgsm_sweep, pgd_sweep, fig42)
    dose_response_figure(fgsm_sweep, pgd_sweep, fig43, xmax=0.02, title_suffix=" (low-$\\epsilon$ zoom)")
    error_pathway_figure(fgsm, pgd, fig44)
    confusion_figure(clean, fgsm, pgd, fig45)

    # Metadata
    meta_path = out_res / "ch04_converged_artifacts_metadata.json"
    metadata = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "run_name": rn,
        "split_used": "primary test split (n=500)",
        "legacy_note": "Legacy val+test (n=996) is NOT used for primary Chapter 4 figures/tables.",
        "input_files": {k: str(v) for k, v in inputs.items()},
        "formulas": {
            "false_positive_rate": "FP / (FP + TN)",
            "safety_score_10_to_1": "10 * missed_fall_rate + false_positive_rate",
        },
        "selected_epsilons": selected_eps,
        "generated_tables": [str(sweep_csv), str(pathways_csv), str(detail_csv), str(walking_csv)],
        "generated_figures": [str(fig42), str(fig43), str(fig44), str(fig45)],
        "scope": "window-level software-tensor; not physical/over-the-air, not clinical, not event-level",
    }
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("Chapter 4 converged artifact generation complete.")
    print(f"Tables  -> {out_res}")
    print(f"Figures -> {out_fig}")
    print("\nSweep selected rows:")
    for r in sweep_rows:
        print(f"  {r['attack']:4s} eps={r['epsilon']} acc={r['accuracy']} "
              f"MFR={r['missed_fall_rate']} FPR={r['false_positive_rate']} "
              f"safety={r['safety_score_10_to_1']} TP/FN/FP/TN={r['tp_fn_fp_tn']}")
    print("\nMulticlass error pathways:")
    for r in pathway_rows:
        print(f"  [{r['condition']}]")
        print(f"     missed: {r['missed_fall_pathways']}")
        print(f"     false-alarm: {r['false_fall_alarm_pathways']}")
    print("\nWalking-class vulnerability:")
    for k, v in walking.items():
        print(f"  {k}: {v}")
    print(f"\nMetadata -> {meta_path}")


if __name__ == "__main__":
    main()
