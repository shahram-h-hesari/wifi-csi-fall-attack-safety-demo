"""
Generate Chapter 6 (defense evaluation) converged-test-split artifacts.

Reads ONLY existing committed converged CSVs (no retraining, no re-attack) and
produces the Chapter 6 defense-evaluation tables and figures on the primary
500-window test split, using the Stage 3 FGSM adversarial-training defended
results. Defended-clean per-window predictions are taken from the
`clean_predicted_label` / `clean_fall_pred_binary` / `clean_prediction_confidence`
columns of the Stage 3 defended attack CSVs.

Interpretation (enforced by the data, not asserted): the defense gives a
partial, attack-specific recovery -- FGSM fall recall recovers from 0.0000 to
~0.3111, PGD remains weak at ~0.0889. It mitigates but does not solve the
safety-proxy failure. Window-level, digital/software-tensor scope only; not
clinical, medical-device, physical/over-the-air, event-level, fall-risk, or
certified-robustness claims.

Outputs (new namespaces only; Ch4/Ch5 folders untouched):
    results/converged_ch06_artifacts/
    figures/converged_ch06_artifacts/
"""

from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
import math
import statistics
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


CLASS_NAMES = {0: "lie down", 1: "fall", 2: "walk", 3: "pickup", 4: "run", 5: "sit down", 6: "stand up"}
NUM_CLASSES = 7
FALL = 1
HIGH_CONF_TAU = 0.5  # documented threshold for "high-confidence" missed-fall rate


def read_rows(path: Path) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sd(num, den):
    return num / den if den else 0.0


def fmt(x, nd=4):
    return f"{x:.{nd}f}" if isinstance(x, float) else x


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------------------
# Load six conditions with multiclass preds, binary preds, and confidence
# ---------------------------------------------------------------------------
def load_conditions(root: Path):
    base = root / "results" / "converged_baseline"
    atk = root / "results" / "converged_attacks"
    clean = read_rows(base / "converged_seed42_test_predictions.csv")
    fgsm = read_rows(atk / "converged_seed42_fgsm_predictions_test_epsilon_0_03.csv")
    pgd = read_rows(atk / "converged_seed42_pgd_predictions_test_epsilon_0_03.csv")
    dfgsm = read_rows(atk / "defended_fgsm_at_seed42_fgsm_predictions_test_epsilon_0_03.csv")
    dpgd = read_rows(atk / "defended_fgsm_at_seed42_pgd_predictions_test_epsilon_0_03.csv")

    def ic(rows, name):
        return np.array([int(r[name]) for r in rows])

    def fc(rows, name):
        return np.array([float(r[name]) for r in rows])

    def pcr(rows):
        return float(np.mean([int(r["prediction_changed"]) for r in rows]))

    C = {}
    C["clean"] = dict(label="Undefended clean", yt=ic(clean, "true_label"), yp=ic(clean, "predicted_label"),
                      conf=fc(clean, "prediction_confidence"), pred_change=None)
    C["fgsm"] = dict(label="Undefended FGSM", yt=ic(fgsm, "true_label"), yp=ic(fgsm, "attacked_predicted_label"),
                     conf=fc(fgsm, "attacked_prediction_confidence"), pred_change=pcr(fgsm))
    C["pgd"] = dict(label="Undefended PGD", yt=ic(pgd, "true_label"), yp=ic(pgd, "attacked_predicted_label"),
                    conf=fc(pgd, "attacked_prediction_confidence"), pred_change=pcr(pgd))
    C["def_clean"] = dict(label="Defended clean", yt=ic(dfgsm, "true_label"), yp=ic(dfgsm, "clean_predicted_label"),
                          conf=fc(dfgsm, "clean_prediction_confidence"), pred_change=None)
    C["def_fgsm"] = dict(label="Defended FGSM", yt=ic(dfgsm, "true_label"), yp=ic(dfgsm, "attacked_predicted_label"),
                         conf=fc(dfgsm, "attacked_prediction_confidence"), pred_change=pcr(dfgsm))
    C["def_pgd"] = dict(label="Defended PGD", yt=ic(dpgd, "true_label"), yp=ic(dpgd, "attacked_predicted_label"),
                        conf=fc(dpgd, "attacked_prediction_confidence"), pred_change=pcr(dpgd))
    return C


