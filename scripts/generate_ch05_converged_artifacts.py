"""
Generate Chapter 5 (safety-proxy interpretation) converged-test-split artifacts.

Reads ONLY existing committed converged result CSVs (no retraining, no re-attack)
and produces the Chapter 5 tables and figures on the primary 500-window test
split, with defended rows refreshed from the Stage 3 converged FGSM
adversarial-training defense.

Conditions:
    clean (undefended), FGSM eps0.03 (undefended), PGD eps0.03 (undefended),
    defended clean, defended FGSM eps0.03, defended PGD eps0.03.

Defended-clean predictions are taken from the `clean_predicted_label` column of
the Stage 3 defended attack CSVs (the defended model's unperturbed prediction
for each window).

Scope: window-level safety-proxy evaluation of digital/software-tensor
perturbations. Not clinical, not medical-device, not physical/over-the-air,
not event-level/long-lie, not fall-risk prediction, not certified robustness.
The defense is partial and attack-specific (mitigates, does not solve).

Outputs (new namespaces only; Chapter 4 folders untouched):
    results/converged_ch05_artifacts/
    figures/converged_ch05_artifacts/
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
import math
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


CLASS_NAMES = {0: "lie down", 1: "fall", 2: "walk", 3: "pickup", 4: "run", 5: "sit down", 6: "stand up"}
NUM_CLASSES = 7
FALL = 1


def read_rows(path: Path) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sd(num, den):
    return num / den if den else 0.0


# ---------------------------------------------------------------------------
# Load the six conditions as (y_true_multi, y_pred_multi, pred_change_rate)
# ---------------------------------------------------------------------------
def load_conditions(root: Path):
    base = root / "results" / "converged_baseline"
    atk = root / "results" / "converged_attacks"

    clean = read_rows(base / "converged_seed42_test_predictions.csv")
    fgsm = read_rows(atk / "converged_seed42_fgsm_predictions_test_epsilon_0_03.csv")
    pgd = read_rows(atk / "converged_seed42_pgd_predictions_test_epsilon_0_03.csv")
    dfgsm = read_rows(atk / "defended_fgsm_at_seed42_fgsm_predictions_test_epsilon_0_03.csv")
    dpgd = read_rows(atk / "defended_fgsm_at_seed42_pgd_predictions_test_epsilon_0_03.csv")

    def col(rows, name):
        return np.array([int(r[name]) for r in rows])

    def pcr(rows):
        return float(np.mean([int(r["prediction_changed"]) for r in rows]))

    conditions = {}
    # multiclass true is identical across files; use clean file's true_label
    conditions["clean"] = {
        "label": "Undefended clean",
        "y_true": col(clean, "true_label"),
        "y_pred": col(clean, "predicted_label"),
        "pred_change": None,
    }
    conditions["fgsm"] = {
        "label": r"Undefended FGSM, $\epsilon=0.03$",
        "y_true": col(fgsm, "true_label"),
        "y_pred": col(fgsm, "attacked_predicted_label"),
        "pred_change": pcr(fgsm),
    }
    conditions["pgd"] = {
        "label": r"Undefended PGD, $\epsilon=0.03$",
        "y_true": col(pgd, "true_label"),
        "y_pred": col(pgd, "attacked_predicted_label"),
        "pred_change": pcr(pgd),
    }
    conditions["def_clean"] = {
        "label": "Defended clean",
        "y_true": col(dfgsm, "true_label"),
        "y_pred": col(dfgsm, "clean_predicted_label"),
        "pred_change": None,
    }
    conditions["def_fgsm"] = {
        "label": r"Defended FGSM, $\epsilon=0.03$",
        "y_true": col(dfgsm, "true_label"),
        "y_pred": col(dfgsm, "attacked_predicted_label"),
        "pred_change": pcr(dfgsm),
    }
    conditions["def_pgd"] = {
        "label": r"Defended PGD, $\epsilon=0.03$",
        "y_true": col(dpgd, "true_label"),
        "y_pred": col(dpgd, "attacked_predicted_label"),
        "pred_change": pcr(dpgd),
    }
    return conditions


def binary_confusion(y_true, y_pred):
    t = (y_true == FALL).astype(int)
    p = (y_pred == FALL).astype(int)
    tp = int(np.sum((t == 1) & (p == 1)))
    fn = int(np.sum((t == 1) & (p == 0)))
    fp = int(np.sum((t == 0) & (p == 1)))
    tn = int(np.sum((t == 0) & (p == 0)))
    return tp, fn, fp, tn


def diagnostics(tp, fn, fp, tn):
    n = tp + fn + fp + tn
    recall = sd(tp, tp + fn)
    specificity = sd(tn, tn + fp)
    precision = sd(tp, tp + fp)
    npv = sd(tn, tn + fn)
    f1 = sd(2 * precision * recall, precision + recall)
    fom = sd(fn, fn + tn)          # false omission rate
    fdr = sd(fp, fp + tp)          # false discovery rate
    bal = (recall + specificity) / 2
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = ((tp * tn - fp * fn) / denom) if denom > 0 else 0.0
    po = sd(tp + tn, n)
    pe = sd((tp + fn) * (tp + fp) + (fn + tn) * (fp + tn), n * n) if n else 0.0
    kappa = sd(po - pe, 1 - pe) if (1 - pe) != 0 else 0.0
    return {
        "sensitivity_recall": recall, "specificity": specificity, "precision_ppv": precision,
        "npv": npv, "f1": f1, "false_omission_rate": fom, "false_discovery_rate": fdr,
        "balanced_accuracy": bal, "mcc": mcc, "cohen_kappa": kappa,
        "missed_fall_rate": sd(fn, tp + fn),
    }


def write_csv(path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def fmt(x, nd=4):
    return f"{x:.{nd}f}" if isinstance(x, float) else x


# ---------------------------------------------------------------------------
# A. Robustness failure thresholds (from sweeps)
# ---------------------------------------------------------------------------
def thresholds_from_sweep(rows):
    rows = sorted(rows, key=lambda r: float(r["epsilon"]))
    clean_recall = float(rows[0]["fall_recall"])

    def first(pred):
        for r in rows:
            if pred(r):
                return float(r["epsilon"])
        return None

    return {
        "clean_fall_recall": clean_recall,
        "first_eps_drop_ge_0_10": first(lambda r: (clean_recall - float(r["fall_recall"])) >= 0.10),
        "first_eps_recall_below_0_50": first(lambda r: float(r["fall_recall"]) < 0.50),
        "first_eps_recall_zero": first(lambda r: float(r["fall_recall"]) == 0.0),
    }


def build_thresholds(root, out_csv):
    atk = root / "results" / "converged_attacks"
    sweeps = [
        ("FGSM", "undefended", atk / "converged_seed42_fgsm_epsilon_sweep_test.csv"),
        ("PGD", "undefended", atk / "converged_seed42_pgd_epsilon_sweep_test.csv"),
        ("FGSM", "defended", atk / "defended_fgsm_at_seed42_fgsm_epsilon_sweep_test.csv"),
        ("PGD", "defended", atk / "defended_fgsm_at_seed42_pgd_epsilon_sweep_test.csv"),
    ]
    rows = []
    for attack, status, path in sweeps:
        if not path.exists():
            rows.append({"attack": attack, "model": status, "clean_fall_recall": "unavailable",
                         "first_eps_drop_ge_0_10": "unavailable",
                         "first_eps_recall_below_0_50": "unavailable",
                         "first_eps_recall_zero": "unavailable"})
            continue
        t = thresholds_from_sweep(read_rows(path))
        rows.append({
            "attack": attack, "model": status,
            "clean_fall_recall": fmt(t["clean_fall_recall"]),
            "first_eps_drop_ge_0_10": t["first_eps_drop_ge_0_10"] if t["first_eps_drop_ge_0_10"] is not None else "never",
            "first_eps_recall_below_0_50": t["first_eps_recall_below_0_50"] if t["first_eps_recall_below_0_50"] is not None else "never",
            "first_eps_recall_zero": t["first_eps_recall_zero"] if t["first_eps_recall_zero"] is not None else "never",
        })
    write_csv(out_csv, ["attack", "model", "clean_fall_recall", "first_eps_drop_ge_0_10",
                        "first_eps_recall_below_0_50", "first_eps_recall_zero"], rows)
    return rows


def main():
    ap = argparse.ArgumentParser(description="Generate Chapter 5 converged test-split artifacts.",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--strict", action="store_true", default=True,
                    help="Fail if primary clean/FGSM/PGD rows do not match Chapter 4 values.")
    ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    out_res = root / "results" / "converged_ch05_artifacts"
    out_fig = root / "figures" / "converged_ch05_artifacts"
    out_res.mkdir(parents=True, exist_ok=True)
    out_fig.mkdir(parents=True, exist_ok=True)

    conditions = load_conditions(root)
    order = ["clean", "fgsm", "pgd", "def_clean", "def_fgsm", "def_pgd"]

    # Per-condition confusion + diagnostics
    cond_stats = {}
    for k in order:
        c = conditions[k]
        tp, fn, fp, tn = binary_confusion(c["y_true"], c["y_pred"])
        d = diagnostics(tp, fn, fp, tn)
        cond_stats[k] = {"label": c["label"], "tp": tp, "fn": fn, "fp": fp, "tn": tn,
                         "pred_change": c["pred_change"], **d}

    # ---- VALIDATION against Chapter 4 ----
    errors = []
    def check(name, got, exp, tol=1e-3):
        ok = (abs(got - exp) <= tol) if isinstance(exp, float) else (got == exp)
        if not ok:
            errors.append(f"{name}: got {got}, expected {exp}")
    cl, fg, pg = cond_stats["clean"], cond_stats["fgsm"], cond_stats["pgd"]
    check("clean TP/FN/FP/TN", (cl["tp"], cl["fn"], cl["fp"], cl["tn"]), (43, 2, 0, 455))
    check("fgsm TP/FN/FP/TN", (fg["tp"], fg["fn"], fg["fp"], fg["tn"]), (0, 45, 47, 408))
    check("pgd TP/FN/FP/TN", (pg["tp"], pg["fn"], pg["fp"], pg["tn"]), (0, 45, 48, 407))
    check("clean fall recall", cl["sensitivity_recall"], 0.9556)
    check("clean missed-fall rate", cl["missed_fall_rate"], 0.0444)
    check("fgsm missed-fall rate", fg["missed_fall_rate"], 1.0)
    check("pgd missed-fall rate", pg["missed_fall_rate"], 1.0)
    check("fgsm pred-change", fg["pred_change"], 0.9520)
    check("pgd pred-change", pg["pred_change"], 0.9720)
    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print("  - " + e)
        raise SystemExit(1)
    print("VALIDATION PASSED: primary clean/FGSM/PGD rows match Chapter 4.\n")

    # ---- A. thresholds ----
    thr_rows = build_thresholds(root, out_res / "ch05_robustness_failure_thresholds.csv")

    # ---- B. risk amplification (no FP ratio: clean FP=0) ----
    clean_mfr = cl["missed_fall_rate"]
    ra_rows = []
    for k in order:
        s = cond_stats[k]
        ra_rows.append({
            "condition": s["label"],
            "fall_recall": fmt(s["sensitivity_recall"]),
            "missed_fall_rate": fmt(s["missed_fall_rate"]),
            "missed_fall_rate_ratio_vs_clean": fmt(sd(s["missed_fall_rate"], clean_mfr)) if clean_mfr else "n/a",
            "missed_fall_count": s["fn"],
            "false_fall_alarm_count": s["fp"],
            "false_alarm_increase_vs_clean": s["fp"] - cl["fp"],
            "false_alarm_ratio_vs_clean": "undefined (clean FP=0)",
            "prediction_change_rate": fmt(s["pred_change"]) if s["pred_change"] is not None else "n/a",
        })
    write_csv(out_res / "ch05_risk_amplification.csv",
              ["condition", "fall_recall", "missed_fall_rate", "missed_fall_rate_ratio_vs_clean",
               "missed_fall_count", "false_fall_alarm_count", "false_alarm_increase_vs_clean",
               "false_alarm_ratio_vs_clean", "prediction_change_rate"], ra_rows)

    # ---- C. extended diagnostics ----
    diag_rows = []
    for k in order:
        s = cond_stats[k]
        diag_rows.append({
            "condition": s["label"], "tp": s["tp"], "fn": s["fn"], "fp": s["fp"], "tn": s["tn"],
            "sensitivity_recall": fmt(s["sensitivity_recall"]), "specificity": fmt(s["specificity"]),
            "precision_ppv": fmt(s["precision_ppv"]), "npv": fmt(s["npv"]), "f1": fmt(s["f1"]),
            "false_omission_rate": fmt(s["false_omission_rate"]), "false_discovery_rate": fmt(s["false_discovery_rate"]),
            "balanced_accuracy": fmt(s["balanced_accuracy"]), "mcc": fmt(s["mcc"]), "cohen_kappa": fmt(s["cohen_kappa"]),
        })
    write_csv(out_res / "ch05_extended_diagnostic_metrics.csv",
              ["condition", "tp", "fn", "fp", "tn", "sensitivity_recall", "specificity", "precision_ppv",
               "npv", "f1", "false_omission_rate", "false_discovery_rate", "balanced_accuracy",
               "mcc", "cohen_kappa"], diag_rows)

    # ---- D. missed-fall destinations ----
    dest_rows = []
    for k in order:
        c = conditions[k]
        yt, yp = c["y_true"], c["y_pred"]
        fall_total = int(np.sum(yt == FALL))
        missed = int(np.sum((yt == FALL) & (yp != FALL)))
        parts = []
        for cls in range(NUM_CLASSES):
            if cls == FALL:
                continue
            n = int(np.sum((yt == FALL) & (yp == cls)))
            if n > 0:
                share = sd(n, missed) * 100
                parts.append((CLASS_NAMES[cls], n, share))
        parts.sort(key=lambda x: x[1], reverse=True)
        dest_str = "; ".join(f"{name}={n} ({share:.1f}\\%)" for name, n, share in parts) or "none"
        dest_rows.append({
            "condition": c["label"], "fall_windows": fall_total, "missed_fall_windows": missed,
            "missed_fall_rate": fmt(sd(missed, fall_total)),
            "dominant_missed_fall_destination_classes": dest_str,
        })
    write_csv(out_res / "ch05_missed_fall_destinations.csv",
              ["condition", "fall_windows", "missed_fall_windows", "missed_fall_rate",
               "dominant_missed_fall_destination_classes"], dest_rows)

    # ---- E. paired safety-state transitions (within-file: clean state vs attacked state) ----
    def state(t_bin, p_bin):
        if t_bin == 1 and p_bin == 1: return "TP"
        if t_bin == 1 and p_bin == 0: return "FN"
        if t_bin == 0 and p_bin == 1: return "FP"
        return "TN"

    atk = root / "results" / "converged_attacks"
    pair_files = [
        ("Clean -> FGSM", atk / "converged_seed42_fgsm_predictions_test_epsilon_0_03.csv"),
        ("Clean -> PGD", atk / "converged_seed42_pgd_predictions_test_epsilon_0_03.csv"),
        ("Defended clean -> Defended FGSM", atk / "defended_fgsm_at_seed42_fgsm_predictions_test_epsilon_0_03.csv"),
        ("Defended clean -> Defended PGD", atk / "defended_fgsm_at_seed42_pgd_predictions_test_epsilon_0_03.csv"),
    ]
    pair_rows = []
    for comp, path in pair_files:
        rows = read_rows(path)
        counts = {}
        src_totals = {}
        for r in rows:
            t = int(r["fall_true_binary"])
            s0 = state(t, int(r["clean_fall_pred_binary"]))
            s1 = state(t, int(r["attacked_fall_pred_binary"]))
            counts[(s0, s1)] = counts.get((s0, s1), 0) + 1
            src_totals[s0] = src_totals.get(s0, 0) + 1
        for (s0, s1), n in sorted(counts.items()):
            pair_rows.append({
                "comparison": comp, "transition": f"{s0} -> {s1}", "count": n,
                "source_total": src_totals[s0], "row_share_pct": f"{sd(n, src_totals[s0])*100:.1f}",
            })
    write_csv(out_res / "ch05_paired_safety_state_transitions.csv",
              ["comparison", "transition", "count", "source_total", "row_share_pct"], pair_rows)

    # ---- F. walking-class (verify against Chapter 4 artifact) ----
    walking_note = {}
    ch4_walk = root / "results" / "converged_ch04_artifacts" / "ch04_walking_class_vulnerability.csv"
    if ch4_walk.exists():
        wk = {r["metric"]: r["value"] for r in read_rows(ch4_walk)}
        walking_note = wk
        write_csv(out_res / "ch05_walking_class_vulnerability.csv", ["metric", "value"],
                  [{"metric": k, "value": v} for k, v in wk.items()])

    # ----------------------- FIGURES -----------------------
    # 5.1 failure threshold: fall recall vs epsilon (undef + defended)
    def sweep_xy(path):
        rows = sorted(read_rows(path), key=lambda r: float(r["epsilon"]))
        return [float(r["epsilon"]) for r in rows], [float(r["fall_recall"]) for r in rows], \
               [float(r["missed_fall_rate"]) for r in rows]
    ef, rf, mf = sweep_xy(atk / "converged_seed42_fgsm_epsilon_sweep_test.csv")
    ep, rp, mp = sweep_xy(atk / "converged_seed42_pgd_epsilon_sweep_test.csv")
    edf, rdf, mdf = sweep_xy(atk / "defended_fgsm_at_seed42_fgsm_epsilon_sweep_test.csv")
    edp, rdp, mdp = sweep_xy(atk / "defended_fgsm_at_seed42_pgd_epsilon_sweep_test.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5))
    a1.plot(ef, rf, "o-", label="FGSM undef"); a1.plot(ep, rp, "s-", label="PGD undef")
    a1.plot(edf, rdf, "o--", label="FGSM defended"); a1.plot(edp, rdp, "s--", label="PGD defended")
    a1.axhline(0.50, color="gray", ls=":", lw=1); a1.set_title("Fall recall vs epsilon")
    a1.set_xlabel(r"$\epsilon$"); a1.set_ylabel("fall recall"); a1.grid(alpha=0.3); a1.legend(fontsize=8)
    a2.plot(ef, mf, "o-", label="FGSM undef"); a2.plot(ep, mp, "s-", label="PGD undef")
    a2.plot(edf, mdf, "o--", label="FGSM defended"); a2.plot(edp, mdp, "s--", label="PGD defended")
    a2.set_title("Missed-fall rate vs epsilon"); a2.set_xlabel(r"$\epsilon$"); a2.set_ylabel("missed-fall rate")
    a2.grid(alpha=0.3); a2.legend(fontsize=8)
    fig.suptitle("Converged test-split failure thresholds (window-level safety proxy)")
    fig.tight_layout(rect=[0, 0, 1, 0.96]); fig.savefig(out_fig / "ch05_figure_5_1_failure_threshold_plot.png", dpi=300); plt.close(fig)

    # 5.3 safety error burden: stacked TP/FN/FP/TN per condition
    labels = [cond_stats[k]["label"].replace(r", $\epsilon=0.03$", "") for k in order]
    tp = [cond_stats[k]["tp"] for k in order]; fn = [cond_stats[k]["fn"] for k in order]
    fp = [cond_stats[k]["fp"] for k in order]; tn = [cond_stats[k]["tn"] for k in order]
    x = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x, tp, label="TP (detected fall)", color="#2ca02c")
    ax.bar(x, fn, bottom=tp, label="FN (missed fall)", color="#d62728")
    ax.bar(x, fp, bottom=np.array(tp)+np.array(fn), label="FP (false alarm)", color="#ff7f0e")
    ax.bar(x, tn, bottom=np.array(tp)+np.array(fn)+np.array(fp), label="TN (correct non-fall)", color="#1f77b4")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("window count (n=500)"); ax.set_title("Safety error burden composition (converged test split)")
    ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(out_fig / "ch05_figure_5_3_safety_error_burden_composition.png", dpi=300); plt.close(fig)

    # 5.5 missed-fall destination heatmap (fall -> non-fall class) for attacked conditions
    attacked_keys = ["fgsm", "pgd", "def_fgsm", "def_pgd"]
    nonfall = [c for c in range(NUM_CLASSES) if c != FALL]
    M = np.zeros((len(attacked_keys), len(nonfall)), dtype=int)
    for i, k in enumerate(attacked_keys):
        yt, yp = conditions[k]["y_true"], conditions[k]["y_pred"]
        for j, cls in enumerate(nonfall):
            M[i, j] = int(np.sum((yt == FALL) & (yp == cls)))
    fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(M, cmap="Reds")
    ax.set_xticks(range(len(nonfall))); ax.set_xticklabels([CLASS_NAMES[c] for c in nonfall], rotation=30, ha="right")
    ax.set_yticks(range(len(attacked_keys))); ax.set_yticklabels([cond_stats[k]["label"] for k in attacked_keys], fontsize=8)
    for i in range(len(attacked_keys)):
        for j in range(len(nonfall)):
            ax.text(j, i, M[i, j], ha="center", va="center", color="black", fontsize=9)
    ax.set_title("Missed-fall destination classes (true fall -> non-fall), converged test split")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04); fig.tight_layout()
    fig.savefig(out_fig / "ch05_figure_5_5_missed_fall_destination_heatmap.png", dpi=300); plt.close(fig)

    # 5.4 paired transition bar (Clean->FGSM, Clean->PGD key transitions)
    key_tr = ["TP -> FN", "TN -> FP", "FP -> TN", "TN -> TN"]
    comps = ["Clean -> FGSM", "Clean -> PGD"]
    data = {comp: {t: 0 for t in key_tr} for comp in comps}
    for r in pair_rows:
        if r["comparison"] in comps and r["transition"] in key_tr:
            data[r["comparison"]][r["transition"]] = r["count"]
    x = np.arange(len(key_tr)); w = 0.38
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - w/2, [data["Clean -> FGSM"][t] for t in key_tr], w, label="Clean -> FGSM", color="#1f77b4")
    ax.bar(x + w/2, [data["Clean -> PGD"][t] for t in key_tr], w, label="Clean -> PGD", color="#d62728")
    ax.set_xticks(x); ax.set_xticklabels(key_tr); ax.set_ylabel("window count")
    ax.set_title("Paired safety-state transitions (converged test split)"); ax.legend(); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(out_fig / "ch05_figure_5_4_paired_safety_state_transition.png", dpi=300); plt.close(fig)

    # ----------------------- metadata + markdown -----------------------
    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "split_used": "primary test split (n=500, fall=45, non-fall=455)",
        "legacy_note": "Legacy 996-window pool is not used here; primary Chapter 5 = 500-window test split.",
        "defense_note": ("Defended rows refreshed from Stage 3 converged FGSM adversarial training. "
                         "Defense is partial and attack-specific: FGSM AT partially recovers FGSM fall "
                         "recall; PGD remains weak at eps=0.03; defense mitigates but does not solve the "
                         "safety failure. No certified robustness."),
        "defended_clean_source": "clean_predicted_label column of Stage 3 defended attack CSVs",
        "paired_transition_matching": ("Within-file per-sample_id: each attack CSV stores the model's clean "
                                        "and attacked prediction for the identical window; clean vs attacked "
                                        "safety state compared per window. No cross-file matching."),
        "claim_boundaries": "window-level safety-proxy; digital/software-tensor; not clinical/medical-device/"
                            "physical-OTA/event-level/long-lie/fall-risk/certified-robustness.",
        "input_files": [
            "results/converged_baseline/converged_seed42_test_predictions.csv",
            "results/converged_attacks/converged_seed42_fgsm_predictions_test_epsilon_0_03.csv",
            "results/converged_attacks/converged_seed42_pgd_predictions_test_epsilon_0_03.csv",
            "results/converged_attacks/converged_seed42_fgsm_epsilon_sweep_test.csv",
            "results/converged_attacks/converged_seed42_pgd_epsilon_sweep_test.csv",
            "results/converged_defense/defended_fgsm_at_seed42_clean_metrics_test.csv",
            "results/converged_attacks/defended_fgsm_at_seed42_fgsm_predictions_test_epsilon_0_03.csv",
            "results/converged_attacks/defended_fgsm_at_seed42_pgd_predictions_test_epsilon_0_03.csv",
            "results/converged_attacks/defended_fgsm_at_seed42_fgsm_epsilon_sweep_test.csv",
            "results/converged_attacks/defended_fgsm_at_seed42_pgd_epsilon_sweep_test.csv",
            "results/converged_ch04_artifacts/ch04_walking_class_vulnerability.csv",
        ],
        "validation": "passed",
        "walking_class": walking_note,
    }
    with (out_res / "ch05_converged_artifacts_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("Chapter 5 converged artifacts generated.")
    print(f"Tables  -> {out_res}")
    print(f"Figures -> {out_fig}\n")
    print("=== Extended diagnostics (per condition) ===")
    for r in diag_rows:
        print(f"  {r['condition']}: TP/FN/FP/TN={r['tp']}/{r['fn']}/{r['fp']}/{r['tn']} "
              f"recall={r['sensitivity_recall']} spec={r['specificity']} F1={r['f1']} MCC={r['mcc']} kappa={r['cohen_kappa']}")
    print("\n=== Risk amplification ===")
    for r in ra_rows:
        print(f"  {r['condition']}: recall={r['fall_recall']} MFR={r['missed_fall_rate']} "
              f"FN={r['missed_fall_count']} FP={r['false_fall_alarm_count']} (+{r['false_alarm_increase_vs_clean']}) "
              f"predchg={r['prediction_change_rate']}")
    print("\n=== Thresholds ===")
    for r in thr_rows:
        print(f"  {r['attack']} {r['model']}: clean_recall={r['clean_fall_recall']} "
              f"drop>=0.10@{r['first_eps_drop_ge_0_10']} <0.50@{r['first_eps_recall_below_0_50']} =0@{r['first_eps_recall_zero']}")
    print("\n=== Missed-fall destinations ===")
    for r in dest_rows:
        print(f"  {r['condition']}: {r['dominant_missed_fall_destination_classes']}")
    print("\n=== Walking-class (from Ch4 artifact) ===")
    for k in ("total_walking_windows", "clean_walking_recall", "fgsm_walking_recall", "pgd_walking_recall",
              "fgsm_walk_to_fall_count", "pgd_walk_to_fall_count"):
        print(f"  {k}: {walking_note.get(k, 'MISSING')}")


if __name__ == "__main__":
    main()