def confusion(yt, yp):
    t = (yt == FALL).astype(int)
    p = (yp == FALL).astype(int)
    tp = int(np.sum((t == 1) & (p == 1)))
    fn = int(np.sum((t == 1) & (p == 0)))
    fp = int(np.sum((t == 0) & (p == 1)))
    tn = int(np.sum((t == 0) & (p == 0)))
    return tp, fn, fp, tn


def balanced_acc(tp, fn, fp, tn):
    return (sd(tp, tp + fn) + sd(tn, tn + fp)) / 2


def conf_metrics(yt, yp, conf):
    """High-confidence missed-fall rate (tau=0.5) and median missed-fall confidence."""
    miss_mask = (yt == FALL) & (yp != FALL)
    fall_total = int(np.sum(yt == FALL))
    high_conf_missed = int(np.sum(miss_mask & (conf >= HIGH_CONF_TAU)))
    hc_mfr = sd(high_conf_missed, fall_total)
    miss_conf = conf[miss_mask]
    median_conf = float(np.median(miss_conf)) if miss_conf.size else float("nan")
    return hc_mfr, median_conf


def sweep_thresholds(path: Path):
    rows = sorted(read_rows(path), key=lambda r: float(r["epsilon"]))
    clean_recall = float(rows[0]["fall_recall"])
    def first(pred):
        for r in rows:
            if pred(r):
                return float(r["epsilon"])
        return None
    return dict(
        drop10=first(lambda r: (clean_recall - float(r["fall_recall"])) >= 0.10),
        below50=first(lambda r: float(r["fall_recall"]) < 0.50),
        zero=first(lambda r: float(r["fall_recall"]) == 0.0),
    )


def main():
    argparse.ArgumentParser(description="Generate Chapter 6 converged artifacts.").parse_args()
    root = Path(__file__).resolve().parents[1]
    atk = root / "results" / "converged_attacks"
    out_res = root / "results" / "converged_ch06_artifacts"
    out_fig = root / "figures" / "converged_ch06_artifacts"
    out_res.mkdir(parents=True, exist_ok=True)
    out_fig.mkdir(parents=True, exist_ok=True)

    C = load_conditions(root)
    order = ["clean", "fgsm", "pgd", "def_clean", "def_fgsm", "def_pgd"]
    stat = {}
    for k in order:
        tp, fn, fp, tn = confusion(C[k]["yt"], C[k]["yp"])
        hc, mc = conf_metrics(C[k]["yt"], C[k]["yp"], C[k]["conf"])
        stat[k] = dict(label=C[k]["label"], tp=tp, fn=fn, fp=fp, tn=tn,
                       recall=sd(tp, tp + fn), mfr=sd(fn, tp + fn), fpr=sd(fp, fp + tn),
                       bal=balanced_acc(tp, fn, fp, tn), f1=sd(2 * tp, 2 * tp + fp + fn),
                       hc_mfr=hc, median_conf=mc, pred_change=C[k]["pred_change"])

    # ---------------- VALIDATION ----------------
    errs = []
    def chk(name, got, exp, tol=1e-3):
        ok = (got == exp) if isinstance(exp, tuple) else (abs(got - exp) <= tol)
        if not ok:
            errs.append(f"{name}: got {got}, expected {exp}")
    for k, exp in [("clean", (43, 2, 0, 455)), ("fgsm", (0, 45, 47, 408)), ("pgd", (0, 45, 48, 407)),
                   ("def_clean", (41, 4, 8, 447)), ("def_fgsm", (14, 31, 27, 428)), ("def_pgd", (4, 41, 54, 401))]:
        s = stat[k]
        chk(f"{k} TP/FN/FP/TN", (s["tp"], s["fn"], s["fp"], s["tn"]), exp)
    chk("def_fgsm recall", stat["def_fgsm"]["recall"], 0.3111)
    chk("def_pgd recall", stat["def_pgd"]["recall"], 0.0889)
    chk("def_fgsm mfr", stat["def_fgsm"]["mfr"], 0.6889)
    chk("def_pgd mfr", stat["def_pgd"]["mfr"], 0.9111)
    thr_def_fgsm = sweep_thresholds(atk / "defended_fgsm_at_seed42_fgsm_epsilon_sweep_test.csv")
    thr_def_pgd = sweep_thresholds(atk / "defended_fgsm_at_seed42_pgd_epsilon_sweep_test.csv")
    thr_undef_fgsm = sweep_thresholds(atk / "converged_seed42_fgsm_epsilon_sweep_test.csv")
    thr_undef_pgd = sweep_thresholds(atk / "converged_seed42_pgd_epsilon_sweep_test.csv")
    chk("FGSM defended zero-recall eps", thr_def_fgsm["zero"], 0.075)
    chk("PGD defended zero-recall eps", thr_def_pgd["zero"], 0.035)
    if errs:
        print("VALIDATION FAILED:")
        for e in errs:
            print("  - " + e)
        raise SystemExit(1)
    print("VALIDATION PASSED: converged Chapter 6 values match source-of-truth.\n")

    cl = stat["clean"]

    # ---------------- A. Defense tradeoff (clean) ----------------
    a_rows = [{
        "metric": m, "undefended_clean": u, "defended_clean": d, "change_def_minus_undef": ch,
    } for m, u, d, ch in [
        ("fall_recall", fmt(cl["recall"]), fmt(stat["def_clean"]["recall"]), fmt(stat["def_clean"]["recall"] - cl["recall"])),
        ("missed_fall_rate", fmt(cl["mfr"]), fmt(stat["def_clean"]["mfr"]), fmt(stat["def_clean"]["mfr"] - cl["mfr"])),
        ("false_fall_alarms", cl["fp"], stat["def_clean"]["fp"], stat["def_clean"]["fp"] - cl["fp"]),
        ("fall_f1", fmt(cl["f1"]), fmt(stat["def_clean"]["f1"]), fmt(stat["def_clean"]["f1"] - cl["f1"])),
        ("balanced_accuracy", fmt(cl["bal"]), fmt(stat["def_clean"]["bal"]), fmt(stat["def_clean"]["bal"] - cl["bal"])),
        ("tp_fn_fp_tn", f"{cl['tp']}/{cl['fn']}/{cl['fp']}/{cl['tn']}",
         f"{stat['def_clean']['tp']}/{stat['def_clean']['fn']}/{stat['def_clean']['fp']}/{stat['def_clean']['tn']}", ""),
    ]]
    write_csv(out_res / "ch06_defense_tradeoff.csv",
              ["metric", "undefended_clean", "defended_clean", "change_def_minus_undef"], a_rows)

    # ---------------- B. Matched defense summary ----------------
    b_rows = []
    for atkk, undef, deff in [("FGSM", "fgsm", "def_fgsm"), ("PGD", "pgd", "def_pgd")]:
        u, d = stat[undef], stat[deff]
        b_rows.append({
            "attack": atkk,
            "undef_recall": fmt(u["recall"]), "def_recall": fmt(d["recall"]),
            "undef_mfr": fmt(u["mfr"]), "def_mfr": fmt(d["mfr"]),
            "undef_FN": u["fn"], "def_FN": d["fn"],
            "undef_FP": u["fp"], "def_FP": d["fp"],
            "undef_tp_fn_fp_tn": f"{u['tp']}/{u['fn']}/{u['fp']}/{u['tn']}",
            "def_tp_fn_fp_tn": f"{d['tp']}/{d['fn']}/{d['fp']}/{d['tn']}",
            "undef_pred_change": fmt(u["pred_change"]), "def_pred_change": fmt(d["pred_change"]),
            "undef_high_conf_mfr": fmt(u["hc_mfr"]), "def_high_conf_mfr": fmt(d["hc_mfr"]),
            "undef_median_missed_conf": fmt(u["median_conf"]), "def_median_missed_conf": fmt(d["median_conf"]),
        })
    write_csv(out_res / "ch06_matched_defense_summary.csv", list(b_rows[0].keys()), b_rows)

    # ---------------- C. Fall-window recovery ----------------
    c_rows = []
    for atkk, undef, deff in [("FGSM", "fgsm", "def_fgsm"), ("PGD", "pgd", "def_pgd")]:
        u, d = stat[undef], stat[deff]
        c_rows.append({
            "attack": atkk, "total_fall_windows": u["tp"] + u["fn"],
            "undef_detected_tp": u["tp"], "def_detected_tp": d["tp"],
            "recovered_fall_windows": d["tp"] - u["tp"], "residual_missed_fn": d["fn"],
            "def_fall_recall": fmt(d["recall"]), "def_missed_fall_rate": fmt(d["mfr"]),
        })
    write_csv(out_res / "ch06_fall_window_recovery.csv", list(c_rows[0].keys()), c_rows)

    # ---------------- D. Class-normalized false-alarm effect ----------------
    def class_fp(cond_key):
        yt, yp = C[cond_key]["yt"], C[cond_key]["yp"]
        out = {}
        for c in range(NUM_CLASSES):
            if c == FALL:
                continue
            cw = int(np.sum(yt == c))
            fp = int(np.sum((yt == c) & (yp == FALL)))
            out[c] = (cw, fp)
        return out
    d_rows = []
    for atkk, undef, deff in [("FGSM", "fgsm", "def_fgsm"), ("PGD", "pgd", "def_pgd")]:
        cu, cd = class_fp(undef), class_fp(deff)
        for c in range(NUM_CLASSES):
            if c == FALL:
                continue
            cw, ufp = cu[c]
            _, dfp = cd[c]
            ur, dr = sd(ufp, cw), sd(dfp, cw)
            d_rows.append({
                "comparison": f"{atkk} -> Def. {atkk}", "true_nonfall_class": CLASS_NAMES[c],
                "class_windows": cw, "attack_FP": ufp, "def_FP": dfp,
                "attack_rate": fmt(ur), "def_rate": fmt(dr),
                "change_pp": fmt((dr - ur) * 100, 2),
            })
    write_csv(out_res / "ch06_class_normalized_defense_effect.csv", list(d_rows[0].keys()), d_rows)

    # walking-label reliability (defended clean/attacked), comparison only
    def walk_recall(cond_key):
        yt, yp = C[cond_key]["yt"], C[cond_key]["yp"]
        tot = int(np.sum(yt == 2))
        cor = int(np.sum((yt == 2) & (yp == 2)))
        return tot, cor, sd(cor, tot)
    walk = {k: walk_recall(k) for k in ["clean", "fgsm", "pgd", "def_clean", "def_fgsm", "def_pgd"]}
    write_csv(out_res / "ch06_walking_reliability.csv", ["condition", "walk_windows", "walk_correct", "walk_recall"],
              [{"condition": stat[k]["label"], "walk_windows": walk[k][0], "walk_correct": walk[k][1],
                "walk_recall": fmt(walk[k][2])} for k in ["clean", "fgsm", "pgd", "def_clean", "def_fgsm", "def_pgd"]])

    # ---------------- E. Recovery / residual-gap ----------------
    e_rows = []
    for atkk, undef, deff, tu, td in [("FGSM", "fgsm", "def_fgsm", thr_undef_fgsm, thr_def_fgsm),
                                      ("PGD", "pgd", "def_pgd", thr_undef_pgd, thr_def_pgd)]:
        u, d = stat[undef], stat[deff]
        recall_recovery = sd(d["recall"] - u["recall"], cl["recall"] - u["recall"])
        e_rows.append({
            "attack": atkk,
            "undef_attacked_recall": fmt(u["recall"]), "def_attacked_recall": fmt(d["recall"]),
            "clean_recall": fmt(cl["recall"]),
            "fall_recall_recovery_fraction": fmt(recall_recovery),
            "remaining_gap_to_clean": fmt(cl["recall"] - d["recall"]),
            "mfr_reduction": fmt(u["mfr"] - d["mfr"]),
            "false_alarm_change_def_minus_undef": d["fp"] - u["fp"],
            "undef_zero_recall_eps": tu["zero"], "def_zero_recall_eps": td["zero"],
            "undef_below50_eps": tu["below50"], "def_below50_eps": td["below50"],
        })
    write_csv(out_res / "ch06_recovery_residual_gap.csv", list(e_rows[0].keys()), e_rows)

    # ---------------- F. Safety-score decomposition ----------------
    # score = w * FNR + 1 * FPR ; weights 1:1, 5:1, 10:1 (illustrative window-level proxy weights)
    f_rows = []
    for w in (1, 5, 10):
        for k in order:
            s = stat[k]
            mf_comp = w * s["mfr"]
            fa_comp = s["fpr"]
            f_rows.append({
                "weighting": f"{w}:1", "condition": s["label"],
                "FNR": fmt(s["mfr"]), "FPR": fmt(s["fpr"]),
                "missed_fall_component": fmt(mf_comp), "false_alert_component": fmt(fa_comp),
                "total_score": fmt(mf_comp + fa_comp),
            })
    write_csv(out_res / "ch06_safety_score_decomposition.csv", list(f_rows[0].keys()), f_rows)

    # ---------------------- FIGURES ----------------------
    grp = ["clean", "fgsm", "pgd"]
    x = np.arange(3); wbar = 0.38
    # 6.1 defense overview: fall recall undef vs def across clean/FGSM/PGD
    undef_r = [stat[k]["recall"] for k in grp]
    def_r = [stat["def_clean"]["recall"], stat["def_fgsm"]["recall"], stat["def_pgd"]["recall"]]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - wbar/2, undef_r, wbar, label="Undefended", color="#d62728")
    ax.bar(x + wbar/2, def_r, wbar, label="Defended (FGSM-AT)", color="#2ca02c")
    ax.set_xticks(x); ax.set_xticklabels(["Clean", "FGSM 0.03", "PGD 0.03"]); ax.set_ylabel("fall recall")
    ax.set_title("Defense overview: fall recall (converged test split)"); ax.legend(); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(out_fig / "ch06_figure_6_1_defense_effect_summary.png", dpi=300); plt.close(fig)

    # 6.2 clean cost
    fig, ax = plt.subplots(figsize=(8, 5))
    mets = ["fall recall", "missed-fall rate", "false alarms (/100)"]
    uvals = [cl["recall"], cl["mfr"], cl["fp"]/100]
    dvals = [stat["def_clean"]["recall"], stat["def_clean"]["mfr"], stat["def_clean"]["fp"]/100]
    xx = np.arange(3)
    ax.bar(xx - wbar/2, uvals, wbar, label="Undefended clean", color="#1f77b4")
    ax.bar(xx + wbar/2, dvals, wbar, label="Defended clean", color="#ff7f0e")
    ax.set_xticks(xx); ax.set_xticklabels(mets); ax.set_title("Clean-performance cost of defense")
    ax.legend(); ax.grid(axis="y", alpha=0.3); fig.tight_layout()
    fig.savefig(out_fig / "ch06_figure_6_2_clean_defense_tradeoff.png", dpi=300); plt.close(fig)

    # 6.3 robustness recovery under attack (fall recall undef vs def, FGSM/PGD)
    fig, ax = plt.subplots(figsize=(8, 5))
    xx = np.arange(2)
    ax.bar(xx - wbar/2, [stat["fgsm"]["recall"], stat["pgd"]["recall"]], wbar, label="Undefended", color="#d62728")
    ax.bar(xx + wbar/2, [stat["def_fgsm"]["recall"], stat["def_pgd"]["recall"]], wbar, label="Defended", color="#2ca02c")
    ax.set_xticks(xx); ax.set_xticklabels(["FGSM 0.03", "PGD 0.03"]); ax.set_ylabel("fall recall")
    ax.set_title("Robustness recovery under attack"); ax.legend(); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(out_fig / "ch06_figure_6_3_matched_attack_defense_effect_comparison.png", dpi=300); plt.close(fig)

    # 6.4 class-normalized defense-effect heatmap (change pp) FGSM & PGD
    nonfall = [c for c in range(NUM_CLASSES) if c != FALL]
    M = np.zeros((2, len(nonfall)))
    for i, (undef, deff) in enumerate([("fgsm", "def_fgsm"), ("pgd", "def_pgd")]):
        cu, cd = class_fp(undef), class_fp(deff)
        for j, c in enumerate(nonfall):
            cw, ufp = cu[c]; _, dfp = cd[c]
            M[i, j] = (sd(dfp, cw) - sd(ufp, cw)) * 100
    fig, ax = plt.subplots(figsize=(10, 3.6))
    vmax = np.abs(M).max() or 1
    im = ax.imshow(M, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(len(nonfall))); ax.set_xticklabels([CLASS_NAMES[c] for c in nonfall], rotation=30, ha="right")
    ax.set_yticks([0, 1]); ax.set_yticklabels(["FGSM->Def", "PGD->Def"])
    for i in range(2):
        for j in range(len(nonfall)):
            ax.text(j, i, f"{M[i,j]:+.1f}", ha="center", va="center", fontsize=8)
    ax.set_title("Class-normalized false-fall-alarm change (pp; negative = improvement)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04); fig.tight_layout()
    fig.savefig(out_fig / "ch06_figure_6_4_class_normalized_defense_effect_heatmap.png", dpi=300); plt.close(fig)

    # 6.5 fall-window recovery
    fig, ax = plt.subplots(figsize=(8, 5))
    cats = ["FGSM", "PGD"]; xx = np.arange(2)
    rec = [stat["def_fgsm"]["tp"], stat["def_pgd"]["tp"]]
    res = [stat["def_fgsm"]["fn"], stat["def_pgd"]["fn"]]
    ax.bar(xx, rec, label="Recovered (detected) fall windows", color="#2ca02c")
    ax.bar(xx, res, bottom=rec, label="Residual missed fall windows", color="#d62728")
    ax.set_xticks(xx); ax.set_xticklabels(cats); ax.set_ylabel("fall windows (of 45)")
    ax.set_title("Fall-window recovery after defense")
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(out_fig / "ch06_figure_6_5_fall_window_recovery_persistence.png", dpi=300, bbox_inches="tight"); plt.close(fig)

    # 6.6 threshold shift (zero-recall epsilon undef vs def)
    fig, ax = plt.subplots(figsize=(8, 5))
    xx = np.arange(2)
    ax.bar(xx - wbar/2, [thr_undef_fgsm["zero"], thr_undef_pgd["zero"]], wbar, label="Undefended", color="#d62728")
    ax.bar(xx + wbar/2, [thr_def_fgsm["zero"], thr_def_pgd["zero"]], wbar, label="Defended", color="#2ca02c")
    ax.set_xticks(xx); ax.set_xticklabels(["FGSM", "PGD"]); ax.set_ylabel(r"$\epsilon$ at zero fall recall")
    ax.set_title("Collapse-threshold shift under defense (higher = more robust)"); ax.legend(); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(out_fig / "ch06_figure_6_6_defense_recovery_residual_gap.png", dpi=300); plt.close(fig)

    # 6.7 safety-score decomposition at 10:1
    fig, ax = plt.subplots(figsize=(11, 5))
    labels = [stat[k]["label"] for k in order]
    mf = [10 * stat[k]["mfr"] for k in order]
    fa = [stat[k]["fpr"] for k in order]
    xx = np.arange(len(order))
    ax.bar(xx, mf, label="missed-fall component (10*FNR)", color="#d62728")
    ax.bar(xx, fa, bottom=mf, label="false-alert component (FPR)", color="#ff7f0e")
    ax.set_xticks(xx); ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("safety-priority score (10:1)"); ax.set_title("Safety-score component decomposition (10:1)")
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True)
    ax.grid(axis="y", alpha=0.3); fig.tight_layout()
    fig.savefig(out_fig / "ch06_figure_6_7_safety_score_component_decomposition.png", dpi=300, bbox_inches="tight"); plt.close(fig)

    # ---------------------- metadata ----------------------
    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "split_used": "primary test split (n=500, fall=45, non-fall=455)",
        "defense": "Stage 3 FGSM adversarial training (converged); partial, attack-specific recovery; "
                   "mitigates but does not solve; no certified robustness.",
        "defended_clean_source": "clean_predicted_label/clean_fall_pred_binary/clean_prediction_confidence of defended attack CSVs",
        "high_conf_missed_fall_definition": f"share of fall windows missed with prediction confidence >= {HIGH_CONF_TAU}",
        "median_missed_fall_confidence_definition": "median prediction confidence over missed (FN) fall windows",
        "safety_score_formula": "score = w * FNR + 1 * FPR (illustrative window-level proxy weights; not clinical utilities)",
        "recall_recovery_formula": "(def_attacked_recall - undef_attacked_recall) / (clean_recall - undef_attacked_recall)",
        "claim_boundaries": "window-level safety-proxy; digital/software-tensor; not clinical/medical-device/"
                            "physical-OTA/event-level/long-lie/fall-risk/certified-robustness.",
        "validation": "passed",
        "thresholds": {"undef_fgsm": thr_undef_fgsm, "undef_pgd": thr_undef_pgd,
                       "def_fgsm": thr_def_fgsm, "def_pgd": thr_def_pgd},
        "confidence_columns_available": True,
        "class_normalized_available": True,
        "outputs_tables": sorted(p.name for p in out_res.glob("*.csv")),
        "outputs_figures": sorted(p.name for p in out_fig.glob("*.png")),
    }
    with (out_res / "ch06_converged_artifacts_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # ---------------------- console summary ----------------------
    print("Chapter 6 converged artifacts generated.")
    print(f"Tables  -> {out_res}\nFigures -> {out_fig}\n")
    print("=== Defense tradeoff (clean) ===")
    print(f"  fall recall {cl['recall']:.4f} -> {stat['def_clean']['recall']:.4f}; "
          f"MFR {cl['mfr']:.4f} -> {stat['def_clean']['mfr']:.4f}; FP {cl['fp']} -> {stat['def_clean']['fp']}")
    print("=== Matched defense (recall, MFR, FP, pred-change, high-conf MFR, median missed conf) ===")
    for r in b_rows:
        print(f"  {r['attack']}: recall {r['undef_recall']}->{r['def_recall']} | MFR {r['undef_mfr']}->{r['def_mfr']} | "
              f"FP {r['undef_FP']}->{r['def_FP']} | predchg {r['undef_pred_change']}->{r['def_pred_change']} | "
              f"hcMFR {r['undef_high_conf_mfr']}->{r['def_high_conf_mfr']} | medConf {r['undef_median_missed_conf']}->{r['def_median_missed_conf']}")
    print("=== Fall-window recovery ===")
    for r in c_rows:
        print(f"  {r['attack']}: recovered {r['recovered_fall_windows']}/45, residual missed {r['residual_missed_fn']}, "
              f"def recall {r['def_fall_recall']}")
    print("=== Recovery / residual gap ===")
    for r in e_rows:
        print(f"  {r['attack']}: recall recovery {r['fall_recall_recovery_fraction']}, "
              f"FA change {r['false_alarm_change_def_minus_undef']:+d}, "
              f"zero-recall eps {r['undef_zero_recall_eps']} -> {r['def_zero_recall_eps']}")
    print("=== Class-normalized: classes where defense WORSENS false alarms (change > 0) ===")
    for r in d_rows:
        if float(r["change_pp"]) > 0:
            print(f"  {r['comparison']} {r['true_nonfall_class']}: {r['change_pp']} pp (attack {r['attack_FP']} -> def {r['def_FP']})")
    print("=== Walking reliability ===")
    for k in ["clean", "def_clean", "fgsm", "def_fgsm", "pgd", "def_pgd"]:
        print(f"  {stat[k]['label']}: walk recall {walk[k][2]:.4f} ({walk[k][1]}/{walk[k][0]})")


if __name__ == "__main__":
    main()
